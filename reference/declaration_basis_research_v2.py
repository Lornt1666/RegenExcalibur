#!/usr/bin/env python3
"""ProofGrid v1.3 research-only declaration/reference basis resolver (v2).

This resolver walks the pinned ILCD+EPD process → flow → flow-property →
unit-group graph by exact dataset UUID and referenced dataset version. It keeps
version-specific copies separate: a same UUID in v1.2 and v1.3 is not considered
an ambiguity merely because the serialized bytes differ between format versions.

No declaration basis is selected. Both reference-exchange meanAmount and
resultingAmount are retained as evidence, and building quantity multiplication
remains prohibited.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

EPD_2019_NS = "http://www.indata.network/EPD/2019"
XML_NS = "http://www.w3.org/XML/1998/namespace"

V12_COMMIT = "b7233bd2dd5435a6b5973505ffa212cd03d23468"
V13_COMMIT = "7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa"
MASTER_COMMIT = "32117b6a70d6c486344247a429449755a2c7eab4"

V12_PROCESS = Path("sample_data/processes/57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")
V13_PROCESS = Path("sample_data/processes/EPDv1.3_example_57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")


class ResearchError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetCandidate:
    source: str
    root: Path
    path: Path
    uuid: str
    kind: str
    dataset_version: str | None
    sha256: str

    def relative_path(self) -> str:
        return self.path.relative_to(self.root).as_posix()

    def row(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.relative_path(),
            "uuid": self.uuid,
            "kind": self.kind,
            "dataset_version": self.dataset_version,
            "sha256": self.sha256,
        }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchError(message)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    value = (node.text or "").strip()
    return value or None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_decimal(value: str | None, label: str) -> dict[str, str] | None:
    if value is None:
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ResearchError(f"{label} is not numeric: {value!r}") from exc
    require(number.is_finite(), f"{label} must be finite: {value!r}")
    if number == 0:
        normalized = "0"
    else:
        normalized = format(number, "f")
        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")
        if normalized == "-0":
            normalized = "0"
    return {"lexical": value, "decimal": normalized}


def first_uuid(root: ET.Element) -> str | None:
    for node in root.iter():
        if local(node.tag) == "UUID" and text(node):
            return text(node)
    return None


def dataset_version(root: ET.Element) -> str | None:
    versions = [text(node) for node in root.iter() if local(node.tag) == "dataSetVersion" and text(node)]
    if not versions:
        return None
    unique = sorted(set(versions))
    require(len(unique) == 1, f"dataset contains ambiguous dataSetVersion values: {unique}")
    return unique[0]


def build_index(roots: list[tuple[str, Path]]) -> dict[str, list[DatasetCandidate]]:
    index: dict[str, list[DatasetCandidate]] = {}
    for source, root_path in roots:
        for path in sorted(root_path.rglob("*.xml")):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            uuid = first_uuid(root)
            if not uuid:
                continue
            row = DatasetCandidate(
                source=source,
                root=root_path,
                path=path,
                uuid=uuid,
                kind=local(root.tag),
                dataset_version=dataset_version(root),
                sha256=sha256_file(path),
            )
            index.setdefault(uuid, []).append(row)
    return index


def resolve_uuid(
    index: dict[str, list[DatasetCandidate]],
    uuid: str,
    *,
    preferred_source: str,
    expected_kinds: set[str],
    expected_version: str | None,
) -> tuple[DatasetCandidate, dict[str, Any]]:
    all_candidates = [row for row in index.get(uuid, []) if row.kind in expected_kinds]
    require(bool(all_candidates), f"UUID unresolved for kinds {sorted(expected_kinds)}: {uuid}")

    version_candidates = all_candidates
    if expected_version:
        exact = [row for row in all_candidates if row.dataset_version == expected_version]
        require(
            bool(exact),
            f"UUID {uuid} has no candidate with referenced dataSetVersion={expected_version}; candidates={[row.row() for row in all_candidates]}",
        )
        version_candidates = exact

    preferred = [row for row in version_candidates if row.source == preferred_source]
    master = [row for row in version_candidates if row.source == "master"]

    if preferred:
        selected_pool = preferred
        policy = "EXACT_VERSION_PREFERRED_FORMAT_SOURCE"
    elif master:
        selected_pool = master
        policy = "EXACT_VERSION_PINNED_MASTER_FALLBACK"
    else:
        sources = sorted({row.source for row in version_candidates})
        require(
            len(sources) == 1,
            f"UUID {uuid} exact-version candidates are cross-source ambiguous without preferred/master candidate: {sources}",
        )
        selected_pool = version_candidates
        policy = "EXACT_VERSION_SINGLE_SOURCE_FALLBACK"

    selected_hashes = sorted({row.sha256 for row in selected_pool})
    require(
        len(selected_hashes) == 1,
        f"UUID {uuid} selected source/version contains non-identical bytes: {selected_hashes}",
    )
    selected = sorted(selected_pool, key=lambda row: row.relative_path())[0]

    return selected, {
        "uuid": uuid,
        "referenced_dataset_version": expected_version,
        "candidate_count_all_versions": len(all_candidates),
        "candidate_count_exact_version": len(version_candidates),
        "selected_pool_count": len(selected_pool),
        "selected_pool_distinct_hash_count": len(selected_hashes),
        "selection_policy": policy,
        "selected": selected.row(),
        "all_candidates": [row.row() for row in sorted(all_candidates, key=lambda row: (row.source, row.dataset_version or "", row.relative_path()))],
        "cross_version_serialization_difference_allowed": True,
    }


def child(parent: ET.Element, name: str) -> ET.Element | None:
    return next((node for node in list(parent) if local(node.tag) == name), None)


def children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in list(parent) if local(node.tag) == name]


def descendants(parent: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in parent.iter() if local(node.tag) == name]


def multilingual(node: ET.Element | None) -> list[dict[str, str | None]]:
    if node is None:
        return []
    rows: list[dict[str, str | None]] = []
    for item in node.iter():
        if local(item.tag) not in {"baseName", "shortDescription", "name"}:
            continue
        value = text(item)
        if value is None:
            continue
        rows.append({
            "element": local(item.tag),
            "language": item.attrib.get(f"{{{XML_NS}}}lang"),
            "value": value,
        })
    return rows


def find_unique_descendant(root: ET.Element, name: str, label: str) -> ET.Element:
    matches = descendants(root, name)
    require(len(matches) == 1, f"{label}: expected exactly one {name}, found {len(matches)}")
    return matches[0]


def parse_process(path: Path, expected_epd_version: str) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(local(root.tag) == "processDataSet", f"not processDataSet: {path}")
    uuid = first_uuid(root)
    require(bool(uuid), "process UUID missing")
    epd_version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
    require(epd_version == expected_epd_version, f"expected epd-version {expected_epd_version}, got {epd_version}")

    quantitative = find_unique_descendant(root, "quantitativeReference", "process")
    ref_ids = [text(node) for node in children(quantitative, "referenceToReferenceFlow") if text(node)]
    require(len(ref_ids) == 1, f"process reference-flow IDs ambiguous: {ref_ids}")
    internal_id = ref_ids[0]

    exchanges = find_unique_descendant(root, "exchanges", "process")
    matches = [node for node in children(exchanges, "exchange") if node.attrib.get("dataSetInternalID") == internal_id]
    require(len(matches) == 1, f"process reference exchange {internal_id} resolved to {len(matches)} exchanges")
    exchange = matches[0]
    flow_ref = child(exchange, "referenceToFlowDataSet")
    require(flow_ref is not None, "process reference exchange lacks referenceToFlowDataSet")
    flow_uuid = flow_ref.attrib.get("refObjectId")
    require(bool(flow_uuid), "flow reference UUID missing")

    return {
        "process": {
            "path": path.as_posix(),
            "sha256": sha256_file(path),
            "uuid": uuid,
            "dataset_version": dataset_version(root),
            "epd_version": epd_version,
        },
        "quantitative_reference": {
            "type": quantitative.attrib.get("type"),
            "reference_flow_internal_ids": ref_ids,
        },
        "reference_exchange": {
            "internal_id": internal_id,
            "mean_amount": canonical_decimal(text(child(exchange, "meanAmount")), "reference exchange meanAmount"),
            "resulting_amount": canonical_decimal(text(child(exchange, "resultingAmount")), "reference exchange resultingAmount"),
            "reference_to_flow_dataset": {
                "uuid": flow_uuid,
                "version": flow_ref.attrib.get("version"),
                "uri": flow_ref.attrib.get("uri"),
                "descriptions": multilingual(flow_ref),
            },
        },
    }


def parse_flow(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(local(root.tag) == "flowDataSet", f"not flowDataSet: {path}")
    uuid = first_uuid(root)
    require(bool(uuid), "flow UUID missing")

    quantitative_candidates = descendants(root, "quantitativeReference")
    flow_property_refs: list[tuple[ET.Element, list[str]]] = []
    for q in quantitative_candidates:
        ids = [text(node) for node in children(q, "referenceToReferenceFlowProperty") if text(node)]
        if ids:
            flow_property_refs.append((q, ids))
    require(len(flow_property_refs) == 1, f"flow quantitative-reference candidates with reference property IDs: {[(q.attrib, ids) for q, ids in flow_property_refs]}")
    quantitative, ref_ids = flow_property_refs[0]
    require(len(ref_ids) == 1, f"flow reference flow-property IDs ambiguous: {ref_ids}")
    internal_id = ref_ids[0]

    properties_parents = descendants(root, "flowProperties")
    require(len(properties_parents) == 1, f"flowProperties collections found: {len(properties_parents)}")
    relations = [node for node in children(properties_parents[0], "flowProperty") if node.attrib.get("dataSetInternalID") == internal_id]
    require(len(relations) == 1, f"flow reference property relation {internal_id} resolved to {len(relations)} entries")
    relation = relations[0]
    property_ref = child(relation, "referenceToFlowPropertyDataSet")
    require(property_ref is not None, "flow relation lacks referenceToFlowPropertyDataSet")
    property_uuid = property_ref.attrib.get("refObjectId")
    require(bool(property_uuid), "flow-property reference UUID missing")

    material_signals: list[dict[str, Any]] = []
    for node in root.iter():
        if local(node.tag) not in {"materialProperties", "materialProperty"}:
            continue
        material_signals.append({
            "element": local(node.tag),
            "attributes": {local(key): value for key, value in sorted(node.attrib.items())},
            "text": text(node),
            "children": [
                {
                    "element": local(c.tag),
                    "attributes": {local(key): value for key, value in sorted(c.attrib.items())},
                    "text": text(c),
                }
                for c in list(node)
            ],
        })

    return {
        "flow": {
            "path": path.as_posix(),
            "sha256": sha256_file(path),
            "uuid": uuid,
            "dataset_version": dataset_version(root),
            "names": multilingual(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "quantitative_reference": {
            "type": quantitative.attrib.get("type"),
            "reference_flow_property_internal_ids": ref_ids,
        },
        "reference_flow_property_relation": {
            "internal_id": internal_id,
            "mean_value": canonical_decimal(text(child(relation, "meanValue")), "flow property relation meanValue"),
            "reference_to_flow_property_dataset": {
                "uuid": property_uuid,
                "version": property_ref.attrib.get("version"),
                "uri": property_ref.attrib.get("uri"),
                "descriptions": multilingual(property_ref),
            },
        },
        "material_property_signals": material_signals,
    }


def parse_flow_property(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(local(root.tag) == "flowPropertyDataSet", f"not flowPropertyDataSet: {path}")
    uuid = first_uuid(root)
    require(bool(uuid), "flow-property UUID missing")

    refs = [
        node for node in root.iter()
        if "unitgroup" in local(node.tag).lower() and node.attrib.get("refObjectId")
    ]
    identities = sorted({(node.attrib.get("refObjectId"), node.attrib.get("version")) for node in refs})
    require(len(identities) == 1, f"flow-property unit-group reference ambiguous: {identities}")
    unit_uuid, unit_version = identities[0]
    selected = next(node for node in refs if node.attrib.get("refObjectId") == unit_uuid and node.attrib.get("version") == unit_version)

    return {
        "flow_property": {
            "path": path.as_posix(),
            "sha256": sha256_file(path),
            "uuid": uuid,
            "dataset_version": dataset_version(root),
            "names": multilingual(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "reference_to_unit_group": {
            "element": local(selected.tag),
            "uuid": unit_uuid,
            "version": unit_version,
            "uri": selected.attrib.get("uri"),
            "descriptions": multilingual(selected),
        },
    }


def parse_unit_group(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(local(root.tag) == "unitGroupDataSet", f"not unitGroupDataSet: {path}")
    uuid = first_uuid(root)
    require(bool(uuid), "unit-group UUID missing")

    quantitative_candidates = descendants(root, "quantitativeReference")
    ref_candidates: list[tuple[ET.Element, list[str]]] = []
    for q in quantitative_candidates:
        ids = [text(node) for node in children(q, "referenceToReferenceUnit") if text(node)]
        if ids:
            ref_candidates.append((q, ids))
    require(len(ref_candidates) == 1, f"unit-group quantitative-reference candidates: {[(q.attrib, ids) for q, ids in ref_candidates]}")
    quantitative, ids = ref_candidates[0]
    require(len(ids) == 1, f"unit-group reference-unit IDs ambiguous: {ids}")
    internal_id = ids[0]

    unit_collections = descendants(root, "units")
    require(len(unit_collections) == 1, f"unit collections found: {len(unit_collections)}")
    matches = [node for node in children(unit_collections[0], "unit") if node.attrib.get("dataSetInternalID") == internal_id]
    require(len(matches) == 1, f"reference unit {internal_id} resolved to {len(matches)} units")
    unit = matches[0]
    name = text(child(unit, "name"))
    conversion = canonical_decimal(text(child(unit, "meanValue")), "unit reference meanValue")
    require(bool(name), "reference unit name missing")
    require(conversion is not None, "reference unit conversion factor missing")

    return {
        "unit_group": {
            "path": path.as_posix(),
            "sha256": sha256_file(path),
            "uuid": uuid,
            "dataset_version": dataset_version(root),
            "names": multilingual(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "reference_unit": {
            "internal_id": internal_id,
            "name": name,
            "conversion_factor": conversion,
            "quantitative_reference_type": quantitative.attrib.get("type"),
        },
    }


def research_one(
    process_path: Path,
    epd_version: str,
    preferred_source: str,
    index: dict[str, list[DatasetCandidate]],
) -> dict[str, Any]:
    process = parse_process(process_path, epd_version)

    flow_ref = process["reference_exchange"]["reference_to_flow_dataset"]
    flow_candidate, flow_resolution = resolve_uuid(
        index,
        flow_ref["uuid"],
        preferred_source=preferred_source,
        expected_kinds={"flowDataSet"},
        expected_version=flow_ref.get("version"),
    )
    flow = parse_flow(flow_candidate.path)

    property_ref = flow["reference_flow_property_relation"]["reference_to_flow_property_dataset"]
    property_candidate, property_resolution = resolve_uuid(
        index,
        property_ref["uuid"],
        preferred_source=preferred_source,
        expected_kinds={"flowPropertyDataSet"},
        expected_version=property_ref.get("version"),
    )
    flow_property = parse_flow_property(property_candidate.path)

    unit_ref = flow_property["reference_to_unit_group"]
    unit_candidate, unit_resolution = resolve_uuid(
        index,
        unit_ref["uuid"],
        preferred_source=preferred_source,
        expected_kinds={"unitGroupDataSet"},
        expected_version=unit_ref.get("version"),
    )
    unit_group = parse_unit_group(unit_candidate.path)

    return {
        "process_reference": process,
        "flow_resolution": flow_resolution,
        "flow_reference": flow,
        "flow_property_resolution": property_resolution,
        "flow_property_reference": flow_property,
        "unit_group_resolution": unit_resolution,
        "unit_group_reference": unit_group,
        "declaration_basis_selected": False,
        "building_quantity_multiplication_permitted": False,
        "unit_conversion_performed": False,
    }


def build_receipt(v12_root: Path, v13_root: Path, master_root: Path) -> dict[str, Any]:
    index = build_index([
        ("v12", v12_root),
        ("v13", v13_root),
        ("master", master_root),
    ])
    v12 = research_one(v12_root / V12_PROCESS, "1.2", "v12", index)
    v13 = research_one(v13_root / V13_PROCESS, "1.3", "v13", index)

    comparison = {
        "reference_flow_uuid_matches": v12["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"] == v13["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"],
        "reference_flow_property_uuid_matches": v12["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"] == v13["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"],
        "unit_group_uuid_matches": v12["flow_property_reference"]["reference_to_unit_group"]["uuid"] == v13["flow_property_reference"]["reference_to_unit_group"]["uuid"],
        "reference_exchange_mean_amount_matches": v12["process_reference"]["reference_exchange"]["mean_amount"] == v13["process_reference"]["reference_exchange"]["mean_amount"],
        "reference_exchange_resulting_amount_matches": v12["process_reference"]["reference_exchange"]["resulting_amount"] == v13["process_reference"]["reference_exchange"]["resulting_amount"],
        "reference_unit_matches": v12["unit_group_reference"]["reference_unit"] == v13["unit_group_reference"]["reference_unit"],
    }

    report: dict[str, Any] = {
        "verdict": "DECLARATION_BASIS_STRUCTURE_RESEARCH_VERIFIABLE",
        "research_version": "1.3.1",
        "scope": "Research-only version-aware UUID-resolved declaration/reference basis graph. No declaration basis is selected and no building-level multiplication is permitted.",
        "upstreams": {
            "v12_commit": V12_COMMIT,
            "v13_commit": V13_COMMIT,
            "master_data_commit": MASTER_COMMIT,
        },
        "dataset_index": {
            "unique_uuid_count": len(index),
            "candidate_count": sum(len(rows) for rows in index.values()),
        },
        "v12": v12,
        "v13": v13,
        "comparison": comparison,
        "declaration_basis_selected": False,
        "basis_extractor_accepted": False,
        "building_quantity_multiplication_permitted": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "Same-UUID datasets serialized differently across ILCD+EPD format versions are retained as version-specific candidates; exact referenced dataSetVersion plus preferred pinned source selects the candidate.",
            "The receipt resolves source reference identities and dimensions but does not choose meanAmount or resultingAmount as the declaration basis.",
            "Material-property signals are retained separately and are not treated as the declared reference quantity.",
            "The environmental-result unit is not treated as the product/reference unit.",
            "No building quantity multiplication, LCA conclusion, professional review, regulatory approval, or certification is produced.",
        ],
    }
    report["receipt_sha256"] = hashlib.sha256(canonical_json_bytes(report)).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12-root", type=Path, required=True)
    parser.add_argument("--v13-root", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build_receipt(args.v12_root.resolve(), args.v13_root.resolve(), args.master_root.resolve())
    except ResearchError as exc:
        print(f"FAILED: {exc}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "v12_reference_flow_uuid": report["v12"]["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"],
        "v12_flow_property_uuid": report["v12"]["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"],
        "v12_unit_group_uuid": report["v12"]["flow_property_reference"]["reference_to_unit_group"]["uuid"],
        "v12_reference_unit": report["v12"]["unit_group_reference"]["reference_unit"],
        "v12_mean_amount": report["v12"]["process_reference"]["reference_exchange"]["mean_amount"],
        "v12_resulting_amount": report["v12"]["process_reference"]["reference_exchange"]["resulting_amount"],
        "comparison": report["comparison"],
        "declaration_basis_selected": report["declaration_basis_selected"],
        "receipt_sha256": report["receipt_sha256"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
