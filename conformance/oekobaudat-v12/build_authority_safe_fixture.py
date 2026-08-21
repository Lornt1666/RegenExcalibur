#!/usr/bin/env python3
"""Build the v0.8 synthetic fixture with an explicit byte-level authority boundary.

This wrapper deliberately does not alter the environmental values or profile
rules used by the existing deterministic synthetic builder. It hardens only the
identity/authority presentation of the synthetic programme-operator placeholder:

- the profile-allowed operator UUID remains solely an interoperability test key;
- displayed contact/reference names are changed to an explicit ProofGrid
  synthetic placeholder instead of presenting a real organisation name;
- the schema-correct ILCD `contactDescriptionOrComment` field records the
  non-affiliation/non-authority semantics;
- real contact/address channels are removed;
- all output hashes and the builder receipt are recomputed after hardening.

Passing the official profile after this transformation proves only bounded
synthetic profile compatibility. It is not registration, programme-operator
approval, BBSR plausibility approval, source-use permission, or certification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET

import build_synthetic_fixture as base

SYNTHETIC_OPERATOR_LABEL = "ProofGrid synthetic programme-operator placeholder"
SYNTHETIC_OPERATOR_DESCRIPTION = (
    "Synthetic local profile-conformance placeholder. The profile-allowed programme-operator UUID is used "
    "only as an interoperability test identifier; no affiliation, no approval, no registration, no contact "
    "authority, and no source-use permission is claimed."
)
FORBIDDEN_CONTACT_FIELDS = {
    "contactAddress",
    "telephone",
    "telefax",
    "email",
    "WWWAddress",
    "centralContactPoint",
    "referenceToContact",
    "referenceToLogo",
}


def node_text(node: ET.Element) -> str:
    return " ".join(part.strip() for part in node.itertext() if part and part.strip())


def find_first(root: ET.Element, name: str) -> ET.Element | None:
    return next((node for node in root.iter() if base.local_name(node.tag) == name), None)


def harden_operator_contact(operator_path: Path) -> dict[str, Any]:
    base.register_namespaces()
    tree = ET.parse(operator_path)
    root = tree.getroot()
    data_info = find_first(root, "dataSetInformation")
    base.require(data_info is not None, "synthetic operator dataSetInformation missing")

    uuid_node = find_first(root, "UUID")
    base.require(uuid_node is not None and (uuid_node.text or "").strip() == base.PROFILE_ALLOWED_OPERATOR_UUID,
                 "synthetic operator UUID mismatch before authority hardening")

    # Replace visible identity labels with an unambiguously synthetic label.
    for node in root.iter():
        if base.local_name(node.tag) in {"shortName", "name"}:
            node.text = SYNTHETIC_OPERATOR_LABEL

    # Remove any inherited contact/relationship channels. These are not needed
    # for profile interoperability and could imply a real contact relationship.
    removed: list[str] = []
    for parent in root.iter():
        for child in list(parent):
            if base.local_name(child.tag) in FORBIDDEN_CONTACT_FIELDS:
                removed.append(base.local_name(child.tag))
                parent.remove(child)

    # Remove any existing comments and write exactly one schema-correct,
    # English authority-boundary marker in the Contact namespace.
    for child in list(data_info):
        if base.local_name(child.tag) == "contactDescriptionOrComment":
            data_info.remove(child)
    marker = ET.SubElement(
        data_info,
        f"{{{base.CONTACT_NS}}}contactDescriptionOrComment",
        {f"{{{base.XML_NS}}}lang": "en"},
    )
    marker.text = SYNTHETIC_OPERATOR_DESCRIPTION

    tree.write(operator_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)

    # Verify the bytes we just wrote, rather than trusting the mutation code.
    verify_root = ET.parse(operator_path).getroot()
    descriptions = [
        node_text(node)
        for node in verify_root.iter()
        if base.local_name(node.tag) == "contactDescriptionOrComment" and node_text(node)
    ]
    base.require(descriptions == [SYNTHETIC_OPERATOR_DESCRIPTION], "authority marker did not round-trip exactly")
    for node in verify_root.iter():
        base.require(base.local_name(node.tag) not in FORBIDDEN_CONTACT_FIELDS,
                     f"forbidden synthetic contact channel survived: {base.local_name(node.tag)}")

    return {
        "uuid": base.PROFILE_ALLOWED_OPERATOR_UUID,
        "display_name": SYNTHETIC_OPERATOR_LABEL,
        "description_field": "contactDescriptionOrComment",
        "description": SYNTHETIC_OPERATOR_DESCRIPTION,
        "fixture_semantics": (
            "Synthetic local link-resolution placeholder using a profile-allowed identifier only; no affiliation, "
            "no approval, no registration, no contact authority, and no source-use permission is claimed."
        ),
        "authority_inference_allowed": False,
        "removed_contact_or_relationship_fields": sorted(set(removed)),
        "forbidden_contact_channels_present": [],
        "sha256": base.sha256_file(operator_path),
    }


def harden_process_operator_labels(process_path: Path) -> dict[str, Any]:
    base.register_namespaces()
    tree = ET.parse(process_path)
    root = tree.getroot()
    changed = 0
    for node in root.iter():
        if base.local_name(node.tag) not in {"referenceToRegistrationAuthority", "referenceToPublisher"}:
            continue
        if node.attrib.get("refObjectId") != base.PROFILE_ALLOWED_OPERATOR_UUID:
            continue
        for child in node.iter():
            if base.local_name(child.tag) == "shortDescription":
                child.text = SYNTHETIC_OPERATOR_LABEL
                changed += 1
    base.require(changed >= 1, "no programme-operator reference label was hardened")
    tree.write(process_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return {
        "changed_reference_descriptions": changed,
        "display_label": SYNTHETIC_OPERATOR_LABEL,
        "sha256": base.sha256_file(process_path),
    }


def recompute_output_files(output_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file() or path.name == "fixture-build-receipt.json":
            continue
        rows.append({
            "path": path.relative_to(output_root).as_posix(),
            "sha256": base.sha256_file(path),
            "size": path.stat().st_size,
        })
    return rows


def build(sample_root: Path, master_root: Path, profile_jar: Path, output_root: Path) -> dict[str, Any]:
    receipt = base.build(sample_root, master_root, profile_jar, output_root)

    operator_path = output_root / "ILCD" / "contacts" / f"{base.PROFILE_ALLOWED_OPERATOR_UUID}.xml"
    process_path = output_root / "ILCD" / "processes" / f"{base.SYNTHETIC_PROCESS_UUID}.xml"
    base.require(operator_path.is_file(), "base fixture did not create synthetic operator placeholder")
    base.require(process_path.is_file(), "base fixture did not create synthetic process")

    operator_receipt = harden_operator_contact(operator_path)
    process_authority_receipt = harden_process_operator_labels(process_path)

    receipt.pop("receipt_sha256", None)
    receipt["builder"] = {
        "name": "ProofGrid v0.8 authority-safe synthetic ÖKOBAUDAT fixture builder",
        "version": "0.8.1",
        "base_builder": "build_synthetic_fixture.py v0.8.0",
    }
    receipt["operator_contact"] = operator_receipt
    receipt["authority_boundary"] = {
        "profile_allowed_operator_uuid": base.PROFILE_ALLOWED_OPERATOR_UUID,
        "identifier_role": "SYNTHETIC_INTEROPERABILITY_TEST_INPUT_ONLY",
        "real_organisation_name_presented_as_fixture_identity": False,
        "authority_inference_allowed": False,
        "process_reference_hardening": process_authority_receipt,
    }
    receipt["process_changes"]["operator_reference_display_label"] = SYNTHETIC_OPERATOR_LABEL
    receipt["process_changes"]["synthetic_process_sha256_after_authority_hardening"] = base.sha256_file(process_path)
    receipt["output_files"] = recompute_output_files(output_root)
    receipt["limitations"] = [
        "This is a synthetic non-production profile-conformance fixture, not a real Environmental Product Declaration.",
        "The profile-allowed programme-operator UUID is solely an interoperability test input; the package explicitly does not state affiliation, approval, registration, publisher authority, contact authority, or source-use permission.",
        "The visible synthetic placeholder label is deliberately not the real programme-operator name.",
        "Profile warnings are retained rather than filled with invented environmental values solely to silence warnings.",
        "Passing a validation profile would not establish scientific validity, product representativeness, BBSR plausibility approval, professional LCA review, programme-operator acceptance, or certification.",
    ]
    receipt["receipt_sha256"] = base.canonical_sha256(receipt)
    (output_root / "fixture-build-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
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
        receipt = build(args.sample_root.resolve(), args.master_root.resolve(), args.profile_jar.resolve(), args.output_root.resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "receipt_sha256": receipt["receipt_sha256"],
        "builder_version": receipt["builder"]["version"],
        "operator_sha256": receipt["operator_contact"]["sha256"],
        "process_sha256": receipt["process_changes"]["synthetic_process_sha256_after_authority_hardening"],
        "authority_inference_allowed": receipt["authority_boundary"]["authority_inference_allowed"],
        "output_files": len(receipt["output_files"]),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
