#!/usr/bin/env python3
"""ProofGrid v1.7 RXEP binder for one exact-Decimal calculated contribution.

The generic RXEP envelope remains backward compatible with legacy numeric
measurements. This profile adds exact Decimal authority and binds the accepted
v1.6 calculation plus v1.6.1 independent software-reproduction evidence while
keeping the environmental evidence state exactly CALCULATED.
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
ENGINE_NAME = "RegenExcalibur ProofGrid RXEP Exact-Decimal Contribution Binder"
ENGINE_VERSION = "1.7.0"
VERDICT = "RXEP_EXACT_DECIMAL_CALCULATION_EVIDENCE_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

EXPECTED_V16 = {
    "head": "99876aadeef1b17bdf4a8a739df1c830fb80b9d3",
    "record_content": "1eff779368d48de3a9c637d0a9298788487c67480d6134c18302af1bacf7848e",
    "record_file": "69921546aa24dd6e0e950964aa3e9bc8bd962f14ab6855f868a5fa8ed639e8d7",
    "receipt": "486c4a9e133bf88ec563215649acdf991c4806a31751ddd6895acbac86615af8",
    "receipt_file": "a21dbe86fce8eb707fc09b57f5638b8d8d1bcb99ae8712fb16fae2d2f894e69f",
    "value_decimal": "15559.479677163699",
    "unit": "kg CO2 eqv.",
}
EXPECTED_V161 = {
    "head": "feba840febeb3181d42414dc951011729b880c2d",
    "receipt": "53d81a57337697daea3a29b2b43a784289cdad98603cea9dd7717f02c654e24c",
    "receipt_file": "729021f7accf74e8389f4d43f9b8b13d8501f5bab795fa9f43d1f330da4a0529",
}


class RXEPContributionError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RXEPContributionError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise RXEPContributionError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RXEPContributionError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def validate_rxep(envelope: dict[str, Any]) -> None:
    schema = json.loads(RXEP_SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RXEPContributionError(f"invalid RXEP schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(envelope), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6])
        raise RXEPContributionError(f"RXEP envelope failed schema validation: {preview}")


def canonical_decimal(value: Any, label: str) -> str:
    require(isinstance(value, str) and value, f"{label} must be a non-empty Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise RXEPContributionError(f"{label} is not Decimal-compatible") from exc
    require(number.is_finite(), f"{label} must be finite")
    if number == 0:
        rendered = "0"
    else:
        rendered = format(number, "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
    require(rendered == value, f"{label} is not canonical Decimal")
    return value


def verify_self_hash(record: dict[str, Any], label: str) -> str:
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), f"{label} missing integrity")
    claimed = integrity.get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing content SHA-256")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, f"{label} content digest mismatch")
    return claimed


def verify_receipt_digest(receipt: dict[str, Any], label: str) -> str:
    claimed = receipt.get("receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing receipt SHA-256")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, f"{label} digest mismatch")
    return claimed


def verify_parents(v16: dict[str, Any], v16_raw: bytes, v16_receipt: dict[str, Any], v16_receipt_raw: bytes, v161: dict[str, Any], v161_raw: bytes) -> None:
    require(v16.get("verdict") == "MAPPED_DECLARED_RESULT_SCALED_VERIFIABLE", "wrong v1.6 result verdict")
    content = verify_self_hash(v16, "v1.6 result")
    require(content == EXPECTED_V16["record_content"], "unaccepted v1.6 result content")
    require(sha256_bytes(v16_raw) == EXPECTED_V16["record_file"], "unaccepted v1.6 result file")
    receipt_sha = verify_receipt_digest(v16_receipt, "v1.6 calculation receipt")
    require(receipt_sha == EXPECTED_V16["receipt"], "unaccepted v1.6 calculation receipt")
    require(sha256_bytes(v16_receipt_raw) == EXPECTED_V16["receipt_file"], "unaccepted v1.6 calculation receipt file")
    require(v16_receipt.get("record_content_sha256") == content, "v1.6 receipt/result content mismatch")
    require(v16_receipt.get("record_file_sha256") == EXPECTED_V16["record_file"], "v1.6 receipt/result file mismatch")
    calc = v16.get("calculation", {})
    require(canonical_decimal(calc.get("scaled_result_decimal"), "v1.6 scaled result") == EXPECTED_V16["value_decimal"], "v1.6 exact Decimal differs from accepted result")
    require(calc.get("scaled_result_unit") == EXPECTED_V16["unit"], "v1.6 result unit mismatch")
    require(calc.get("mapped_quantity", {}).get("source_token_is_authority") is True, "v1.6 source quantity authority lost")
    require(calc.get("mapped_quantity", {}).get("parser_numeric_value_is_authority") is False, "v1.6 parser float authority promotion rejected")
    for key in ("aggregation_performed", "missing_modules_are_zero", "unit_conversion_performed", "scenario_inference_performed", "fuzzy_mapping_performed", "scientific_validation_performed", "professional_review_performed", "certified"):
        require(v16.get(key) is False, f"v1.6 {key} promotion rejected")

    require(v161.get("verdict") == "MAPPED_DECLARED_RESULT_SCALED_INDEPENDENTLY_REPRODUCED", "wrong v1.6.1 comparison verdict")
    comparison_sha = verify_receipt_digest(v161, "v1.6.1 comparison receipt")
    require(comparison_sha == EXPECTED_V161["receipt"], "unaccepted v1.6.1 comparison receipt")
    require(sha256_bytes(v161_raw) == EXPECTED_V161["receipt_file"], "unaccepted v1.6.1 comparison receipt file")
    require(v161.get("accepted_v16_head") == EXPECTED_V16["head"], "v1.6.1 accepted-head mismatch")
    require(v161.get("independent_runner_count") == 2 and v161.get("byte_identical") is True, "v1.6.1 independent reproduction not proven")
    require(v161.get("record_content_sha256") == EXPECTED_V16["record_content"], "v1.6.1 record-content mismatch")
    require(v161.get("record_file_sha256") == EXPECTED_V16["record_file"], "v1.6.1 record-file mismatch")
    require(v161.get("calculation_receipt_sha256") == EXPECTED_V16["receipt"], "v1.6.1 receipt mismatch")
    require(v161.get("scaled_result_decimal") == EXPECTED_V16["value_decimal"], "v1.6.1 result mismatch")
    require(v161.get("certified") is False, "v1.6.1 certification promotion rejected")


def verify_profile(envelope: dict[str, Any]) -> None:
    validate_rxep(envelope)
    require(envelope.get("review", {}).get("state") == "CALCULATED", "v1.7 RXEP review state must remain CALCULATED")
    require(envelope.get("review", {}).get("reviewer") is None, "v1.7 must not invent a reviewer")
    measurement = envelope.get("measurement", {})
    require(measurement.get("value_decimal") == EXPECTED_V16["value_decimal"], "v1.7 exact Decimal measurement mismatch")
    require(measurement.get("decimal_value_is_authority") is True, "v1.7 Decimal value must be authority")
    require(measurement.get("numeric_value_is_authority") is False, "v1.7 generic numeric value cannot be authority")
    require(measurement.get("unit") == EXPECTED_V16["unit"], "v1.7 unit mismatch")
    require(envelope.get("certified") is False, "v1.7 certification promotion rejected")
    require(envelope.get("scientific_validation_performed") is False, "v1.7 scientific-validation promotion rejected")
    require(envelope.get("professional_review_performed") is False, "v1.7 professional-review promotion rejected")
    require(envelope.get("aggregation_performed") is False, "v1.7 aggregation promotion rejected")


def build_envelope(v16: dict[str, Any], v16_raw: bytes, v16_receipt: dict[str, Any], v16_receipt_raw: bytes, v161: dict[str, Any], v161_raw: bytes) -> dict[str, Any]:
    verify_parents(v16, v16_raw, v16_receipt, v16_receipt_raw, v161, v161_raw)
    calc = v16["calculation"]
    selection = v16["selection"]
    exact = Decimal(calc["scaled_result_decimal"])
    display_value = float(exact)
    envelope: dict[str, Any] = {
        "id": f"rxep:v17:{v16['integrity']['content_sha256']}",
        "subject": {
            "id": v16["inputs"]["element_global_id"],
            "type": "ifc-declaration-environmental-contribution",
            "name": "Exact mapped IFC declared environmental contribution",
        },
        "claim": {
            "type": "scaled_declared_environmental_contribution",
            "statement": "One exact mapped IFC quantity was scaled against one exact declaration reference basis and one explicitly selected source-declared environmental result row.",
        },
        "measurement": {
            "value": display_value,
            "value_decimal": calc["scaled_result_decimal"],
            "decimal_value_is_authority": True,
            "numeric_value_is_authority": False,
            "numeric_value_role": "NON_AUTHORITATIVE_DISPLAY",
            "unit": calc["scaled_result_unit"],
            "indicator_code": selection["indicator_code"],
            "indicator_uuid": selection["indicator_uuid"],
            "module": selection["module"],
            "scenario": copy.deepcopy(selection["scenario"]),
        },
        "methodology": {
            "name": calc["method"],
            "version": calc["version"],
            "formula": calc["formula"],
            "calculation_scope": v16["calculation_scope"],
        },
        "sources": [
            {"path": "accepted-v1.6/mapped-declared-result-calculation.json", "sha256": EXPECTED_V16["record_file"], "kind": "calculation-record", "content_sha256": EXPECTED_V16["record_content"]},
            {"path": "accepted-v1.6/mapped-declared-result-calculation-receipt.json", "sha256": EXPECTED_V16["receipt_file"], "kind": "calculation-receipt", "receipt_sha256": EXPECTED_V16["receipt"]},
            {"path": "accepted-v1.6.1/v161-independent-comparison-receipt.json", "sha256": EXPECTED_V161["receipt_file"], "kind": "software-reproduction-receipt", "receipt_sha256": EXPECTED_V161["receipt"]},
        ],
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": "UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": [
            "Independent reproduction applies to the software calculation and canonical bytes; it does not promote the environmental claim to independently verified.",
            "The generic numeric measurement value is a non-authoritative interoperability/display representation; value_decimal is the exact evidence authority.",
            "This envelope describes one mapped declared contribution only, not a complete building LCA.",
            "No aggregation, unit conversion, scientific validation, professional review, regulatory approval, or certification is performed.",
        ],
        "aggregation_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "software_reproduction": {"independent_runner_count": 2, "byte_identical": True, "comparison_receipt_sha256": EXPECTED_V161["receipt"]},
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    verify_profile(envelope)
    return envelope


def write_outputs(envelope: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    envelope_path = output_dir / "rxep-exact-decimal-calculated-contribution.json"
    receipt_path = output_dir / "rxep-exact-decimal-calculated-contribution-receipt.json"
    envelope_bytes = pretty_json_bytes(envelope)
    envelope_path.write_bytes(envelope_bytes)
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "review_state": "CALCULATED",
        "record_content_sha256": envelope["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(envelope_bytes),
        "value_decimal": envelope["measurement"]["value_decimal"],
        "unit": envelope["measurement"]["unit"],
        "decimal_value_is_authority": True,
        "numeric_value_is_authority": False,
        "accepted_v16_head": EXPECTED_V16["head"],
        "v16_record_content_sha256": EXPECTED_V16["record_content"],
        "v16_calculation_receipt_sha256": EXPECTED_V16["receipt"],
        "accepted_v161_head": EXPECTED_V161["head"],
        "v161_comparison_receipt_sha256": EXPECTED_V161["receipt"],
        "software_reproduction_verified": True,
        "environmental_claim_independently_verified": False,
        "aggregation_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    receipt_bytes = pretty_json_bytes(receipt)
    receipt_path.write_bytes(receipt_bytes)
    return {
        "record": str(envelope_path),
        "receipt": str(receipt_path),
        "record_file_sha256": sha256_bytes(envelope_bytes),
        "receipt_file_sha256": sha256_bytes(receipt_bytes),
        "receipt_sha256": receipt["receipt_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--v16-record", type=Path, required=True)
    p.add_argument("--v16-receipt", type=Path, required=True)
    p.add_argument("--v161-comparison", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        v16, v16_raw = load_json(args.v16_record)
        v16_receipt, v16_receipt_raw = load_json(args.v16_receipt)
        v161, v161_raw = load_json(args.v161_comparison)
        envelope = build_envelope(v16, v16_raw, v16_receipt, v16_receipt_raw, v161, v161_raw)
        outputs = write_outputs(envelope, args.output_dir)
    except RXEPContributionError as exc:
        print(f"FAILED: {exc}")
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"REVIEW_STATE={envelope['review']['state']}")
    print(f"VALUE_DECIMAL={envelope['measurement']['value_decimal']}")
    print(f"DISPLAY_VALUE={envelope['measurement']['value']}")
    print(f"RECORD_SHA256={outputs['record_file_sha256']}")
    print(f"RECEIPT_SHA256={outputs['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
