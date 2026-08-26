#!/usr/bin/env python3
"""ProofGrid v3.5 admission for externally acquired authoritative material evidence.

This layer does not decide IFC-to-environmental suitability and performs no
mapping or impact calculation. It verifies that an externally acquired source
record is internally consistent with the exact returned bytes and with the
bounded candidate-binding decision encoded in the v3.5 schema.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "external-material-specification-source-v35.schema.json"
VERDICT = "EXTERNAL_AUTHORITATIVE_MATERIAL_SPECIFICATION_ADMISSION_VERIFIABLE"
ENGINE_NAME = "RegenExcalibur ProofGrid External Material Specification Admission"
ENGINE_VERSION = "3.5.0"
ZERO = "0" * 64
CANON = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"


class ExternalMaterialSpecAdmissionError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExternalMaterialSpecAdmissionError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalMaterialSpecAdmissionError(f"invalid source record: {path}: {exc}") from exc
    require(isinstance(value, dict), "source record must be a JSON object")
    return value


def validate_schema(value: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ExternalMaterialSpecAdmissionError(f"invalid v3.5 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:8])
        raise ExternalMaterialSpecAdmissionError(f"source record failed v3.5 schema validation: {preview}")


def validate_source_record(source: dict[str, Any], content_bytes: bytes) -> None:
    validate_schema(source)

    acquisition = source["acquisition"]
    require(acquisition["content_bytes"] == len(content_bytes), "source byte-size mismatch")
    require(acquisition["content_sha256"] == sha256_bytes(content_bytes), "source SHA-256 mismatch")

    decision = source["decision"]
    candidate = source["candidate"]
    semantics = source["material_semantics"]
    boundaries = source["authority_boundaries"]

    # The exact v3.2 candidate is already enforced by schema constants.
    require(candidate["ifc_source_sha256"] == "19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb", "wrong IFC source")
    require(candidate["step_id"] == 9730, "wrong candidate STEP ID")
    require(candidate["global_id"] == "3BmeJtEDj3AQO77Os2w7Ny", "wrong candidate GlobalId")
    require(candidate["object_id"] == "2395272", "wrong candidate object ID")

    if decision == "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND":
        require(candidate["candidate_bound"] is True, "bound decision requires candidate_bound=true")
        require(candidate["binding_method"] != "UNBOUND", "bound decision requires explicit binding method")
        require(semantics["strength_class_explicit"] is True, "bound decision requires explicit strength class")
        require(isinstance(semantics["concrete_strength_class"], str), "bound decision requires concrete strength class")
        require(semantics["strength_class_source_text_sha256"] is not None, "bound decision requires exact source-text digest")
        require(semantics["explicit_absence_statement"] is False, "bound strength class conflicts with absence statement")

    elif decision == "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND":
        require(candidate["candidate_bound"] is False, "unbound decision requires candidate_bound=false")

    elif decision == "AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED":
        require(semantics["strength_class_explicit"] is False, "absence decision cannot contain explicit strength class")
        require(semantics["concrete_strength_class"] is None, "absence decision requires null strength class")
        require(semantics["explicit_absence_statement"] is True, "absence decision requires explicit absence statement")

    else:
        raise ExternalMaterialSpecAdmissionError(f"unsupported v3.5 decision: {decision}")

    for key in (
        "fuzzy_matching",
        "strength_class_inferred",
        "environmental_mapping_performed",
        "impact_calculation_performed",
        "scientific_suitability_confirmed",
        "professional_review_performed",
        "regulator_acceptance_implied",
        "certified",
    ):
        require(boundaries[key] is False, f"forbidden authority promotion: {key}")


def build_admission(source: dict[str, Any], content_bytes: bytes) -> dict[str, Any]:
    validate_source_record(source, content_bytes)

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridExternalMaterialSpecificationAdmission",
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "source": copy.deepcopy(source),
        "candidate_resolution_state": source["decision"],
        "source_fact_only": True,
        "environmental_source_equivalence_decided": False,
        "mapping_authorized": False,
        "environmental_mapping_performed": False,
        "impact_calculation_performed": False,
        "impact_calculation_permitted": False,
        "scientific_suitability_confirmed": False,
        "professional_review_performed": False,
        "regulator_acceptance_implied": False,
        "certified": False,
        "limitations": [
            "This admission verifies provenance and bounded candidate/material semantics only.",
            "A returned strength class is not automatically equivalent to the admitted environmental declaration.",
            "A separate reviewed suitability gate is required before any IFC-to-environmental mapping or impact calculation.",
        ],
        "integrity": {"content_sha256": ZERO, "canonicalization": CANON, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    return record


def build_receipt(record: dict[str, Any], raw: bytes) -> dict[str, Any]:
    source = record["source"]
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "decision": record["candidate_resolution_state"],
        "source_content_sha256": source["acquisition"]["content_sha256"],
        "source_content_bytes": source["acquisition"]["content_bytes"],
        "candidate_global_id": source["candidate"]["global_id"],
        "candidate_object_id": source["candidate"]["object_id"],
        "candidate_bound": source["candidate"]["candidate_bound"],
        "concrete_strength_class": source["material_semantics"]["concrete_strength_class"],
        "explicit_absence_statement": source["material_semantics"]["explicit_absence_statement"],
        "mapping_authorized": False,
        "impact_calculation_permitted": False,
        "scientific_suitability_confirmed": False,
        "certified": False,
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(raw),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-record", type=Path, required=True)
    parser.add_argument("--content-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        source = load_json(args.source_record)
        content_bytes = args.content_file.read_bytes()
        record = build_admission(source, content_bytes)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "external-material-specification-admission.json"
        receipt_path = args.output_dir / "external-material-specification-admission-receipt.json"
        raw = pretty_json_bytes(record)
        record_path.write_bytes(raw)
        receipt_path.write_bytes(pretty_json_bytes(build_receipt(record, raw)))
    except (OSError, ExternalMaterialSpecAdmissionError) as exc:
        print(f"FAILED: {exc}")
        return 2

    print(f"RESULT: {VERDICT}")
    print(f"DECISION: {record['candidate_resolution_state']}")
    print("MAPPING_AUTHORIZED=false")
    print("IMPACT_CALCULATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
