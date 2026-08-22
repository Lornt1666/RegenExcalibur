#!/usr/bin/env python3
"""ProofGrid v2.7 RXEP binder for the accepted third exact contribution.

This layer performs no environmental arithmetic, set admission, aggregation, or
completeness promotion. It binds the accepted v2.6 calculation/reproduction
bytes into one RXEP exact-Decimal CALCULATED evidence envelope.
"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
RXEP_SCHEMA = ROOT / "specs" / "rxep" / "evidence-envelope.schema.json"
ENGINE_NAME = "RegenExcalibur ProofGrid Third RXEP Exact-Decimal Binder"
ENGINE_VERSION = "2.7.0"
VERDICT = "THIRD_RXEP_EXACT_DECIMAL_CALCULATION_EVIDENCE_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

EXPECTED = {
    "head": "bca64726c75345841eca27ba3135ad8febdf429a",
    "record_content": "125b070fa9935b667cc23beb0c07a955be9b27d9c4d1412f94307c41306fbe56",
    "record_file": "6f26a7dea2bfaf424c390a39fe00ac0e572af26602cd455f6d77ccad180d9106",
    "receipt": "be67971767fb7210622b60cc4280bec1d00085a1108884e2fa185017bdec946e",
    "receipt_file": "8429c4b054710f6f9969c4145dc1b4bd8cbe16478d00a644e2c7419edb494128",
    "comparison": "5d87af95ff0782f71ef7e557562d8aaaa7e49c736135dfb8f8fcb970df1a7ba7",
    "comparison_file": "faa75ec8531f591cad7444186b37a6636a65669193a7e71791c596b23a057e98",
    "value_decimal": "3889.86991929092475",
    "unit": "kg CO2 eqv.",
    "element": "1DXL7DJx51bvggyIPU2Xi7",
    "source_sha": "ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d",
    "indicator_code": "GWP-total",
    "indicator_uuid": "6a37f984-a4b3-458a-a20a-64418c145fa2",
    "module": "A1-A3",
}

class ThirdRXEPError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ThirdRXEPError(message)

def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ThirdRXEPError(f"unable to load JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw

def verify_self_hash(record: dict[str, Any]) -> str:
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), "v2.6 record missing integrity")
    claimed = integrity.get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "v2.6 record missing content digest")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, "v2.6 record content digest mismatch")
    return claimed

def verify_receipt(receipt: dict[str, Any]) -> str:
    claimed = receipt.get("receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "v2.6 receipt missing digest")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, "v2.6 receipt digest mismatch")
    return claimed

def verify_comparison(receipt: dict[str, Any]) -> str:
    claimed = receipt.get("comparison_receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "v2.6 comparison missing digest")
    shadow = copy.deepcopy(receipt)
    shadow.pop("comparison_receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, "v2.6 comparison digest mismatch")
    return claimed

def canonical_decimal(value: Any) -> str:
    require(isinstance(value, str) and value, "exact result must be Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ThirdRXEPError("exact result is not Decimal-compatible") from exc
    require(number.is_finite(), "exact result must be finite")
    rendered = "0" if number == 0 else format(number, "f").rstrip("0").rstrip(".")
    require(rendered == value, "exact result is not canonical Decimal")
    return value

def validate_rxep(envelope: dict[str, Any]) -> None:
    schema = json.loads(RXEP_SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ThirdRXEPError(f"invalid RXEP schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(envelope), key=lambda e: list(e.path))
    if errors:
        raise ThirdRXEPError("RXEP schema validation failed: " + "; ".join(e.message for e in errors[:6]))

def verify_parents(record: dict[str, Any], record_raw: bytes, receipt: dict[str, Any], receipt_raw: bytes, comparison: dict[str, Any], comparison_raw: bytes) -> None:
    require(record.get("verdict") == "THIRD_MAPPED_DECLARED_RESULT_EXACT_DECIMAL_VERIFIABLE", "wrong v2.6 record verdict")
    content = verify_self_hash(record)
    require(content == EXPECTED["record_content"], "unaccepted v2.6 record content")
    require(sha256_bytes(record_raw) == EXPECTED["record_file"], "unaccepted v2.6 record file")
    receipt_sha = verify_receipt(receipt)
    require(receipt_sha == EXPECTED["receipt"], "unaccepted v2.6 receipt")
    require(sha256_bytes(receipt_raw) == EXPECTED["receipt_file"], "unaccepted v2.6 receipt file")
    require(receipt.get("record_content_sha256") == content, "v2.6 receipt/content mismatch")
    require(receipt.get("record_file_sha256") == EXPECTED["record_file"], "v2.6 receipt/file mismatch")
    comparison_sha = verify_comparison(comparison)
    require(comparison_sha == EXPECTED["comparison"], "unaccepted v2.6 comparison receipt")
    require(sha256_bytes(comparison_raw) == EXPECTED["comparison_file"], "unaccepted v2.6 comparison file")
    require(comparison.get("independent_runner_count") == 2 and comparison.get("byte_identical") is True, "v2.6 independent reproduction not proven")
    require(comparison.get("record_content_sha256") == EXPECTED["record_content"], "v2.6 comparison content mismatch")
    require(comparison.get("record_file_sha256") == EXPECTED["record_file"], "v2.6 comparison file mismatch")
    require(comparison.get("receipt_sha256") == EXPECTED["receipt"], "v2.6 comparison receipt mismatch")
    calc = record.get("calculation", {})
    require(canonical_decimal(calc.get("scaled_result_decimal")) == EXPECTED["value_decimal"], "v2.6 exact Decimal mismatch")
    require(calc.get("scaled_result_unit") == EXPECTED["unit"], "v2.6 unit mismatch")
    require(calc.get("mapped_quantity", {}).get("source_token_is_authority") is True, "STEP source token authority lost")
    require(calc.get("mapped_quantity", {}).get("parser_numeric_value_is_authority") is False, "parser float authority promotion rejected")
    require(record.get("inputs", {}).get("element_global_id") == EXPECTED["element"], "v2.6 element mismatch")
    require(record.get("inputs", {}).get("ifc_source_sha256") == EXPECTED["source_sha"], "v2.6 source SHA mismatch")
    selection = record.get("selection", {})
    require(selection.get("indicator_code") == EXPECTED["indicator_code"], "indicator mismatch")
    require(selection.get("indicator_uuid") == EXPECTED["indicator_uuid"], "indicator UUID mismatch")
    require(selection.get("module") == EXPECTED["module"], "module mismatch")
    require(selection.get("scenario") is None, "scenario mismatch")
    require(record.get("rxep_binding_performed") is False, "v2.6 already claims RXEP binding")
    require(record.get("contribution_set_admission_performed") is False, "v2.6 already claims set admission")
    require(record.get("aggregate_recomputed") is False, "v2.6 already claims aggregation")
    require(record.get("certified") is False and record.get("professional_review_performed") is False and record.get("scientific_validation_performed") is False, "v2.6 trust promotion rejected")

def build_envelope(record: dict[str, Any], record_raw: bytes, receipt: dict[str, Any], receipt_raw: bytes, comparison: dict[str, Any], comparison_raw: bytes) -> dict[str, Any]:
    verify_parents(record, record_raw, receipt, receipt_raw, comparison, comparison_raw)
    calc = record["calculation"]
    selection = record["selection"]
    exact = Decimal(EXPECTED["value_decimal"])
    envelope: dict[str, Any] = {
        "id": f"rxep:v27:{EXPECTED['record_content']}",
        "subject": {"id": EXPECTED["element"], "type": "ifc-declaration-environmental-contribution", "name": "Third exact mapped IFC declared environmental contribution"},
        "claim": {"type": "scaled_declared_environmental_contribution", "statement": "One accepted exact third IFC contribution is represented in RXEP without re-calculation, set admission, or aggregation."},
        "measurement": {
            "value": float(exact),
            "value_decimal": EXPECTED["value_decimal"],
            "decimal_value_is_authority": True,
            "numeric_value_is_authority": False,
            "numeric_value_role": "NON_AUTHORITATIVE_DISPLAY",
            "unit": EXPECTED["unit"],
            "indicator_code": EXPECTED["indicator_code"],
            "indicator_uuid": EXPECTED["indicator_uuid"],
            "module": EXPECTED["module"],
            "scenario": None,
        },
        "methodology": {"name": calc["method"], "version": "2.6.0", "formula": calc["formula"], "calculation_scope": record["calculation_scope"]},
        "sources": [
            {"path": "accepted-v2.6/third-mapped-declared-result-calculation.json", "sha256": EXPECTED["record_file"], "kind": "calculation-record", "content_sha256": EXPECTED["record_content"]},
            {"path": "accepted-v2.6/third-mapped-declared-result-calculation-receipt.json", "sha256": EXPECTED["receipt_file"], "kind": "calculation-receipt", "receipt_sha256": EXPECTED["receipt"]},
            {"path": "accepted-v2.6/v26-independent-comparison-receipt.json", "sha256": EXPECTED["comparison_file"], "kind": "software-reproduction-receipt", "receipt_sha256": EXPECTED["comparison"]},
        ],
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": "UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": [
            "Independent software reproduction does not promote the environmental claim to independently verified.",
            "measurement.value_decimal is exact authority; the generic JSON number is display/interoperability only.",
            "This envelope is not yet admitted into an environmental contribution set and no aggregate is recomputed.",
            "No whole-building completeness, scientific validation, professional review, regulatory approval, or certification is claimed.",
        ],
        "rxep_binding_performed": True,
        "contribution_set_admission_performed": False,
        "aggregate_recomputed": False,
        "environmental_coverage_status": "RXEP_BOUND_CONTRIBUTION_NOT_YET_SET_ADMITTED",
        "whole_building_completeness_evaluated": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "software_reproduction": {"independent_runner_count": 2, "byte_identical": True, "comparison_receipt_sha256": EXPECTED["comparison"]},
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    validate_profile(envelope)
    return envelope

def validate_profile(envelope: dict[str, Any]) -> None:
    validate_rxep(envelope)
    require(envelope.get("review", {}).get("state") == "CALCULATED" and envelope.get("review", {}).get("reviewer") is None, "review state promotion rejected")
    m = envelope.get("measurement", {})
    require(m.get("value_decimal") == EXPECTED["value_decimal"], "RXEP exact Decimal mismatch")
    require(m.get("decimal_value_is_authority") is True and m.get("numeric_value_is_authority") is False, "RXEP numeric authority mismatch")
    require(m.get("unit") == EXPECTED["unit"] and m.get("indicator_code") == EXPECTED["indicator_code"] and m.get("indicator_uuid") == EXPECTED["indicator_uuid"] and m.get("module") == EXPECTED["module"] and m.get("scenario") is None, "RXEP measurement identity mismatch")
    require(envelope.get("rxep_binding_performed") is True, "RXEP binding state missing")
    require(envelope.get("contribution_set_admission_performed") is False, "set-admission promotion rejected")
    require(envelope.get("aggregate_recomputed") is False, "aggregate promotion rejected")
    require(envelope.get("whole_building_completeness_evaluated") is False, "completeness promotion rejected")
    require(envelope.get("scientific_validation_performed") is False and envelope.get("professional_review_performed") is False and envelope.get("certified") is False, "trust promotion rejected")

def write_outputs(envelope: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "third-rxep-calculated-contribution.json"
    receipt_path = output_dir / "third-rxep-calculated-contribution-receipt.json"
    record_bytes = pretty_json_bytes(envelope)
    record_path.write_bytes(record_bytes)
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": envelope["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "value_decimal": EXPECTED["value_decimal"],
        "unit": EXPECTED["unit"],
        "element_global_id": EXPECTED["element"],
        "review_state": "CALCULATED",
        "rxep_binding_performed": True,
        "contribution_set_admission_performed": False,
        "aggregate_recomputed": False,
        "whole_building_completeness_evaluated": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    receipt_path.write_bytes(pretty_json_bytes(receipt))
    return receipt

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--comparison", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        record, record_raw = load_json(a.record)
        receipt, receipt_raw = load_json(a.receipt)
        comparison, comparison_raw = load_json(a.comparison)
        envelope = build_envelope(record, record_raw, receipt, receipt_raw, comparison, comparison_raw)
        write_outputs(envelope, a.output_dir)
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"EXACT DECIMAL: {EXPECTED['value_decimal']} {EXPECTED['unit']}")
    print("REVIEW STATE: CALCULATED")
    print("SET ADMISSION: false")
    print("AGGREGATE RECOMPUTED: false")
    print("NOT CERTIFIED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
