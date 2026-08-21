#!/usr/bin/env python3
"""ProofGrid v1.0 admission-bound environmental source identity normalizer.

This layer may run only after the v0.9 admission state machine has admitted the
exact source for normalization. It normalizes deterministic ILCD+EPD process
identity/provenance metadata only. It deliberately does not normalize impact
factors, perform scientific/professional review, or claim certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission as admission  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Source Identity Normalizer"
ENGINE_VERSION = "1.0.0"
VERDICT = "ADMITTED_ENVIRONMENTAL_SOURCE_IDENTITY_VERIFIABLE"
SCHEMA_PATH = ROOT / "schemas" / "environmental-source-identity.schema.json"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
PROCESS_NS = admission.PROCESS_NS
EPD_2019_NS = admission.EPD_2019_NS
XML_NS = "http://www.w3.org/XML/1998/namespace"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64


class CanonicalizationError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CanonicalizationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(f"invalid JSON in {path}: {exc}") from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def first_text(root: ET.Element, wanted: str) -> str | None:
    for node in root.iter():
        if local_name(node.tag) == wanted and node.text and node.text.strip():
            return node.text.strip()
    return None


def validate_schema(instance: dict[str, Any]) -> None:
    schema = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise CanonicalizationError(f"invalid canonical identity schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda err: list(err.path))
    if errors:
        preview = "; ".join(f"{list(err.path)}: {err.message}" for err in errors[:5])
        raise CanonicalizationError(f"canonical source identity failed schema validation: {preview}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CanonicalizationError(message)


def verify_receipt_chain(
    preflight_receipt: dict[str, Any],
    conformance_receipt: dict[str, Any],
    admission_receipt: dict[str, Any],
) -> None:
    try:
        admission.verify_canonical_receipt(preflight_receipt, "admission preflight")
        admission.verify_canonical_receipt(conformance_receipt, "conformance")
        admission.verify_canonical_receipt(admission_receipt, "admission")
        expected = admission.finalize(preflight_receipt, conformance_receipt)
    except admission.AdmissionError as exc:
        raise CanonicalizationError(str(exc)) from exc

    require(
        canonical_json_bytes(expected) == canonical_json_bytes(admission_receipt),
        "admission receipt does not exactly reproduce from the supplied preflight and conformance receipts",
    )
    require(admission_receipt.get("verdict") == admission.VERDICT if hasattr(admission, "VERDICT") else admission_receipt.get("verdict") == "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE", "wrong admission verdict")
    require(admission_receipt.get("state") == "ADMITTED_FOR_NORMALIZATION", "source is not in ADMITTED_FOR_NORMALIZATION state")
    require(admission_receipt.get("admitted") is True, "source is not admitted")
    require(admission_receipt.get("normalization_permitted") is True, "normalization is not permitted")
    require(admission_receipt.get("certified") is False, "admission receipt must remain certified=false")
    require(preflight_receipt.get("certified") is False, "preflight receipt must remain certified=false")
    require(conformance_receipt.get("certified") is False, "conformance receipt must remain certified=false")
    require(
        admission_receipt.get("preflight_receipt_sha256") == preflight_receipt.get("receipt_sha256"),
        "admission/preflight receipt binding mismatch",
    )
    require(
        admission_receipt.get("conformance", {}).get("receipt_sha256") == conformance_receipt.get("receipt_sha256"),
        "admission/conformance receipt binding mismatch",
    )


def extract_process_identity(raw: bytes, *, label: str, expected_version: str) -> dict[str, Any]:
    try:
        root = admission.safe_xml_root(raw, label)
    except admission.AdmissionError as exc:
        raise CanonicalizationError(str(exc)) from exc
    require(root.tag == f"{{{PROCESS_NS}}}processDataSet", f"{label} is not an ILCD processDataSet")
    version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
    require(version == expected_version, f"{label} version mismatch: expected {expected_version}, got {version}")

    info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    require(info is not None, f"{label} lacks processInformation/dataSetInformation")
    uuid_node = info.find(f"{{{COMMON_NS}}}UUID")
    require(uuid_node is not None and bool((uuid_node.text or "").strip()), f"{label} lacks a process dataset UUID")
    dataset_uuid = (uuid_node.text or "").strip()

    names: list[dict[str, str | None]] = []
    name_node = info.find(f"{{{PROCESS_NS}}}name")
    if name_node is not None:
        for node in name_node:
            if local_name(node.tag) != "baseName":
                continue
            value = (node.text or "").strip()
            if not value:
                continue
            names.append({"language": node.attrib.get(f"{{{XML_NS}}}lang"), "value": value})
    names.sort(key=lambda row: ((row["language"] or ""), row["value"]))

    return {
        "process_dataset_uuid": dataset_uuid,
        "process_xml_sha256": sha256_bytes(raw),
        "dataset_version": first_text(root, "dataSetVersion"),
        "names": names,
        "registration_number": first_text(root, "registrationNumber"),
    }


def source_identity(source_path: Path, *, media_type: str, expected_version: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        detected = admission.detect_source(source_path, media_type)
    except admission.AdmissionError as exc:
        raise CanonicalizationError(str(exc)) from exc
    require(detected["detected_version"] == expected_version, "detected source version does not match admitted version")

    if detected["container"] == "XML":
        identity = extract_process_identity(source_path.read_bytes(), label=source_path.name, expected_version=expected_version)
        return detected, identity

    require(detected["container"] == "ZIP", f"unsupported admitted source container: {detected['container']}")
    process_rows: list[tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(source_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                try:
                    path = admission.safe_zip_name(info.filename)
                except admission.AdmissionError as exc:
                    raise CanonicalizationError(str(exc)) from exc
                name = path.as_posix()
                if name.startswith("ILCD/processes/") and name.lower().endswith(".xml"):
                    process_rows.append((name, zf.read(info)))
    except zipfile.BadZipFile as exc:
        raise CanonicalizationError(f"invalid ZIP source: {source_path}") from exc

    require(len(process_rows) == 1, f"single-record normalization requires exactly one ILCD process dataset; found {len(process_rows)}")
    label, raw = process_rows[0]
    return detected, extract_process_identity(raw, label=label, expected_version=expected_version)


def build_record(
    source_path: Path,
    preflight_receipt: dict[str, Any],
    conformance_receipt: dict[str, Any],
    admission_receipt: dict[str, Any],
) -> dict[str, Any]:
    verify_receipt_chain(preflight_receipt, conformance_receipt, admission_receipt)

    source_path = Path(source_path).resolve()
    require(source_path.is_file(), f"source file not found: {source_path}")
    expected_source_sha = admission_receipt["source"]["sha256"]
    actual_source_sha = sha256_file(source_path)
    require(actual_source_sha == expected_source_sha, f"source SHA-256 mismatch: expected {expected_source_sha}, got {actual_source_sha}")

    expected_version = str(admission_receipt["source"]["detected_version"])
    media_type = str(preflight_receipt["source"]["media_type"])
    detected, identity = source_identity(source_path, media_type=media_type, expected_version=expected_version)

    require(detected["source_sha256"] == expected_source_sha, "detected source hash does not match admission source hash")
    require(detected["container"] == admission_receipt["source"]["container"], "container does not match admitted container")
    require(
        detected.get("package_manifest_sha256") == admission_receipt["source"].get("package_manifest_sha256"),
        "package-manifest identity does not match admission receipt",
    )

    route = admission_receipt["routing"]["route"]
    if expected_version == "1.2":
        require(route == admission.V12_ROUTE, "v1.2 source is not bound to the v1.2 profile route")
        require(detected["container"] == "ZIP", "v1.2 canonicalization requires the admitted ZIP package")
        require(admission_receipt["conformance"].get("profile_validation_performed") is True, "v1.2 admission did not perform required profile validation")
    elif expected_version == "1.3":
        require(route == admission.V13_ROUTE, "v1.3 source is not bound to the v1.3 XSD/master-data route")
        require(detected["container"] == "XML", "v1.3 canonicalization requires the admitted XML source")
        require(admission_receipt["conformance"].get("profile_validation_performed") is False, "v1.3 admission may not relabel v1.2 profile validation")
    else:
        raise CanonicalizationError(f"unsupported admitted ILCD+EPD version: {expected_version}")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridCanonicalEnvironmentalSourceIdentity",
        "id": f"rx-source:{expected_version}:{identity['process_dataset_uuid']}",
        "verdict": VERDICT,
        "certified": False,
        "impact_values_normalized": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "source": {
            "sha256": actual_source_sha,
            "package_manifest_sha256": detected.get("package_manifest_sha256"),
            "container": detected["container"],
            "media_type": media_type,
            "format_name": "ILCD+EPD",
            "format_version": expected_version,
        },
        "identity": identity,
        "authority": {
            "decision": admission_receipt["rights"]["decision"],
            "status": admission_receipt["rights"]["status"],
            "transformation": admission_receipt["rights"]["transformation"],
            "redistribution": admission_receipt["rights"]["redistribution"],
        },
        "routing": admission_receipt["routing"],
        "conformance": admission_receipt["conformance"],
        "admission": {
            "receipt_sha256": admission_receipt["receipt_sha256"],
            "preflight_receipt_sha256": preflight_receipt["receipt_sha256"],
        },
        "rxep_bridge": {
            "supporting_evidence_only": True,
            "review_state_elevation_permitted": False,
        },
        "evidence_dimensions": {
            "source_authority": "BOUND_FROM_ADMISSION",
            "source_integrity": "REVERIFIED",
            "format_or_profile_conformance": "BOUND_FROM_ADMISSION",
            "identity_normalization": "DETERMINISTIC_METADATA_ONLY",
            "impact_values": "NOT_NORMALIZED",
            "scientific_validity": "NOT_EVALUATED",
            "professional_review": "NOT_EVALUATED",
            "certification": "NOT_EVALUATED",
        },
        "limitations": [
            "This record normalizes deterministic source identity/provenance metadata only; environmental impact values are not normalized by v1.0.",
            "Admission/profile/schema conformance does not establish scientific validity, product representativeness, professional LCA suitability, programme-operator/BBSR approval, or certification.",
            "The normalized UUID/name metadata describes the admitted document identity and does not prove real-product or installed-material identity.",
            "This record is RXEP supporting evidence only and cannot automatically elevate RXEP review state.",
        ],
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION},
    }
    digest = sha256_bytes(canonical_json_bytes(record))
    record["integrity"]["content_sha256"] = digest
    validate_schema(record)
    return record


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_id": record["id"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "source_sha256": record["source"]["sha256"],
        "package_manifest_sha256": record["source"]["package_manifest_sha256"],
        "format_version": record["source"]["format_version"],
        "route": record["routing"]["route"],
        "admission_receipt_sha256": record["admission"]["receipt_sha256"],
        "preflight_receipt_sha256": record["admission"]["preflight_receipt_sha256"],
        "conformance_receipt_sha256": record["conformance"]["receipt_sha256"],
        "impact_values_normalized": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "rxep_review_state_elevation_permitted": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def normalize(
    source_path: Path,
    *,
    preflight_path: Path,
    conformance_path: Path,
    admission_path: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    preflight_receipt = load_json(preflight_path)
    conformance_receipt = load_json(conformance_path)
    admission_receipt = load_json(admission_path)
    record = build_record(source_path, preflight_receipt, conformance_receipt, admission_receipt)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "canonical-source-identity.json"
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt = build_receipt(record, record_bytes)
    receipt_path = output_dir / "canonicalization-receipt.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return record, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.0 admission-bound environmental source identity normalizer")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--conformance", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record, receipt = normalize(
            args.source,
            preflight_path=args.preflight,
            conformance_path=args.conformance,
            admission_path=args.admission,
            output_dir=args.output_dir,
        )
    except (CanonicalizationError, admission.AdmissionError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {receipt['verdict']}")
    print(f"SOURCE IDENTITY: {record['identity']['process_dataset_uuid']}")
    print(f"FORMAT: ILCD+EPD v{record['source']['format_version']}")
    print("IMPACT VALUES NORMALIZED: false")
    print("SCIENTIFIC VALIDATION: false")
    print("PROFESSIONAL REVIEW: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
