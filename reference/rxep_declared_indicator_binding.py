#!/usr/bin/env python3
"""ProofGrid v1.2 exact-decimal RXEP binder for declared indicators.

The binder converts a verified ProofGrid v1.1 declared-indicator extraction
record into RX Evidence Protocol v0.2 envelopes. Each envelope asserts only that
the exact admitted source *declares* the retained value for the retained
module/scenario identity.

No calculation, unit conversion, scientific validation, professional review,
regulatory applicability, signature, or certification is added by this layer.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, RefResolver, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declared_environmental_indicators as declared  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid RXEP Declared Indicator Binder"
ENGINE_VERSION = "1.2.0"
PROTOCOL_VERSION = "0.2"
VERDICT = "RXEP_DECLARED_INDICATOR_EVIDENCE_BOUND_VERIFIABLE"
REVIEW_STATE = "CLAIMED"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

ENVELOPE_SCHEMA_PATH = ROOT / "specs" / "rxep" / "v0.2" / "evidence-envelope.schema.json"
BUNDLE_SCHEMA_PATH = ROOT / "schemas" / "rxep-v02-declared-indicator-bundle.schema.json"


class BindingError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BindingError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise BindingError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BindingError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected a JSON object in {path}")
    return value, raw


def validate_envelope(instance: dict[str, Any]) -> None:
    schema, _ = load_json_bytes(ENVELOPE_SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise BindingError(f"invalid RXEP v0.2 envelope schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise BindingError(f"RXEP v0.2 envelope schema validation failed: {preview}")


def validate_bundle(instance: dict[str, Any]) -> None:
    schema, _ = load_json_bytes(BUNDLE_SCHEMA_PATH)
    envelope_schema, _ = load_json_bytes(ENVELOPE_SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise BindingError(f"invalid RXEP v0.2 bundle schema: {exc.message}") from exc
    resolver = RefResolver.from_schema(
        schema,
        store={envelope_schema["$id"]: envelope_schema},
    )
    errors = sorted(
        Draft202012Validator(schema, resolver=resolver).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise BindingError(f"RXEP v0.2 bundle schema validation failed: {preview}")


def verify_record_integrity(record: dict[str, Any]) -> None:
    try:
        declared.validate_schema(record)
    except Exception as exc:
        raise BindingError(f"v1.1 extraction record schema validation failed: {exc}") from exc

    require(record.get("verdict") == declared.VERDICT, "wrong v1.1 extraction verdict")
    require(record.get("calculated") is False, "v1.1 extraction record must remain calculated=false")
    require(record.get("unit_conversion_performed") is False, "v1.1 extraction record must remain unit_conversion_performed=false")
    require(record.get("scientific_validation_performed") is False, "v1.1 extraction record may not claim scientific validation")
    require(record.get("professional_review_performed") is False, "v1.1 extraction record may not claim professional review")
    require(record.get("certified") is False, "v1.1 extraction record must remain certified=false")
    require(record.get("missing_value_policy", {}).get("missing_modules_are_zero") is False, "v1.1 record may not treat missing modules as zero")
    require(record.get("missing_value_policy", {}).get("aggregation_performed") is False, "v1.1 record may not aggregate lifecycle modules")

    expected = record.get("integrity", {}).get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, "v1.1 extraction record integrity digest missing")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = declared.ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"v1.1 extraction record integrity mismatch: expected {expected}, got {actual}")


def verify_receipt_integrity(receipt: dict[str, Any]) -> None:
    expected = receipt.get("receipt_sha256")
    require(isinstance(expected, str) and len(expected) == 64, "v1.1 extraction receipt digest missing")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"v1.1 extraction receipt integrity mismatch: expected {expected}, got {actual}")
    require(receipt.get("verdict") == declared.VERDICT, "wrong v1.1 extraction receipt verdict")
    require(receipt.get("certified") is False, "v1.1 extraction receipt must remain certified=false")
    require(receipt.get("calculated") is False, "v1.1 extraction receipt must remain calculated=false")
    require(receipt.get("unit_conversion_performed") is False, "v1.1 extraction receipt must remain unit_conversion_performed=false")
    require(receipt.get("scientific_validation_performed") is False, "v1.1 extraction receipt may not claim scientific validation")
    require(receipt.get("professional_review_performed") is False, "v1.1 extraction receipt may not claim professional review")
    require(receipt.get("certified_state") == "NOT_EVALUATED", "v1.1 extraction receipt certification state must remain NOT_EVALUATED")


def verify_parent_bindings(
    record: dict[str, Any],
    record_bytes: bytes,
    receipt: dict[str, Any],
) -> None:
    verify_record_integrity(record)
    verify_receipt_integrity(receipt)

    require(receipt.get("record_file_sha256") == sha256_bytes(record_bytes), "v1.1 extraction receipt record-file hash mismatch")
    require(receipt.get("record_content_sha256") == record["integrity"]["content_sha256"], "v1.1 receipt/record content-hash mismatch")
    require(receipt.get("source_sha256") == record["source"]["sha256"], "v1.1 receipt/source hash mismatch")
    require(receipt.get("process_xml_sha256") == record["source"]["process_xml_sha256"], "v1.1 receipt/process XML hash mismatch")
    require(receipt.get("process_dataset_uuid") == record["source"]["process_dataset_uuid"], "v1.1 receipt/process UUID mismatch")
    require(receipt.get("format_version") == record["source"]["format_version"], "v1.1 receipt/format-version mismatch")
    require(receipt.get("canonical_source_content_sha256") == record["canonical_source"]["content_sha256"], "v1.1 receipt/canonical-source hash mismatch")
    require(receipt.get("admission_receipt_sha256") == record["canonical_source"]["admission_receipt_sha256"], "v1.1 receipt/admission hash mismatch")
    require(receipt.get("frozen_map_sha256") == record["frozen_map"]["sha256"], "v1.1 receipt/frozen-map hash mismatch")
    require(receipt.get("research_freeze_receipt_sha256") == record["frozen_map"]["research_freeze_receipt_sha256"], "v1.1 receipt/research-freeze hash mismatch")
    require(receipt.get("indicator_uuid") == record["indicator_scope"]["indicator_uuid"], "v1.1 receipt/indicator UUID mismatch")
    require(receipt.get("indicator_code") == record["indicator_scope"]["code"], "v1.1 receipt/indicator code mismatch")
    require(receipt.get("row_count") == len(record["rows"]), "v1.1 receipt/row-count mismatch")


def scenario_name(row: dict[str, Any]) -> str | None:
    scenario = row.get("scenario")
    if scenario is None:
        return None
    require(isinstance(scenario, dict), "v1.1 row scenario must be an object or null")
    name = scenario.get("name")
    require(isinstance(name, str) and bool(name.strip()), "v1.1 row scenario name is missing")
    return name.strip()


def verify_rows(record: dict[str, Any]) -> None:
    scope = record["indicator_scope"]
    rows = record.get("rows")
    require(isinstance(rows, list) and bool(rows), "v1.1 extraction record has no rows")
    seen: set[tuple[str, str, str | None]] = set()
    for row in rows:
        require(row.get("indicator_uuid") == scope["indicator_uuid"], "v1.1 row indicator UUID differs from record scope")
        require(row.get("canonical_unit") == scope["canonical_unit"], "v1.1 row unit differs from record scope")
        require(row.get("unit_group_uuid") == scope["unit_group_uuid"], "v1.1 row unit-group UUID differs from record scope")
        require(row.get("value_origin") == "DECLARED_IN_SOURCE", "v1.1 row is not source-declared")
        require(row.get("calculated") is False, "v1.1 row must remain calculated=false")
        require(row.get("unit_conversion_performed") is False, "v1.1 row must remain unit_conversion_performed=false")
        module = row.get("module")
        require(isinstance(module, str) and bool(module.strip()), "v1.1 row lifecycle module is missing")
        scenario = scenario_name(row)
        key = (scope["indicator_uuid"], module, scenario)
        require(key not in seen, f"duplicate v1.1 row identity: {key}")
        seen.add(key)
        lexical = row.get("value_lexical")
        decimal_value = row.get("value_decimal")
        require(isinstance(lexical, str) and bool(lexical), "v1.1 row lexical value is missing")
        require(isinstance(decimal_value, str) and bool(decimal_value), "v1.1 row Decimal value is missing")
        canonical = declared.canonical_decimal(lexical)
        require(canonical == decimal_value, f"v1.1 lexical/Decimal mismatch: lexical={lexical!r}, expected={canonical!r}, got={decimal_value!r}")


def parent_material(
    record_path: Path,
    receipt_path: Path,
) -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    record, record_bytes = load_json_bytes(record_path)
    receipt, receipt_bytes = load_json_bytes(receipt_path)
    verify_parent_bindings(record, record_bytes, receipt)
    verify_rows(record)
    return record, record_bytes, receipt, receipt_bytes


def claim_statement(record: dict[str, Any], row: dict[str, Any]) -> str:
    scenario = scenario_name(row)
    scenario_text = f"scenario {scenario}" if scenario else "no scenario"
    return (
        f"The exact admitted ILCD+EPD source declares {record['indicator_scope']['code']} = "
        f"{row['value_decimal']} {row['canonical_unit']} for lifecycle module {row['module']} and {scenario_text}."
    )


def envelope_id(record: dict[str, Any], row: dict[str, Any]) -> str:
    identity = {
        "protocol_version": PROTOCOL_VERSION,
        "source_sha256": record["source"]["sha256"],
        "process_dataset_uuid": record["source"]["process_dataset_uuid"],
        "indicator_uuid": row["indicator_uuid"],
        "module": row["module"],
        "scenario": scenario_name(row),
    }
    return f"rxep:0.2:declared:{sha256_bytes(canonical_json_bytes(identity))}"


def build_envelope(
    record: dict[str, Any],
    receipt: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    scenario = scenario_name(row)
    envelope: dict[str, Any] = {
        "protocol_version": PROTOCOL_VERSION,
        "id": envelope_id(record, row),
        "subject": {
            "id": record["source"]["process_dataset_uuid"],
            "type": "ILCD_PROCESS_DATASET",
            "source_format_version": record["source"]["format_version"],
        },
        "claim": {
            "type": "SOURCE_DECLARED_ENVIRONMENTAL_INDICATOR",
            "statement": claim_statement(record, row),
            "indicator_uuid": row["indicator_uuid"],
            "indicator_code": record["indicator_scope"]["code"],
            "module": row["module"],
            "scenario": scenario,
        },
        "measurement": {
            "value_lexical": row["value_lexical"],
            "value_decimal": row["value_decimal"],
            "unit": row["canonical_unit"],
            "unit_group_uuid": row["unit_group_uuid"],
            "value_origin": "DECLARED_IN_SOURCE",
            "calculated": False,
            "unit_conversion_performed": False,
        },
        "methodology": {
            "name": "ProofGrid Declared Environmental Indicator Extraction",
            "version": "1.1.0",
            "operation": "EXTRACTION_ONLY",
            "formula": None,
            "aggregation_performed": False,
        },
        "sources": [
            {
                "role": "V1_1_EXTRACTION_RECORD",
                "reference": f"v1.1-record:{record['integrity']['content_sha256']}",
                "sha256": receipt["record_file_sha256"],
            },
            {
                "role": "ADMITTED_SOURCE_BYTES",
                "reference": f"source:sha256:{record['source']['sha256']}",
                "sha256": record["source"]["sha256"],
            },
            {
                "role": "ILCD_PROCESS_XML",
                "reference": f"ilcd-process:{record['source']['process_dataset_uuid']}",
                "sha256": record["source"]["process_xml_sha256"],
            },
        ],
        "provenance": {
            "v1_1_extraction_receipt_sha256": receipt["receipt_sha256"],
            "v1_1_record_content_sha256": record["integrity"]["content_sha256"],
            "v1_1_record_file_sha256": receipt["record_file_sha256"],
            "canonical_source_content_sha256": record["canonical_source"]["content_sha256"],
            "admission_receipt_sha256": record["canonical_source"]["admission_receipt_sha256"],
            "research_freeze_receipt_sha256": record["frozen_map"]["research_freeze_receipt_sha256"],
            "frozen_map_sha256": record["frozen_map"]["sha256"],
            "source_location": row["source_location"],
        },
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": "SOURCE_DECLARATION_ONLY_NO_REGULATORY_APPLICABILITY_INFERRED",
        "review": {"state": REVIEW_STATE, "reviewer": None},
        "evidence_dimensions": {
            "source_authority": "BOUND_FROM_PARENT",
            "source_integrity": "BOUND_FROM_PARENT",
            "format_or_profile_conformance": "BOUND_FROM_PARENT",
            "identity_normalization": "BOUND_FROM_PARENT",
            "declared_value_extraction": "OBSERVED_IN_SOURCE",
            "scientific_validity": "NOT_EVALUATED",
            "professional_review": "NOT_EVALUATED",
            "certification": "NOT_EVALUATED",
        },
        "limitations": [
            "This RXEP envelope asserts only what the exact admitted source declares; it does not assert scientific correctness or real-product representativeness.",
            "No calculation, unit conversion, lifecycle-module aggregation, professional review, programme-operator/BBSR approval, regulatory applicability, or certification is added by this binding.",
            "RXEP review state is CLAIMED only; no reviewer or cryptographic signature is attached.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    validate_envelope(envelope)
    return envelope


def build_bundle(
    record: dict[str, Any],
    record_bytes: bytes,
    receipt: dict[str, Any],
    *,
    requested_review_state: str = REVIEW_STATE,
) -> dict[str, Any]:
    require(requested_review_state == REVIEW_STATE, f"automatic RXEP review-state elevation is prohibited: requested {requested_review_state}")
    verify_parent_bindings(record, record_bytes, receipt)
    verify_rows(record)
    envelopes = [build_envelope(record, receipt, row) for row in record["rows"]]
    ids = [envelope["id"] for envelope in envelopes]
    require(len(ids) == len(set(ids)), "duplicate deterministic RXEP envelope ID")

    bundle: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridRXEPDeclaredIndicatorEvidenceBundle",
        "verdict": VERDICT,
        "protocol_version": PROTOCOL_VERSION,
        "certified": False,
        "review_state": REVIEW_STATE,
        "signed": False,
        "parent": {
            "v1_1_verdict": record["verdict"],
            "extraction_receipt_sha256": receipt["receipt_sha256"],
            "record_content_sha256": record["integrity"]["content_sha256"],
            "record_file_sha256": receipt["record_file_sha256"],
            "source_sha256": record["source"]["sha256"],
            "process_xml_sha256": record["source"]["process_xml_sha256"],
            "process_dataset_uuid": record["source"]["process_dataset_uuid"],
            "format_version": record["source"]["format_version"],
            "canonical_source_content_sha256": record["canonical_source"]["content_sha256"],
            "admission_receipt_sha256": record["canonical_source"]["admission_receipt_sha256"],
        },
        "envelope_count": len(envelopes),
        "envelopes": envelopes,
        "limitations": [
            "This bundle is evidence of source-declared environmental values only; it is not an LCA conclusion, building-level result, professional review, regulatory approval, or certification.",
            "Every envelope remains review.state=CLAIMED and signature=null.",
            "Exact Decimal strings, parent hashes, and canonical JSON digests are the integrity authority; no binary floating-point value is used as evidence authority.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    bundle["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(bundle))
    validate_bundle(bundle)
    return bundle


def build_receipt(bundle: dict[str, Any], bundle_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "protocol_version": PROTOCOL_VERSION,
        "certified": False,
        "review_state": REVIEW_STATE,
        "signed": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "bundle_content_sha256": bundle["integrity"]["content_sha256"],
        "bundle_file_sha256": sha256_bytes(bundle_file_bytes),
        "envelope_count": bundle["envelope_count"],
        "envelope_content_sha256": [envelope["integrity"]["content_sha256"] for envelope in bundle["envelopes"]],
        "parent_extraction_receipt_sha256": bundle["parent"]["extraction_receipt_sha256"],
        "parent_record_content_sha256": bundle["parent"]["record_content_sha256"],
        "source_sha256": bundle["parent"]["source_sha256"],
        "process_dataset_uuid": bundle["parent"]["process_dataset_uuid"],
        "format_version": bundle["parent"]["format_version"],
        "limitations": list(bundle["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def bind(
    extraction_record_path: Path,
    *,
    extraction_receipt_path: Path,
    output_dir: Path,
    requested_review_state: str = REVIEW_STATE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    record, record_bytes, receipt, _ = parent_material(extraction_record_path, extraction_receipt_path)
    bundle = build_bundle(record, record_bytes, receipt, requested_review_state=requested_review_state)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "rxep-v02-declared-indicator-bundle.json"
    bundle_bytes = (json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    bundle_path.write_bytes(bundle_bytes)
    out_receipt = build_receipt(bundle, bundle_bytes)
    receipt_path = output_dir / "rxep-v02-binding-receipt.json"
    receipt_path.write_bytes((json.dumps(out_receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return bundle, out_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.2 exact-decimal RXEP binder")
    parser.add_argument("--extraction-record", type=Path, required=True)
    parser.add_argument("--extraction-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--review-state", default=REVIEW_STATE)
    args = parser.parse_args(argv)
    try:
        bundle, receipt = bind(
            args.extraction_record,
            extraction_receipt_path=args.extraction_receipt,
            output_dir=args.output_dir,
            requested_review_state=args.review_state,
        )
    except (BindingError, declared.ExtractionError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {receipt['verdict']}")
    print(f"PROTOCOL: RXEP v{receipt['protocol_version']}")
    print(f"ENVELOPES: {receipt['envelope_count']}")
    print("REVIEW STATE: CLAIMED")
    print("SIGNED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
