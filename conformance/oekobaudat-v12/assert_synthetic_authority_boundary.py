#!/usr/bin/env python3
"""Fail closed if the v0.8 synthetic profile fixture could be mistaken for real authority.

This guard does not decide ÖKOBAUDAT profile compatibility. The official profile
runner does that separately. This guard only proves that the synthetic package
and its receipts preserve explicit non-affiliation / non-certification semantics
around the profile-allowed programme-operator identifier used for link/rule
interoperability testing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
EXPECTED_PROCESS_UUID = "6b47f4cf-0bc4-4e0d-b9fd-9d5f845d1de0"
EXPECTED_OPERATOR_UUID = "d111dbec-b024-4be5-86c5-752d6eb2cf95"
EXPECTED_REGISTRATION = "RX-PROOFGRID-V08-SYNTH-001"
FORBIDDEN_CONTACT_FIELDS = {
    "contactAddress", "email", "wwwAddress", "phone", "fax", "faxNumber"
}


class BoundaryError(ValueError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def first_text(root: ET.Element, name: str) -> str:
    for node in root.iter():
        if local_name(node.tag) == name and node.text and node.text.strip():
            return node.text.strip()
    return ""


def inspect(package_root: Path, build_receipt_path: Path, final_receipt_path: Path) -> dict:
    package_root = package_root.resolve()
    build_receipt_path = build_receipt_path.resolve()
    final_receipt_path = final_receipt_path.resolve()
    if not package_root.is_dir():
        raise BoundaryError("synthetic package root is missing")
    if not build_receipt_path.is_file() or not final_receipt_path.is_file():
        raise BoundaryError("required build/final receipt is missing")

    build = json.loads(build_receipt_path.read_text(encoding="utf-8"))
    final = json.loads(final_receipt_path.read_text(encoding="utf-8"))

    process_files = sorted((package_root / "ILCD" / "processes").glob("*.xml"))
    if len(process_files) != 1:
        raise BoundaryError(f"expected exactly one synthetic process; found {len(process_files)}")
    process_path = process_files[0]
    process_root = ET.parse(process_path).getroot()
    if process_root.tag != f"{{{PROCESS_NS}}}processDataSet":
        raise BoundaryError("synthetic process root is not processDataSet")
    if process_root.attrib.get(f"{{{EPD_2019_NS}}}epd-version") != "1.2":
        raise BoundaryError("synthetic process is not explicitly ILCD+EPD v1.2")
    if first_text(process_root, "UUID") != EXPECTED_PROCESS_UUID:
        raise BoundaryError("unexpected synthetic process UUID")
    if first_text(process_root, "registrationNumber") != EXPECTED_REGISTRATION:
        raise BoundaryError("synthetic registration marker is missing or changed")

    comments = [
        (node.text or "").strip()
        for node in process_root.iter()
        if local_name(node.tag) == "generalComment" and (node.text or "").strip()
    ]
    joined_comments = " ".join(comments).lower()
    if "synthetic non-production interoperability fixture" not in joined_comments:
        raise BoundaryError("process does not visibly identify itself as a synthetic non-production fixture")
    if "no affiliation" not in joined_comments or "no" not in joined_comments:
        raise BoundaryError("process comment does not preserve explicit non-affiliation semantics")

    operator_refs = []
    for node in process_root.iter():
        if local_name(node.tag) in {"referenceToRegistrationAuthority", "referenceToPublisher"}:
            operator_refs.append({
                "field": local_name(node.tag),
                "refObjectId": node.attrib.get("refObjectId"),
                "shortDescription": first_text(node, "shortDescription"),
            })
    if not operator_refs or any(x["refObjectId"] != EXPECTED_OPERATOR_UUID for x in operator_refs):
        raise BoundaryError("profile-allowed operator identifier is not isolated to the expected synthetic test reference")

    operator_path = package_root / "ILCD" / "contacts" / f"{EXPECTED_OPERATOR_UUID}.xml"
    if not operator_path.is_file():
        raise BoundaryError("synthetic operator placeholder contact is missing")
    operator_root = ET.parse(operator_path).getroot()
    if first_text(operator_root, "UUID") != EXPECTED_OPERATOR_UUID:
        raise BoundaryError("synthetic operator contact UUID mismatch")
    description = first_text(operator_root, "contactDescription")
    lower_description = description.lower()
    required_phrases = ("synthetic local profile-conformance placeholder", "no affiliation", "no", "authority")
    if any(phrase not in lower_description for phrase in required_phrases):
        raise BoundaryError("synthetic operator contact description does not preserve the non-authority boundary")

    forbidden_present = []
    for node in operator_root.iter():
        if local_name(node.tag) in FORBIDDEN_CONTACT_FIELDS and ((node.text or "").strip() or node.attrib):
            forbidden_present.append(local_name(node.tag))
    if forbidden_present:
        raise BoundaryError(f"synthetic operator placeholder contains contact/address channels: {sorted(set(forbidden_present))}")

    semantics = build.get("operator_contact", {}).get("fixture_semantics", "")
    if "no affiliation" not in semantics.lower() or "source-use permission" not in semantics.lower():
        raise BoundaryError("builder receipt lost explicit non-affiliation/source-use semantics")
    build_limitations = " ".join(build.get("limitations", [])).lower()
    if "synthetic non-production" not in build_limitations or "does not state affiliation" not in build_limitations:
        raise BoundaryError("builder limitations do not preserve the authority boundary")

    if final.get("certified") is not False:
        raise BoundaryError("final receipt must remain certified=false")
    final_limitations = " ".join(final.get("limitations", [])).lower()
    for phrase in (
        "synthetic and non-production",
        "does not state affiliation",
        "source acquisition/use authorization remains a separate",
    ):
        if phrase not in final_limitations:
            raise BoundaryError(f"final receipt is missing required limitation phrase: {phrase}")

    receipt = {
        "gate": "ProofGrid v0.8 synthetic authority boundary",
        "verdict": "SYNTHETIC_AUTHORITY_BOUNDARY_PASS",
        "authority_inference_allowed": False,
        "certified": False,
        "profile_operator_identifier_role": "SYNTHETIC_INTEROPERABILITY_TEST_INPUT_ONLY",
        "synthetic_process": {
            "uuid": EXPECTED_PROCESS_UUID,
            "registration_number": EXPECTED_REGISTRATION,
            "sha256": sha256_file(process_path),
            "non_production_marker_present": True,
            "non_affiliation_marker_present": True,
        },
        "synthetic_operator_placeholder": {
            "uuid": EXPECTED_OPERATOR_UUID,
            "sha256": sha256_file(operator_path),
            "description": description,
            "forbidden_contact_channels_present": [],
            "profile_reference_fields": operator_refs,
        },
        "source_receipts": {
            "builder_receipt_sha256": build.get("receipt_sha256"),
            "final_profile_receipt_sha256": final.get("receipt_sha256"),
        },
        "limitations": [
            "This guard proves only explicit synthetic/non-affiliation semantics around a test identifier.",
            "It does not grant or prove programme-operator affiliation, registration, approval, publisher authority, contact authority, source-use rights, scientific validity, professional review, BBSR plausibility approval, or certification.",
        ],
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--final-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = inspect(args.package_root, args.build_receipt, args.final_receipt)
    except (BoundaryError, ET.ParseError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
