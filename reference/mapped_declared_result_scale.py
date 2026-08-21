#!/usr/bin/env python3
"""ProofGrid v1.6 exact-decimal scaling of one mapped declared result row.

The engine verifies accepted v1.5 mapping evidence and v1.4 declaration evidence,
selects exactly one explicitly requested declared environmental row, and applies
one Decimal formula:

    (mapped IFC quantity / declaration reference quantity) * declared result

There is deliberately no aggregation path, no missing-module zeroing, no unit
conversion table, no scenario inference, and no fuzzy mapping path.
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declaration_evidence_bundle as v14  # noqa: E402
from reference import ifc_declaration_product_map as v15  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Mapped Declared Result Scaler"
ENGINE_VERSION = "1.6.0"
VERDICT = "MAPPED_DECLARED_RESULT_SCALED_VERIFIABLE"
SCOPE = "SINGLE_MAPPED_DECLARED_RESULT_ROW"
METHOD = "exact_decimal_reference_basis_scaling"
FORMULA = "(mapped_quantity / declaration_reference_quantity) * declared_environmental_result"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64
REQUEST_SCHEMA = ROOT / "schemas" / "mapped-declared-result-calculation-request.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "mapped-declared-result-calculation.schema.json"
V15_SCHEMA = ROOT / "schemas" / "ifc-declaration-product-mapping-result.schema.json"
V14_SCHEMA = ROOT / "schemas" / "declaration-evidence-bundle.schema.json"


class ScalingError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise ScalingError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScalingError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ScalingError(f"expected JSON object: {path}")
    return value, raw


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalingError(message)


def validate_schema(value: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ScalingError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
        raise ScalingError(f"{label} failed schema validation: {preview}")


def decimal_from(value: Any, label: str, *, positive: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ScalingError(f"{label} must be a finite Decimal") from exc
    if not number.is_finite():
        raise ScalingError(f"{label} must be finite")
    if positive and number <= 0:
        raise ScalingError(f"{label} must be greater than zero")
    return number


def canonical_decimal(value: Decimal) -> str:
    require(value.is_finite(), "cannot canonicalize non-finite Decimal")
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text == "-0":
        return "0"
    return text


def verify_v15_mapping(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    validate_schema(record, V15_SCHEMA, "v1.5 mapping record")
    body = copy.deepcopy(record)
    claimed = body["integrity"]["content_sha256"]
    body["integrity"]["content_sha256"] = ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(body))
    require(actual == claimed, "v1.5 mapping content digest mismatch")

    claimed_receipt = receipt.get("receipt_sha256")
    require(isinstance(claimed_receipt, str) and len(claimed_receipt) == 64, "v1.5 mapping receipt digest missing")
    receipt_body = copy.deepcopy(receipt)
    receipt_body.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(receipt_body)) == claimed_receipt, "v1.5 mapping receipt digest mismatch")
    require(receipt.get("verdict") == v15.VERDICT, "wrong v1.5 mapping receipt verdict")
    require(receipt.get("record_content_sha256") == claimed, "v1.5 mapping receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "v1.5 mapping receipt/file mismatch")
    require(receipt.get("mapping_method") == v15.MAPPING_METHOD, "v1.5 mapping method mismatch")
    require(receipt.get("fuzzy_matching_performed") is False, "v1.5 fuzzy-mapping promotion rejected")
    require(receipt.get("automatic_name_mapping_performed") is False, "v1.5 automatic-name mapping promotion rejected")
    require(receipt.get("environmental_calculation_performed") is False, "v1.5 calculation promotion rejected")
    require(receipt.get("building_quantity_multiplication_performed") is False, "v1.5 multiplication promotion rejected")
    require(receipt.get("unit_conversion_performed") is False, "v1.5 unit-conversion promotion rejected")
    require(receipt.get("certified") is False, "v1.5 certification promotion rejected")


def verify_v14_bundle(bundle: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    validate_schema(bundle, V14_SCHEMA, "v1.4 declaration bundle")
    try:
        content = v14.verify_record_integrity(bundle, label="v1.4 declaration bundle")
        v14.verify_receipt(receipt, label="v1.4 declaration bundle receipt", verdict=v14.VERDICT)
    except v14.BundleError as exc:
        raise ScalingError(str(exc)) from exc
    require(receipt.get("record_content_sha256") == content, "v1.4 bundle receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "v1.4 bundle receipt/file mismatch")
    require(receipt.get("building_quantity_multiplication_performed") is False, "v1.4 multiplication promotion rejected")
    require(receipt.get("calculated") is False, "v1.4 calculated promotion rejected")
    require(receipt.get("aggregation_performed") is False, "v1.4 aggregation promotion rejected")
    require(receipt.get("unit_conversion_performed") is False, "v1.4 conversion promotion rejected")
    require(receipt.get("certified") is False, "v1.4 certification promotion rejected")


def exact_scenario_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    return left == right


def select_row(bundle: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    results = bundle["environmental_results"]
    require(results.get("aggregation_performed") is False, "parent environmental results were aggregated")
    require(results.get("missing_modules_are_zero") is False, "parent environmental results treat missing modules as zero")
    rows = results.get("rows")
    require(isinstance(rows, list) and rows, "declaration bundle contains no environmental rows")

    matches = [
        row
        for row in rows
        if row.get("indicator_uuid") == selection["indicator_uuid"]
        and row.get("module") == selection["module"]
        and exact_scenario_equal(row.get("scenario"), selection["scenario"])
    ]
    require(len(matches) == 1, f"exact row selection must resolve to one row; found {len(matches)}")
    row = matches[0]
    require(row.get("value_origin") == "DECLARED_IN_SOURCE", "selected row is not source-declared")
    require(row.get("calculated") is False, "selected source row is already marked calculated")
    require(row.get("unit_conversion_performed") is False, "selected source row already applied unit conversion")
    require(row.get("canonical_unit") == results["indicator_scope"]["canonical_unit"], "selected row unit disagrees with indicator scope")
    require(isinstance(row.get("value_lexical"), str) and row["value_lexical"], "selected row lexical value missing")
    require(isinstance(row.get("value_decimal"), str) and row["value_decimal"], "selected row Decimal value missing")
    declared = decimal_from(row["value_decimal"], "declared environmental result")
    require(canonical_decimal(declared) == row["value_decimal"], "selected row value_decimal is not canonical")
    lexical_decimal = decimal_from(row["value_lexical"], "declared environmental result lexical value")
    require(lexical_decimal == declared, "selected row lexical and canonical Decimal values disagree")
    return row


def scale(
    mapping_record_path: Path,
    mapping_receipt_path: Path,
    bundle_path: Path,
    bundle_receipt_path: Path,
    request_path: Path,
) -> dict[str, Any]:
    mapping, mapping_raw = load_json(mapping_record_path)
    mapping_receipt, _ = load_json(mapping_receipt_path)
    bundle, bundle_raw = load_json(bundle_path)
    bundle_receipt, _ = load_json(bundle_receipt_path)
    request, request_raw = load_json(request_path)

    validate_schema(request, REQUEST_SCHEMA, "v1.6 calculation request")
    verify_v15_mapping(mapping, mapping_raw, mapping_receipt)
    verify_v14_bundle(bundle, bundle_raw, bundle_receipt)

    bindings = request["bindings"]
    require(bindings["mapping_record_content_sha256"] == mapping["integrity"]["content_sha256"], "request/mapping content binding mismatch")
    require(bindings["mapping_receipt_sha256"] == mapping_receipt["receipt_sha256"], "request/mapping receipt binding mismatch")
    require(bindings["declaration_bundle_content_sha256"] == bundle["integrity"]["content_sha256"], "request/bundle content binding mismatch")
    require(bindings["declaration_bundle_receipt_sha256"] == bundle_receipt["receipt_sha256"], "request/bundle receipt binding mismatch")

    declaration = mapping["declaration"]
    require(declaration["bundle_content_sha256"] == bundle["integrity"]["content_sha256"], "v1.5 mapping is not bound to this v1.4 bundle content")
    require(declaration["bundle_receipt_sha256"] == bundle_receipt["receipt_sha256"], "v1.5 mapping is not bound to this v1.4 bundle receipt")
    require(declaration["source_sha256"] == bundle["source_identity"]["source_sha256"], "mapping/bundle declaration source mismatch")
    require(declaration["process_dataset_uuid"] == bundle["source_identity"]["process_dataset_uuid"], "mapping/bundle process UUID mismatch")
    require(declaration["product_flow_uuid"] == bundle["declared_reference_basis"]["product_flow_uuid"], "mapping/bundle product-flow UUID mismatch")
    require(declaration["reference_quantity_decimal"] == bundle["declared_reference_basis"]["quantity_decimal"], "mapping/bundle reference quantity mismatch")
    require(declaration["reference_unit"] == bundle["declared_reference_basis"]["unit"], "mapping/bundle reference unit mismatch")

    mapped_quantity = mapping["ifc"]["quantity"]
    require(mapped_quantity["unit_identity"] == "kg", "v1.6 initial mapped quantity unit must be kg")
    require(mapped_quantity.get("numerical_conversion_applied") is False, "mapped quantity contains a prior numerical unit conversion")
    require(declaration["reference_unit"] == "kg", "v1.6 initial declaration reference unit must be kg")
    mapped_lexical = json.dumps(mapped_quantity["value"], ensure_ascii=False, separators=(",", ":"))
    mapped_decimal = decimal_from(mapped_lexical, "mapped IFC quantity", positive=True)
    reference_decimal = decimal_from(declaration["reference_quantity_decimal"], "declaration reference quantity", positive=True)
    require(canonical_decimal(reference_decimal) == declaration["reference_quantity_decimal"], "declaration reference quantity is not canonical Decimal")

    row = select_row(bundle, request["selection"])
    declared_decimal = decimal_from(row["value_decimal"], "selected declared result")
    scale_factor = mapped_decimal / reference_decimal
    scaled = scale_factor * declared_decimal

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridMappedDeclaredResultCalculation",
        "verdict": VERDICT,
        "calculation_scope": SCOPE,
        "inputs": {
            "request_file_sha256": sha256_bytes(request_raw),
            "mapping_record_content_sha256": mapping["integrity"]["content_sha256"],
            "mapping_record_file_sha256": sha256_bytes(mapping_raw),
            "mapping_receipt_sha256": mapping_receipt["receipt_sha256"],
            "declaration_bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "declaration_bundle_file_sha256": sha256_bytes(bundle_raw),
            "declaration_bundle_receipt_sha256": bundle_receipt["receipt_sha256"],
            "ifc_source_sha256": mapping["ifc"]["source_sha256"],
            "element_global_id": mapping["ifc"]["element"]["global_id"],
            "product_flow_uuid": declaration["product_flow_uuid"],
            "product_flow_version": declaration["product_flow_version"],
        },
        "selection": {
            "indicator_uuid": request["selection"]["indicator_uuid"],
            "module": request["selection"]["module"],
            "scenario": copy.deepcopy(request["selection"]["scenario"]),
            "source_location": copy.deepcopy(row["source_location"]),
        },
        "calculation": {
            "method": METHOD,
            "version": ENGINE_VERSION,
            "formula": FORMULA,
            "mapped_quantity": {
                "value_lexical": mapped_lexical,
                "value_decimal": canonical_decimal(mapped_decimal),
                "unit": "kg",
            },
            "reference_quantity": {
                "value_lexical": declaration["reference_quantity_decimal"],
                "value_decimal": canonical_decimal(reference_decimal),
                "unit": "kg",
            },
            "declared_result": {
                "value_lexical": row["value_lexical"],
                "value_decimal": row["value_decimal"],
                "unit": row["canonical_unit"],
                "value_origin": row["value_origin"],
                "source_calculated": row["calculated"],
                "source_unit_conversion_performed": row["unit_conversion_performed"],
            },
            "scale_factor_decimal": canonical_decimal(scale_factor),
            "scaled_result_decimal": canonical_decimal(scaled),
            "scaled_result_unit": row["canonical_unit"],
        },
        "calculation_performed": True,
        "aggregation_performed": False,
        "missing_modules_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "fuzzy_mapping_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This result is one deterministic scaled contribution for one explicitly selected source-declared row and one exact mapped IFC quantity; it is not a complete building LCA.",
            "No lifecycle-module/scenario aggregation is performed and missing modules are not treated as zero.",
            "The kg-to-kg relationship is identity-only; no unit conversion is performed.",
            "The declared environmental result remains source-content evidence; this calculation does not establish scientific validity, product representativeness, professional LCA review, programme-operator/BBSR approval, regulatory approval, or certification.",
        ],
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    validate_schema(record, RESULT_SCHEMA, "v1.6 scaled result")
    return record


def build_receipt(record: dict[str, Any], record_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "mapping_receipt_sha256": record["inputs"]["mapping_receipt_sha256"],
        "declaration_bundle_receipt_sha256": record["inputs"]["declaration_bundle_receipt_sha256"],
        "indicator_uuid": record["selection"]["indicator_uuid"],
        "module": record["selection"]["module"],
        "scenario": copy.deepcopy(record["selection"]["scenario"]),
        "scale_factor_decimal": record["calculation"]["scale_factor_decimal"],
        "scaled_result_decimal": record["calculation"]["scaled_result_decimal"],
        "scaled_result_unit": record["calculation"]["scaled_result_unit"],
        "calculation_scope": SCOPE,
        "calculation_performed": True,
        "aggregation_performed": False,
        "missing_modules_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "fuzzy_mapping_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def write_outputs(output_dir: Path, record: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "mapped-declared-result-calculation.json"
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt = build_receipt(record, record_bytes)
    receipt_path = output_dir / "mapped-declared-result-calculation-receipt.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return record_path, receipt_path, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.6 exact-decimal mapped declared-result scaling")
    parser.add_argument("--mapping-record", type=Path, required=True)
    parser.add_argument("--mapping-receipt", type=Path, required=True)
    parser.add_argument("--declaration-bundle", type=Path, required=True)
    parser.add_argument("--declaration-bundle-receipt", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = scale(
            args.mapping_record,
            args.mapping_receipt,
            args.declaration_bundle,
            args.declaration_bundle_receipt,
            args.request,
        )
        _, _, receipt = write_outputs(args.output_dir, record)
    except (ScalingError, SchemaError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {receipt['verdict']}")
    print(f"SCOPE: {receipt['calculation_scope']}")
    print(f"MODULE: {receipt['module']}")
    print(f"SCALE FACTOR: {receipt['scale_factor_decimal']}")
    print(f"SCALED RESULT: {receipt['scaled_result_decimal']} {receipt['scaled_result_unit']}")
    print("AGGREGATION: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
