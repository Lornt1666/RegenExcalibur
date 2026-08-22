#!/usr/bin/env python3
"""ProofGrid v2.1 RXEP binder for the accepted v2.0 two-member PARTIAL set total.

This layer performs no new environmental arithmetic. It binds the exact accepted,
independently reproduced v2.0 Decimal total into RXEP while preserving PARTIAL
completeness and CALCULATED environmental-review state.
"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
RXEP_SCHEMA = ROOT / "specs" / "rxep" / "evidence-envelope.schema.json"
ENGINE_NAME = "RegenExcalibur ProofGrid RXEP Partial Set Exact Decimal Binder"
ENGINE_VERSION = "2.1.0"
VERDICT = "RXEP_PARTIAL_SET_EXACT_DECIMAL_TOTAL_EVIDENCE_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

EXPECTED_V20 = {
    "head": "2fc2c450b1f37cb2c355ff12d09622ad5f094eec",
    "artifact_id": 9464376763,
    "artifact_zip_sha256": "9b63ae70c4db86e2b01577bcc433471ad705a3aedcc590cf028fd874d95e677b",
    "record_content": "8b47dfb87f1be4e1979666f85f7da58c41c00e48c92b7cd4a2f3c9fdd62e8ed0",
    "record_file": "3e50fc30562b0611170b78baf1cf8b52a0cd39ba052f1398c7463a700ba9e6d8",
    "receipt": "991de0efd5c71c067391c8e5fa7bbf81fd55febb72a4cfe8cf5a10f09ac238d4",
    "receipt_file": "17ee6da67b9c549f6b53346fa49e4bf8d30d4d459a4f2c17566d286521cb8f2d",
    "comparison": "74f5ef72a9f1fdd6c8145bc3291e0bfbb9373c94cbf1b048822e291266b7f839",
    "value_decimal": "23339.2195157455485",
    "unit": "kg CO2 eqv.",
    "member_count": 2,
}
EXPECTED_COMPATIBILITY = {
    "indicator_code": "GWP-total",
    "indicator_uuid": "6a37f984-a4b3-458a-a20a-64418c145fa2",
    "module": "A1-A3",
    "scenario": None,
    "unit": "kg CO2 eqv.",
}


class RXEPPartialTotalError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RXEPPartialTotalError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RXEPPartialTotalError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RXEPPartialTotalError(f"invalid JSON in {path}: {exc}") from exc


def verify_canonical_receipt(receipt: dict[str, Any], field: str, label: str) -> str:
    claimed = receipt.get(field)
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing {field}")
    body = copy.deepcopy(receipt)
    body.pop(field, None)
    actual = sha256_bytes(canonical_json_bytes(body))
    require(actual == claimed, f"{label} canonical digest mismatch: expected {claimed}, got {actual}")
    return actual


def verify_record_integrity(record: dict[str, Any]) -> str:
    claimed = record.get("integrity", {}).get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "v2.0 aggregation record missing content hash")
    body = copy.deepcopy(record)
    body["integrity"]["content_sha256"] = ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(body))
    require(actual == claimed, f"v2.0 aggregation content digest mismatch: expected {claimed}, got {actual}")
    return actual


def canonical_decimal(value: str) -> Decimal:
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise RXEPPartialTotalError("v2.0 total_value_decimal is not a valid Decimal") from exc
    require(number.is_finite(), "v2.0 total_value_decimal must be finite")
    require(format(number, "f") == value, "v2.0 total_value_decimal is not canonical plain Decimal text")
    return number


def verify_parent(record_path: Path, receipt_path: Path, comparison_path: Path, *, expected: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected = EXPECTED_V20 if expected is None else expected
    record = load_json(record_path)
    receipt = load_json(receipt_path)
    comparison = load_json(comparison_path)
    require(sha256_file(record_path) == expected["record_file"], "wrong/tampered v2.0 aggregation record file")
    require(sha256_file(receipt_path) == expected["receipt_file"], "wrong/tampered v2.0 aggregation receipt file")
    content = verify_record_integrity(record)
    require(content == expected["record_content"], "v2.0 aggregation record content is not the accepted identity")
    verify_canonical_receipt(receipt, "receipt_sha256", "v2.0 aggregation receipt")
    require(receipt["receipt_sha256"] == expected["receipt"], "v2.0 aggregation receipt is not the accepted identity")
    verify_canonical_receipt(comparison, "comparison_receipt_sha256", "v2.0 comparison receipt")
    require(comparison["comparison_receipt_sha256"] == expected["comparison"], "v2.0 comparison receipt is not the accepted identity")
    require(record.get("verdict") == "PARTIAL_CONTRIBUTION_SET_EXACT_DECIMAL_TOTAL_VERIFIABLE", "wrong v2.0 record verdict")
    require(receipt.get("verdict") == record.get("verdict"), "v2.0 receipt verdict mismatch")
    require(comparison.get("verdict") == "PARTIAL_CONTRIBUTION_SET_EXACT_DECIMAL_TOTAL_INDEPENDENTLY_REPRODUCED", "wrong v2.0 comparison verdict")
    require(record.get("completeness_status") == "PARTIAL", "v2.0 parent completeness must remain PARTIAL")
    require(record.get("member_count") == expected["member_count"], "v2.0 parent member count mismatch")
    require(record.get("compatibility") == EXPECTED_COMPATIBILITY, "v2.0 compatibility tuple mismatch")
    require(record.get("aggregation", {}).get("total_value_decimal") == expected["value_decimal"], "v2.0 exact total mismatch")
    require(record.get("aggregation", {}).get("unit") == expected["unit"], "v2.0 unit mismatch")
    canonical_decimal(str(record["aggregation"]["total_value_decimal"]))
    require(receipt.get("record_content_sha256") == expected["record_content"], "v2.0 receipt/record binding mismatch")
    require(receipt.get("record_file_sha256") == expected["record_file"], "v2.0 receipt/file binding mismatch")
    require(receipt.get("total_value_decimal") == expected["value_decimal"], "v2.0 receipt Decimal mismatch")
    require(receipt.get("completeness_status") == "PARTIAL", "v2.0 receipt completeness promotion")
    require(comparison.get("byte_identical") is True, "v2.0 software reproduction was not byte-identical")
    require(comparison.get("independent_runner_count") == 2, "v2.0 comparison did not use two independent runners")
    require(comparison.get("record_content_sha256") == expected["record_content"], "v2.0 comparison/record binding mismatch")
    require(comparison.get("receipt_sha256") == expected["receipt"], "v2.0 comparison/receipt binding mismatch")
    require(comparison.get("total_value_decimal") == expected["value_decimal"], "v2.0 comparison Decimal mismatch")
    require(comparison.get("completeness_status") == "PARTIAL", "v2.0 comparison completeness promotion")
    for obj, label in ((record, "record"), (receipt, "receipt"), (comparison, "comparison")):
        require(obj.get("aggregation_performed") is True, f"v2.0 {label} lost aggregation_performed")
        require(obj.get("sum_performed") is True, f"v2.0 {label} lost sum_performed")
        require(obj.get("whole_building_lca_claimed") is False, f"v2.0 {label} promotes whole-building LCA")
        require(obj.get("declared_scope_complete_claimed") is False, f"v2.0 {label} promotes declared-scope completeness")
        require(obj.get("scientific_validation_performed") is False, f"v2.0 {label} promotes scientific validation")
        require(obj.get("professional_review_performed") is False, f"v2.0 {label} promotes professional review")
        require(obj.get("certified") is False, f"v2.0 {label} promotes certification")
    require(record.get("missing_contributions_are_zero") is False, "v2.0 record treats missing contributions as zero")
    require(record.get("missing_modules_are_zero") is False, "v2.0 record treats missing modules as zero")
    require(record.get("unit_conversion_performed") is False, "v2.0 record performs unit conversion")
    require(record.get("scenario_inference_performed") is False, "v2.0 record performs scenario inference")
    return record, receipt, comparison


def validate_rxep_schema(envelope: dict[str, Any]) -> None:
    schema = load_json(RXEP_SCHEMA)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RXEPPartialTotalError(f"invalid RXEP schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(envelope), key=lambda err: list(err.path))
    if errors:
        preview = "; ".join(f"{list(err.path)}: {err.message}" for err in errors[:5])
        raise RXEPPartialTotalError(f"RXEP envelope failed schema validation: {preview}")


def verify_profile(envelope: dict[str, Any]) -> None:
    validate_rxep_schema(envelope)
    require(envelope.get("verdict") == VERDICT, "wrong v2.1 RXEP verdict")
    require(envelope.get("review") == {"state": "CALCULATED", "reviewer": None}, "RXEP review state must remain CALCULATED with no reviewer")
    measurement = envelope.get("measurement", {})
    require(measurement.get("value_decimal") == EXPECTED_V20["value_decimal"], "RXEP exact Decimal total mismatch")
    canonical_decimal(str(measurement.get("value_decimal")))
    require(measurement.get("decimal_value_is_authority") is True, "RXEP Decimal authority flag must be true")
    require(measurement.get("numeric_value_is_authority") is False, "RXEP generic numeric display may not be authoritative")
    require(measurement.get("unit") == EXPECTED_V20["unit"], "RXEP unit mismatch")
    for key in ("indicator_code", "indicator_uuid", "module", "scenario"):
        require(measurement.get(key) == EXPECTED_COMPATIBILITY[key], f"RXEP measurement {key} mismatch")
    require(measurement.get("member_count") == 2, "RXEP member_count must remain 2")
    require(measurement.get("completeness_status") == "PARTIAL", "RXEP completeness must remain PARTIAL")
    require(measurement.get("aggregation_scope") == "ADMITTED_SET_MEMBERS_ONLY", "RXEP aggregation scope mismatch")
    require(envelope.get("aggregation_performed") is True, "RXEP must retain aggregation_performed=true")
    require(envelope.get("sum_performed") is True, "RXEP must retain sum_performed=true")
    require(envelope.get("completeness_status") == "PARTIAL", "RXEP completeness promotion rejected")
    require(envelope.get("whole_building_lca_claimed") is False, "RXEP whole-building LCA promotion rejected")
    require(envelope.get("declared_scope_complete_claimed") is False, "RXEP declared-scope-complete promotion rejected")
    require(envelope.get("missing_contributions_are_zero") is False, "RXEP missing-contribution zero inference rejected")
    require(envelope.get("missing_modules_are_zero") is False, "RXEP missing-module zero inference rejected")
    require(envelope.get("unit_conversion_performed") is False, "RXEP unit conversion promotion rejected")
    require(envelope.get("scenario_inference_performed") is False, "RXEP scenario inference promotion rejected")
    require(envelope.get("environmental_claim_independently_verified") is False, "software reproduction may not promote the environmental claim")
    require(envelope.get("scientific_validation_performed") is False, "RXEP scientific-validation promotion rejected")
    require(envelope.get("professional_review_performed") is False, "RXEP professional-review promotion rejected")
    require(envelope.get("certified") is False, "RXEP certification promotion rejected")
    repro = envelope.get("software_reproduction", {})
    require(repro.get("independent_runner_count") == 2 and repro.get("byte_identical") is True, "v2.0 software reproduction binding is incomplete")
    require(repro.get("comparison_receipt_sha256") == EXPECTED_V20["comparison"], "wrong v2.0 comparison receipt binding")
    claimed = envelope.get("integrity", {}).get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "RXEP content hash missing")
    body = copy.deepcopy(envelope)
    body["integrity"]["content_sha256"] = ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(body))
    require(actual == claimed, f"RXEP content hash mismatch: expected {claimed}, got {actual}")


def build_envelope(record: dict[str, Any], receipt: dict[str, Any], comparison: dict[str, Any], comparison_file_sha256: str) -> dict[str, Any]:
    value_decimal = str(record["aggregation"]["total_value_decimal"])
    value = float(Decimal(value_decimal))
    envelope: dict[str, Any] = {
        "id": "rxep:proofgrid:v21:partial-set-total",
        "subject": {"id": record["source_set"]["scope_id"], "type": "environmental-contribution-set", "name": "ProofGrid accepted two-member PARTIAL contribution set"},
        "claim": {"type": "partial_contribution_set_exact_decimal_total", "statement": "The two exact admitted contribution members sum to the declared partial-set total; completeness remains PARTIAL."},
        "measurement": {"value": value, "value_decimal": value_decimal, "decimal_value_is_authority": True, "numeric_value_is_authority": False, "unit": record["aggregation"]["unit"], "indicator_code": record["compatibility"]["indicator_code"], "indicator_uuid": record["compatibility"]["indicator_uuid"], "module": record["compatibility"]["module"], "scenario": record["compatibility"]["scenario"], "member_count": record["member_count"], "completeness_status": record["completeness_status"], "aggregation_scope": record["aggregation"]["scope"]},
        "methodology": {"name": "bind_accepted_partial_set_exact_decimal_total", "version": ENGINE_VERSION, "formula": "sum(admitted member value_decimal strings using exact Decimal arithmetic); no missing-value inference", "parent_method": record["aggregation"]["method"], "parent_method_version": record["aggregation"]["version"]},
        "sources": [
            {"path": "v2.0/partial-contribution-set-exact-decimal-total.json", "sha256": EXPECTED_V20["record_file"], "kind": "accepted-v2.0-aggregation-record", "content_sha256": EXPECTED_V20["record_content"]},
            {"path": "v2.0/partial-contribution-set-exact-decimal-total-receipt.json", "sha256": EXPECTED_V20["receipt_file"], "kind": "accepted-v2.0-aggregation-receipt", "receipt_sha256": EXPECTED_V20["receipt"]},
            {"path": "v2.0/v20-independent-comparison-receipt.json", "sha256": comparison_file_sha256, "kind": "accepted-v2.0-independent-software-reproduction", "comparison_receipt_sha256": EXPECTED_V20["comparison"]},
        ],
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": "SYNTHETIC_TEST_ONLY",
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": ["This RXEP envelope represents the exact sum of two admitted members in a PARTIAL contribution set only.", "PARTIAL completeness is preserved; this is not a whole-building LCA or declared-scope-complete result.", "Independent software reproduction does not independently verify the environmental claim scientifically or professionally.", "Missing contributions/modules are not treated as zero; no unit conversion or scenario inference is performed.", "This evidence is not regulatory approval or certification."],
        "integrity": {"content_sha256": ZERO_DIGEST, "signature": None},
        "verdict": VERDICT,
        "aggregation_performed": True,
        "sum_performed": True,
        "completeness_status": "PARTIAL",
        "whole_building_lca_claimed": False,
        "declared_scope_complete_claimed": False,
        "missing_contributions_are_zero": False,
        "missing_modules_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "environmental_claim_independently_verified": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "parent_v20": {"accepted_head": EXPECTED_V20["head"], "artifact_id": EXPECTED_V20["artifact_id"], "artifact_zip_sha256": EXPECTED_V20["artifact_zip_sha256"], "record_content_sha256": record["integrity"]["content_sha256"], "receipt_sha256": receipt["receipt_sha256"]},
        "software_reproduction": {"verdict": comparison["verdict"], "independent_runner_count": comparison["independent_runner_count"], "byte_identical": comparison["byte_identical"], "comparison_receipt_sha256": comparison["comparison_receipt_sha256"]},
    }
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    verify_profile(envelope)
    return envelope


def build_receipt(envelope: dict[str, Any], envelope_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "review_state": "CALCULATED",
        "value_decimal": envelope["measurement"]["value_decimal"],
        "unit": envelope["measurement"]["unit"],
        "decimal_value_is_authority": True,
        "numeric_value_is_authority": False,
        "member_count": 2,
        "completeness_status": "PARTIAL",
        "aggregation_scope": "ADMITTED_SET_MEMBERS_ONLY",
        "rxep_record_content_sha256": envelope["integrity"]["content_sha256"],
        "rxep_record_file_sha256": sha256_bytes(envelope_file_bytes),
        "parent_v20_record_content_sha256": EXPECTED_V20["record_content"],
        "parent_v20_receipt_sha256": EXPECTED_V20["receipt"],
        "parent_v20_comparison_receipt_sha256": EXPECTED_V20["comparison"],
        "aggregation_performed": True,
        "sum_performed": True,
        "whole_building_lca_claimed": False,
        "declared_scope_complete_claimed": False,
        "environmental_claim_independently_verified": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def bind(record_path: Path, receipt_path: Path, comparison_path: Path, output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    record, receipt, comparison = verify_parent(record_path, receipt_path, comparison_path)
    envelope = build_envelope(record, receipt, comparison, sha256_file(comparison_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    envelope_path = output_dir / "rxep-partial-set-exact-decimal-total.json"
    envelope_bytes = pretty_json_bytes(envelope)
    envelope_path.write_bytes(envelope_bytes)
    out_receipt = build_receipt(envelope, envelope_bytes)
    (output_dir / "rxep-partial-set-exact-decimal-total-receipt.json").write_bytes(pretty_json_bytes(out_receipt))
    return envelope, out_receipt


def main() -> int:
    p = argparse.ArgumentParser(description="Bind accepted v2.0 PARTIAL exact-Decimal set total into RXEP CALCULATED evidence")
    p.add_argument("--v20-record", type=Path, required=True)
    p.add_argument("--v20-receipt", type=Path, required=True)
    p.add_argument("--v20-comparison", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    try:
        envelope, receipt = bind(args.v20_record, args.v20_receipt, args.v20_comparison, args.output_dir)
    except RXEPPartialTotalError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"REVIEW STATE: {envelope['review']['state']}")
    print(f"EXACT DECIMAL: {envelope['measurement']['value_decimal']} {envelope['measurement']['unit']}")
    print(f"COMPLETENESS: {envelope['completeness_status']}")
    print("WHOLE-BUILDING LCA: FALSE")
    print("NOT CERTIFIED")
    print(f"Receipt: {receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
