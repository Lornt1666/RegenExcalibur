#!/usr/bin/env python3
"""ProofGrid v1.8 contribution-set admission and anti-double-count gate.

Admits exact CALCULATED RXEP environmental contributions into one canonical
PARTIAL contribution set. This layer performs no summation or aggregation.

Each member binds both its RXEP envelope/receipt and the underlying mapped
calculation/receipt. The latter provides a semantic calculation-lineage key so
rewrapping the same contribution under a different member ID still fails.
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
REQUEST_SCHEMA = ROOT / "schemas" / "environmental-contribution-set-request.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "environmental-contribution-set.schema.json"
RXEP_SCHEMA = ROOT / "specs" / "rxep" / "evidence-envelope.schema.json"

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Contribution Set Admission"
ENGINE_VERSION = "1.8.0"
VERDICT = "ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64
RXEP_VERDICT = "RXEP_EXACT_DECIMAL_CALCULATION_EVIDENCE_VERIFIABLE"
CALC_VERDICT = "MAPPED_DECLARED_RESULT_SCALED_VERIFIABLE"


class ContributionSetError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContributionSetError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ContributionSetError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContributionSetError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def validate_schema(value: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ContributionSetError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6])
        raise ContributionSetError(f"{label} failed schema validation: {preview}")


def safe_member_file(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative, "member path must be non-empty")
    candidate = (root / relative).resolve()
    root = root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ContributionSetError(f"member path escapes request directory: {relative}") from exc
    require(candidate.is_file(), f"missing member file: {relative}")
    return candidate


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


def exact_scenario(value: Any) -> Any:
    if value is None:
        return None
    require(isinstance(value, dict), "scenario must be null or an object")
    return copy.deepcopy(value)


def source_entry(envelope: dict[str, Any], kind: str) -> dict[str, Any]:
    matches = [x for x in envelope.get("sources", []) if isinstance(x, dict) and x.get("kind") == kind]
    require(len(matches) == 1, f"RXEP envelope must contain exactly one {kind} source; found {len(matches)}")
    return matches[0]


def verify_rxep_member(record: dict[str, Any], raw: bytes, receipt: dict[str, Any], receipt_raw: bytes, expected: dict[str, Any]) -> None:
    validate_schema(record, RXEP_SCHEMA, "RXEP member")
    content = verify_self_hash(record, "RXEP member")
    require(content == expected["rxep_record_content_sha256"], "unaccepted RXEP member content")
    require(sha256_bytes(raw) == expected["rxep_record_file_sha256"], "unaccepted RXEP member file")
    receipt_sha = verify_receipt_digest(receipt, "RXEP member receipt")
    require(receipt_sha == expected["rxep_receipt_sha256"], "unaccepted RXEP member receipt")
    require(sha256_bytes(receipt_raw) == expected["rxep_receipt_file_sha256"], "unaccepted RXEP member receipt file")
    require(receipt.get("verdict") == RXEP_VERDICT, "wrong RXEP member receipt verdict")
    require(receipt.get("record_content_sha256") == content, "RXEP receipt/member content mismatch")
    require(receipt.get("record_file_sha256") == expected["rxep_record_file_sha256"], "RXEP receipt/member file mismatch")
    require(receipt.get("review_state") == "CALCULATED", "RXEP receipt review state must remain CALCULATED")
    require(receipt.get("certified") is False, "RXEP receipt certification promotion rejected")
    require(record.get("review") == {"state": "CALCULATED", "reviewer": None}, "RXEP member review state/reviewer must remain CALCULATED/null")
    measurement = record.get("measurement", {})
    require(measurement.get("decimal_value_is_authority") is True, "RXEP member Decimal authority missing")
    require(measurement.get("numeric_value_is_authority") is False, "RXEP member numeric authority promotion rejected")
    require(isinstance(measurement.get("value_decimal"), str) and measurement["value_decimal"], "RXEP member exact Decimal missing")
    for key in ("aggregation_performed", "scientific_validation_performed", "professional_review_performed", "certified"):
        require(record.get(key) is False, f"RXEP member {key} promotion rejected")


def verify_calculation_member(record: dict[str, Any], raw: bytes, receipt: dict[str, Any], receipt_raw: bytes, expected: dict[str, Any]) -> None:
    require(record.get("verdict") == CALC_VERDICT, "wrong calculation member verdict")
    content = verify_self_hash(record, "calculation member")
    require(content == expected["calculation_record_content_sha256"], "unaccepted calculation member content")
    require(sha256_bytes(raw) == expected["calculation_record_file_sha256"], "unaccepted calculation member file")
    receipt_sha = verify_receipt_digest(receipt, "calculation member receipt")
    require(receipt_sha == expected["calculation_receipt_sha256"], "unaccepted calculation member receipt")
    require(sha256_bytes(receipt_raw) == expected["calculation_receipt_file_sha256"], "unaccepted calculation member receipt file")
    require(receipt.get("verdict") == CALC_VERDICT, "wrong calculation receipt verdict")
    require(receipt.get("record_content_sha256") == content, "calculation receipt/record content mismatch")
    require(receipt.get("record_file_sha256") == expected["calculation_record_file_sha256"], "calculation receipt/record file mismatch")
    require(record.get("calculation_performed") is True, "calculation member is not calculated")
    require(record.get("calculation_scope") == "SINGLE_MAPPED_DECLARED_RESULT_ROW", "unsupported calculation scope")
    for key in ("aggregation_performed", "missing_modules_are_zero", "unit_conversion_performed", "scenario_inference_performed", "fuzzy_mapping_performed", "scientific_validation_performed", "professional_review_performed", "certified"):
        require(record.get(key) is False, f"calculation member {key} promotion rejected")


def semantic_identity(calc: dict[str, Any]) -> dict[str, Any]:
    inputs = calc.get("inputs", {})
    selection = calc.get("selection", {})
    calculation = calc.get("calculation", {})
    result = {
        "ifc_source_sha256": inputs.get("ifc_source_sha256"),
        "element_global_id": inputs.get("element_global_id"),
        "product_flow_uuid": inputs.get("product_flow_uuid"),
        "product_flow_version": inputs.get("product_flow_version"),
        "quantity_record_content_sha256": inputs.get("quantity_record_content_sha256"),
        "mapping_record_content_sha256": inputs.get("mapping_record_content_sha256"),
        "closure_record_content_sha256": inputs.get("closure_record_content_sha256"),
        "declaration_bundle_content_sha256": inputs.get("declaration_bundle_content_sha256"),
        "indicator_code": selection.get("indicator_code"),
        "indicator_uuid": selection.get("indicator_uuid"),
        "module": selection.get("module"),
        "scenario": exact_scenario(selection.get("scenario")),
        "value_decimal": calculation.get("scaled_result_decimal"),
        "unit": calculation.get("scaled_result_unit"),
    }
    for key, value in result.items():
        if key == "scenario":
            continue
        require(value is not None and value != "", f"calculation semantic identity missing {key}")
    return result


def bind_member(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    rxep_path = safe_member_file(root, spec["rxep_record_path"])
    rxep_receipt_path = safe_member_file(root, spec["rxep_receipt_path"])
    calc_path = safe_member_file(root, spec["calculation_record_path"])
    calc_receipt_path = safe_member_file(root, spec["calculation_receipt_path"])
    rxep, rxep_raw = load_json(rxep_path)
    rxep_receipt, rxep_receipt_raw = load_json(rxep_receipt_path)
    calc, calc_raw = load_json(calc_path)
    calc_receipt, calc_receipt_raw = load_json(calc_receipt_path)
    verify_rxep_member(rxep, rxep_raw, rxep_receipt, rxep_receipt_raw, spec)
    verify_calculation_member(calc, calc_raw, calc_receipt, calc_receipt_raw, spec)

    calc_source = source_entry(rxep, "calculation-record")
    calc_receipt_source = source_entry(rxep, "calculation-receipt")
    require(calc_source.get("content_sha256") == calc["integrity"]["content_sha256"], "RXEP/calculation content binding mismatch")
    require(calc_source.get("sha256") == sha256_bytes(calc_raw), "RXEP/calculation file binding mismatch")
    require(calc_receipt_source.get("receipt_sha256") == calc_receipt["receipt_sha256"], "RXEP/calculation receipt binding mismatch")
    require(calc_receipt_source.get("sha256") == sha256_bytes(calc_receipt_raw), "RXEP/calculation receipt file binding mismatch")
    require(rxep_receipt.get("v16_record_content_sha256") == calc["integrity"]["content_sha256"], "RXEP receipt/calculation content mismatch")
    require(rxep_receipt.get("v16_calculation_receipt_sha256") == calc_receipt["receipt_sha256"], "RXEP receipt/calculation receipt mismatch")

    identity = semantic_identity(calc)
    measurement = rxep["measurement"]
    require(rxep["subject"]["id"] == identity["element_global_id"], "RXEP/calculation element identity mismatch")
    require(measurement.get("indicator_code") == identity["indicator_code"], "RXEP/calculation indicator code mismatch")
    require(measurement.get("indicator_uuid") == identity["indicator_uuid"], "RXEP/calculation indicator UUID mismatch")
    require(measurement.get("module") == identity["module"], "RXEP/calculation module mismatch")
    require(exact_scenario(measurement.get("scenario")) == identity["scenario"], "RXEP/calculation scenario mismatch")
    require(measurement.get("unit") == identity["unit"], "RXEP/calculation unit mismatch")
    require(measurement.get("value_decimal") == identity["value_decimal"], "RXEP/calculation Decimal result mismatch")

    identity_sha = sha256_bytes(canonical_json_bytes(identity))
    return {
        "member_id": spec["member_id"],
        "rxep": {
            "record_content_sha256": rxep["integrity"]["content_sha256"],
            "record_file_sha256": sha256_bytes(rxep_raw),
            "receipt_sha256": rxep_receipt["receipt_sha256"],
            "receipt_file_sha256": sha256_bytes(rxep_receipt_raw),
            "review_state": rxep["review"]["state"],
        },
        "calculation": {
            "record_content_sha256": calc["integrity"]["content_sha256"],
            "record_file_sha256": sha256_bytes(calc_raw),
            "receipt_sha256": calc_receipt["receipt_sha256"],
            "receipt_file_sha256": sha256_bytes(calc_receipt_raw),
        },
        "semantic_identity": identity,
        "semantic_identity_sha256": identity_sha,
    }


def build_set(request_path: Path) -> dict[str, Any]:
    request_path = Path(request_path).resolve()
    request, request_raw = load_json(request_path)
    validate_schema(request, REQUEST_SCHEMA, "v1.8 contribution-set request")
    root = request_path.parent

    ids: set[str] = set()
    exact_records: set[str] = set()
    exact_receipts: set[str] = set()
    semantic_keys: set[str] = set()
    members: list[dict[str, Any]] = []
    for spec in request["members"]:
        member_id = spec["member_id"]
        require(member_id not in ids, f"duplicate member_id: {member_id}")
        ids.add(member_id)
        member = bind_member(root, spec)
        record_key = member["rxep"]["record_content_sha256"]
        receipt_key = member["rxep"]["receipt_sha256"]
        semantic_key = member["semantic_identity_sha256"]
        require(record_key not in exact_records, "duplicate RXEP record membership rejected")
        require(receipt_key not in exact_receipts, "duplicate RXEP receipt membership rejected")
        require(semantic_key not in semantic_keys, "semantic duplicate contribution membership rejected")
        exact_records.add(record_key)
        exact_receipts.add(receipt_key)
        semantic_keys.add(semantic_key)
        members.append(member)

    members.sort(key=lambda x: x["member_id"])
    compatibility = request["compatibility"]
    for member in members:
        identity = member["semantic_identity"]
        require(identity["indicator_code"] == compatibility["indicator_code"], "mixed indicator code rejected")
        require(identity["indicator_uuid"] == compatibility["indicator_uuid"], "mixed indicator UUID rejected")
        require(identity["unit"] == compatibility["unit"], "mixed environmental unit rejected")
        require(identity["module"] == compatibility["module"], "mixed module rejected")
        require(identity["scenario"] == exact_scenario(compatibility["scenario"]), "mixed/inferred scenario rejected")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridEnvironmentalContributionSet",
        "verdict": VERDICT,
        "set_id": request["set_id"],
        "scope_id": request["scope_id"],
        "completeness_status": "PARTIAL",
        "compatibility": copy.deepcopy(compatibility),
        "members": members,
        "member_count": len(members),
        "request_file_sha256": sha256_bytes(request_raw),
        "aggregation_performed": False,
        "sum_performed": False,
        "missing_contributions_are_zero": False,
        "missing_modules_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "duplicate_members_permitted": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This record admits contribution membership only; it does not sum or aggregate environmental contributions.",
            "completeness_status=PARTIAL is explicit; member count does not imply whole-building or declared-scope completeness.",
            "Missing contributions/modules are not treated as zero, and no unit conversion or scenario inference is performed.",
            "Membership integrity and compatibility do not establish scientific validity, professional review, regulatory approval, or certification."
        ],
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    validate_schema(record, RESULT_SCHEMA, "v1.8 contribution set")
    return record


def write_outputs(record: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "environmental-contribution-set.json"
    receipt_path = output_dir / "environmental-contribution-set-receipt.json"
    record_bytes = pretty_json_bytes(record)
    record_path.write_bytes(record_bytes)
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "set_id": record["set_id"],
        "scope_id": record["scope_id"],
        "completeness_status": record["completeness_status"],
        "member_count": record["member_count"],
        "member_semantic_identity_sha256": [m["semantic_identity_sha256"] for m in record["members"]],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "aggregation_performed": False,
        "sum_performed": False,
        "duplicate_members_permitted": False,
        "missing_contributions_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    receipt_path.write_bytes(pretty_json_bytes(receipt))
    return {
        "record": str(record_path),
        "receipt": str(receipt_path),
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": receipt["record_file_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.8 contribution-set admission")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = build_set(args.request)
        result = write_outputs(record, args.output_dir)
    except ContributionSetError as exc:
        print(f"FAILED: {exc}")
        return 2
    print("✓ exact RXEP member integrity")
    print("✓ exact calculation lineage integrity")
    print("✓ semantic duplicate prevention")
    print("✓ indicator/unit/module/scenario compatibility")
    print("✓ explicit PARTIAL completeness")
    print("RESULT: ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE")
    print("NO SUMMATION OR WHOLE-BUILDING LCA CLAIM")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
