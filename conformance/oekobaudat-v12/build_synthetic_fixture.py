#!/usr/bin/env python3
"""Build a deterministic synthetic ILCD+EPD v1.2 package for ÖKOBAUDAT profile testing.

The builder derives only from pinned public InData examples/master data plus the
exact locally resolved ÖKOBAUDAT profile JAR. It does not claim that the
synthetic fixture is a real EPD, affiliated with a referenced programme
operator, authorised by BBSR, or scientifically representative of a product.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
CONTACT_NS = "http://lca.jrc.it/ILCD/Contact"
EPD_2013_NS = "http://www.iai.kit.edu/EPD/2013"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

START_PROCESS_UUID = "57a4ae65-d305-421e-b21f-a3f0c35b8abe"
SYNTHETIC_PROCESS_UUID = "6b47f4cf-0bc4-4e0d-b9fd-9d5f845d1de0"
SYNTHETIC_REGISTRATION_NUMBER = "RX-PROOFGRID-V08-SYNTH-001"

# This is one of the exact programme-operator UUIDs accepted by ÖKOBAUDAT
# profile 3.8.0. It is used only as a synthetic profile-conformance identifier.
# It does not state affiliation, approval, registration, or source-use authority.
PROFILE_ALLOWED_OPERATOR_UUID = "d111dbec-b024-4be5-86c5-752d6eb2cf95"
PROFILE_ALLOWED_OPERATOR_NAME = "Institut Bauen und Umwelt e.V."

PROFILE_CATEGORIES_RESOURCE = "edu/kit/iai/lca/epd/categories/OEKOBAU.DAT_Categories.xml"


class FixtureError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureError(message)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def dataset_identity(path: Path) -> tuple[str | None, str | None]:
    root = ET.parse(path).getroot()
    uuid = None
    for node in root.iter():
        if local_name(node.tag) == "UUID" and node.text and node.text.strip():
            uuid = node.text.strip()
            break
    return uuid, local_name(root.tag)


def type_dir(root_name: str | None) -> str:
    return {
        "processDataSet": "processes",
        "flowDataSet": "flows",
        "flowPropertyDataSet": "flowproperties",
        "unitGroupDataSet": "unitgroups",
        "contactDataSet": "contacts",
        "sourceDataSet": "sources",
        "LCIAMethodDataSet": "lciamethods",
        "lifeCycleModelDataSet": "lifecyclemodels",
    }.get(root_name or "", "misc")


def build_index(sample_root: Path, master_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for source_root, priority in ((master_root, 0), (sample_root, 1)):
        for path in source_root.rglob("*.xml"):
            try:
                uuid, kind = dataset_identity(path)
            except ET.ParseError:
                continue
            if not uuid:
                continue
            row = {"path": path, "kind": kind, "source_root": source_root, "priority": priority}
            if uuid not in index or priority > int(index[uuid]["priority"]):
                index[uuid] = row
    return index


def copy_reference_closure(sample_root: Path, master_root: Path, package_root: Path) -> dict[str, Any]:
    index = build_index(sample_root, master_root)
    require(START_PROCESS_UUID in index, "pinned Wood panel process is not present in source index")

    queue = [START_PROCESS_UUID]
    seen: set[str] = set()
    missing: set[str] = set()
    copied: list[dict[str, Any]] = []
    copied_source_by_dest: dict[Path, Path] = {}

    while queue:
        uuid = queue.pop(0)
        if uuid in seen:
            continue
        seen.add(uuid)
        row = index.get(uuid)
        if row is None:
            missing.add(uuid)
            continue

        src: Path = row["path"]
        dest = package_root / type_dir(row["kind"]) / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied_source_by_dest[dest.resolve()] = src.resolve()
        copied.append(
            {
                "uuid": uuid,
                "kind": row["kind"],
                "source": str(src),
                "dest": str(dest.relative_to(package_root.parent)),
                "sha256": sha256_file(src),
            }
        )

        tree = ET.parse(src)
        root = tree.getroot()
        for node in root.iter():
            ref = node.attrib.get("refObjectId")
            if ref and ref not in seen:
                if ref in index:
                    queue.append(ref)
                else:
                    missing.add(ref)

            for attr in ("locations", "classes"):
                value = node.attrib.get(attr)
                if not value:
                    continue
                candidate = (src.parent / value).resolve()
                if candidate.is_file():
                    try:
                        rel = candidate.relative_to(sample_root.resolve())
                    except ValueError:
                        continue
                    target = package_root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(candidate, target)

    # Resolve non-UUID digital-file links from the original public sample tree.
    # In ILCD sourceDataSet documents the path is carried by the `uri` attribute.
    copied_digital: list[dict[str, str]] = []
    for dest_resolved, src_resolved in list(copied_source_by_dest.items()):
        tree = ET.parse(dest_resolved)
        for node in tree.getroot().iter():
            if local_name(node.tag) != "referenceToDigitalFile":
                continue
            rel_text = (node.attrib.get("uri") or (node.text or "")).strip()
            if not rel_text:
                continue

            original = (src_resolved.parent / rel_text).resolve()
            target = (dest_resolved.parent / rel_text).resolve()
            try:
                target.relative_to(package_root.resolve())
            except ValueError as exc:
                raise FixtureError(f"digital-file path escapes package: {rel_text}") from exc

            if original.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
                copied_digital.append(
                    {
                        "reference": rel_text,
                        "source": str(original),
                        "dest": str(target.relative_to(package_root.parent)),
                        "sha256": sha256_file(original),
                    }
                )

    return {
        "copied": copied,
        "copied_digital_files": copied_digital,
        "unresolved_refObjectIds": sorted(missing),
    }


def extract_profile_categories(profile_jar: Path, evidence_root: Path) -> tuple[Path, list[dict[str, str]]]:
    with zipfile.ZipFile(profile_jar) as zf:
        require(PROFILE_CATEGORIES_RESOURCE in zf.namelist(), "ÖKOBAUDAT category resource missing from exact profile JAR")
        data = zf.read(PROFILE_CATEGORIES_RESOURCE)

    category_path = evidence_root / "oekobaudat-profile-categories.xml"
    category_path.parent.mkdir(parents=True, exist_ok=True)
    category_path.write_bytes(data)

    root = ET.fromstring(data)
    candidates: list[tuple[int, str, list[dict[str, str]]]] = []

    def walk(node: ET.Element, path: list[dict[str, str]]) -> None:
        for child in node:
            if local_name(child.tag) != "category":
                continue
            entry = {"id": child.attrib.get("id", ""), "name": child.attrib.get("name", "")}
            next_path = path + [entry]
            child_categories = [x for x in child if local_name(x.tag) == "category"]
            if child_categories:
                walk(child, next_path)
            else:
                text = " ".join(x["name"].lower() for x in next_path)
                score = sum(10 for term in ("holz", "wood", "panel", "platte") if term in text)
                candidates.append((score, "/".join(x["id"] for x in next_path), next_path))

    for section in root.iter():
        if local_name(section.tag) == "categories" and section.attrib.get("dataType") == "Process":
            walk(section, [])

    require(candidates, "no process-category leaf found in ÖKOBAUDAT category resource")
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return category_path, candidates[0][2]


def register_namespaces() -> None:
    ET.register_namespace("", PROCESS_NS)
    ET.register_namespace("common", COMMON_NS)
    ET.register_namespace("c", CONTACT_NS)
    ET.register_namespace("epd", EPD_2013_NS)
    ET.register_namespace("epd2", EPD_2019_NS)
    ET.register_namespace("xsi", XSI_NS)


def mutate_process(process_path: Path, category_path: list[dict[str, str]]) -> dict[str, Any]:
    register_namespaces()
    tree = ET.parse(process_path)
    root = tree.getroot()
    require(root.attrib.get(f"{{{EPD_2019_NS}}}epd-version") == "1.2", "base process is not ILCD+EPD v1.2")

    info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    require(info is not None, "process dataSetInformation missing")
    uuid_node = info.find(f"{{{COMMON_NS}}}UUID")
    require(uuid_node is not None, "process UUID missing")
    uuid_node.text = SYNTHETIC_PROCESS_UUID

    name = info.find(f"{{{PROCESS_NS}}}name")
    require(name is not None, "process name missing")
    for base in name.findall(f"{{{PROCESS_NS}}}baseName"):
        lang = base.attrib.get(f"{{{XML_NS}}}lang")
        base.text = (
            "ProofGrid Synthetic Wood Panel — ÖKOBAUDAT 3.8.0 Conformance Fixture"
            if lang != "de"
            else "ProofGrid Synthetisches Holzpanel — ÖKOBAUDAT 3.8.0 Konformitätstest"
        )

    general = info.find(f"{{{COMMON_NS}}}generalComment")
    if general is not None:
        general.text = (
            "Synthetic non-production interoperability fixture derived from the public InData ILCD+EPD v1.2 example. "
            "Any programme-operator identifier is used only to exercise the published validation profile; no affiliation, approval, registration, or source-use authority is claimed."
        )

    class_info = info.find(f"{{{PROCESS_NS}}}classificationInformation")
    require(class_info is not None, "classificationInformation missing")
    for child in list(class_info):
        if local_name(child.tag) == "classification":
            class_info.remove(child)

    # Public InData v1.2 examples use the classification name `oekobau.dat`.
    # The selected path is drawn from the exact 3.8.0 profile category resource.
    classification = ET.SubElement(class_info, f"{{{COMMON_NS}}}classification", {"name": "oekobau.dat"})
    for level, entry in enumerate(category_path):
        cls = ET.SubElement(
            classification,
            f"{{{COMMON_NS}}}class",
            {"level": str(level), "classId": entry["id"]},
        )
        cls.text = entry["name"]

    removed_preceding = 0
    for parent in root.iter():
        for child in list(parent):
            if local_name(child.tag) == "referenceToPrecedingDataSetVersion":
                parent.remove(child)
                removed_preceding += 1

    changed_operator_refs = 0
    for node in root.iter():
        if local_name(node.tag) in {"referenceToRegistrationAuthority", "referenceToPublisher"}:
            node.attrib["refObjectId"] = PROFILE_ALLOWED_OPERATOR_UUID
            node.attrib["version"] = "00.00.002"
            for child in node:
                if local_name(child.tag) == "shortDescription":
                    child.text = PROFILE_ALLOWED_OPERATOR_NAME
            changed_operator_refs += 1

    registration = next((x for x in root.iter() if local_name(x.tag) == "registrationNumber"), None)
    if registration is not None:
        registration.text = SYNTHETIC_REGISTRATION_NUMBER

    version = next((x for x in root.iter() if local_name(x.tag) == "dataSetVersion"), None)
    if version is not None:
        version.text = "00.00.001"

    tree.write(process_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return {
        "synthetic_process_uuid": SYNTHETIC_PROCESS_UUID,
        "removed_preceding_dataset_references": removed_preceding,
        "changed_program_operator_references": changed_operator_refs,
        "selected_oekobaudat_category_path": category_path,
        "classification_name": "oekobau.dat",
    }


def create_synthetic_operator_contact(source_contact: Path, target_contact: Path) -> dict[str, Any]:
    register_namespaces()
    tree = ET.parse(source_contact)
    root = tree.getroot()
    uuid_node = next((x for x in root.iter() if local_name(x.tag) == "UUID"), None)
    require(uuid_node is not None, "operator contact UUID missing")
    uuid_node.text = PROFILE_ALLOWED_OPERATOR_UUID

    for node in root.iter():
        if local_name(node.tag) in {"shortName", "name"}:
            node.text = PROFILE_ALLOWED_OPERATOR_NAME

    version = next((x for x in root.iter() if local_name(x.tag) == "dataSetVersion"), None)
    if version is not None:
        version.text = "00.00.002"

    target_contact.parent.mkdir(parents=True, exist_ok=True)
    tree.write(target_contact, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return {
        "uuid": PROFILE_ALLOWED_OPERATOR_UUID,
        "display_name": PROFILE_ALLOWED_OPERATOR_NAME,
        "fixture_semantics": "Synthetic local link-resolution placeholder using a profile-allowed identifier only; no affiliation, approval, registration, or authority is claimed.",
        "sha256": sha256_file(target_contact),
    }


def build(sample_root: Path, master_root: Path, profile_jar: Path, output_root: Path) -> dict[str, Any]:
    sample_root = sample_root.resolve()
    master_root = master_root.resolve()
    profile_jar = profile_jar.resolve()
    output_root = output_root.resolve()
    require(sample_root.is_dir(), "sample root missing")
    require(master_root.is_dir(), "master-data root missing")
    require(profile_jar.is_file(), "profile JAR missing")

    if output_root.exists():
        shutil.rmtree(output_root)
    package_root = output_root / "ILCD"
    package_root.mkdir(parents=True)

    closure = copy_reference_closure(sample_root, master_root, package_root)
    categories_file, category_path = extract_profile_categories(profile_jar, output_root / "_profile_evidence")

    original_process = package_root / "processes" / "57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml"
    require(original_process.is_file(), "closure did not include base process")
    synthetic_process = package_root / "processes" / f"{SYNTHETIC_PROCESS_UUID}.xml"
    original_process.rename(synthetic_process)
    process_changes = mutate_process(synthetic_process, category_path)

    original_operator = package_root / "contacts" / "bee77d31-1837-404b-abdf-ef271c83e5a7.xml"
    require(original_operator.is_file(), "closure did not include base Swift contact")
    synthetic_operator = package_root / "contacts" / f"{PROFILE_ALLOWED_OPERATOR_UUID}.xml"
    operator_receipt = create_synthetic_operator_contact(original_operator, synthetic_operator)
    # Retain the original Swift contact because public source-document datasets
    # in the recursive closure still reference it independently of the process's
    # registration-authority/publisher fields.

    files: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": str(path.relative_to(output_root)),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
            )

    receipt: dict[str, Any] = {
        "builder": {
            "name": "ProofGrid v0.8 synthetic ÖKOBAUDAT fixture builder",
            "version": "0.8.0-iteration-2",
        },
        "source": {
            "indata_v12_process_uuid": START_PROCESS_UUID,
            "source_semantics": "Pinned public Apache-2.0 InData sample plus pinned public InData master data.",
        },
        "profile_dependency": {
            "name": "EPD 1.2 ÖKOBAUDAT",
            "version": "3.8.0",
            "jar_sha256": sha256_file(profile_jar),
            "category_resource": PROFILE_CATEGORIES_RESOURCE,
            "category_resource_sha256": sha256_file(categories_file),
        },
        "closure": closure,
        "process_changes": process_changes,
        "operator_contact": operator_receipt,
        "output_files": files,
        "limitations": [
            "This is a synthetic non-production profile-conformance fixture, not a real Environmental Product Declaration.",
            "Use of a profile-allowed programme-operator identifier is solely an interoperability test input and does not state affiliation, registration, approval, publisher authority, or source-use permission.",
            "Passing a validation profile would not establish scientific validity, product representativeness, BBSR plausibility approval, professional LCA review, or certification.",
        ],
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    (output_root / "fixture-build-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-root", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--profile-jar", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = build(args.sample_root, args.master_root, args.profile_jar, args.output_root)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    print(
        json.dumps(
            {
                "receipt_sha256": receipt["receipt_sha256"],
                "synthetic_process_uuid": receipt["process_changes"]["synthetic_process_uuid"],
                "selected_category_path": receipt["process_changes"]["selected_oekobaudat_category_path"],
                "classification_name": receipt["process_changes"]["classification_name"],
                "copied_digital_files": len(receipt["closure"]["copied_digital_files"]),
                "output_files": len(receipt["output_files"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
