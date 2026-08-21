#!/usr/bin/env python3
"""ProofGrid v1.4.1 declaration product identity-closure hardener.

Additively binds an accepted v1.4 declaration-evidence bundle back to the exact
accepted v1.3 reference-basis record so downstream mapping can rely on the full
product-flow / flow-property / reference-unit identity closure rather than a
UUID-only shortcut.

No environmental calculation or quantity multiplication is performed.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declaration_evidence_bundle as v14  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Declaration Product Identity Closure Hardener"
ENGINE_VERSION = "1.4.1"
VERDICT = "DECLARATION_PRODUCT_IDENTITY_CLOSURE_BOUND_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = v14.CANONICALIZATION
SCHEMA_PATH = ROOT / "schemas" / "declaration-product-identity-closure.schema.json"


class ClosureError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureError(message)


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ClosureError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosureError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def verify_v14(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    require(record.get("verdict") == "DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE", "v1.4 bundle verdict mismatch")
    try:
        content = v14.verify_record_integrity(record, label="v1.4 declaration bundle")
        v14.verify_receipt(receipt, label="v1.4 declaration-bundle receipt", verdict="DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE")
    except Exception as exc:
        raise ClosureError(str(exc)) from exc
    require(receipt.get("record_content_sha256") == content, "v1.4 receipt/content mismatch")
    require(receipt.get("record_file_sha256") == v14.sha256_bytes(raw), "v1.4 receipt/file mismatch")
    require(receipt.get("source_identity") == record.get("source_identity"), "v1.4 source-identity receipt mismatch")
    require(receipt.get("parent_evidence") == record.get("parent_evidence"), "v1.4 parent-evidence receipt mismatch")
    for key in (
        "calculated",
        "environmental_values_transformed",
        "building_quantity_multiplication_performed",
        "aggregation_performed",
        "unit_conversion_performed",
        "scientific_validation_performed",
        "professional_review_performed",
        "certified",
    ):
        require(record.get(key) is False, f"v1.4 {key} promotion rejected")
        require(receipt.get(key) is False, f"v1.4 receipt {key} promotion rejected")


def verify_basis(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    try:
        v14.verify_basis(record, raw, receipt)
    except Exception as exc:
        raise ClosureError(str(exc)) from exc


def validate_internal_identity(record: dict[str, Any]) -> None:
    process_ref = record.get("process_reference", {})
    product = record.get("product_flow", {})
    flow_property = record.get("flow_property", {})
    reference_unit = record.get("reference_unit", {})
    basis = record.get("declared_reference_basis", {})

    require(process_ref.get("product_flow_uuid") == product.get("uuid") == basis.get("product_flow_uuid"), "product-flow UUID closure mismatch")
    require(process_ref.get("product_flow_version") == product.get("version"), "product-flow version closure mismatch")
    require(isinstance(product.get("names"), list) and product["names"], "product-flow names missing")
    require(isinstance(product.get("sha256"), str) and len(product["sha256"]) == 64, "product-flow SHA-256 missing")
    require(str(product.get("reference_flow_property_internal_id", "")) == "0", "unexpected reference flow-property internal ID")

    require(flow_property.get("reference_unit_group_uuid") == reference_unit.get("unit_group_uuid"), "flow-property/reference-unit-group mismatch")
    require(isinstance(flow_property.get("uuid"), str) and flow_property["uuid"], "flow-property UUID missing")
    require(isinstance(flow_property.get("version"), str) and flow_property["version"], "flow-property version missing")
    require(isinstance(flow_property.get("master_sha256"), str) and len(flow_property["master_sha256"]) == 64, "flow-property master SHA-256 missing")
    require(reference_unit.get("reference_unit_internal_id") == "0", "unexpected reference unit internal ID")
    require(reference_unit.get("name") == basis.get("unit"), "reference-unit/basis-unit mismatch")
    require(reference_unit.get("factor_decimal") == "1", "non-identity reference-unit factor requires separate conversion gate")
    require(flow_property.get("flow_mean_decimal") == "1", "non-identity flow-property mean requires separate conversion gate")
    require(process_ref.get("exchange_amount_decimal") == basis.get("quantity_decimal"), "process exchange/reference-basis quantity mismatch")
    require(process_ref.get("exchange_amount_decimal") == "1", "non-identity process exchange amount requires separate calculation gate")
    require(basis.get("identity_chain") is True and basis.get("basis_status") == "IDENTITY_CHAIN_VERIFIED", "declared basis identity chain not verified")


def bind(v14_record: dict[str, Any], v14_raw: bytes, v14_receipt: dict[str, Any], basis_record: dict[str, Any], basis_raw: bytes, basis_receipt: dict[str, Any]) -> dict[str, Any]:
    verify_v14(v14_record, v14_raw, v14_receipt)
    verify_basis(basis_record, basis_raw, basis_receipt)
    validate_internal_identity(basis_record)

    basis_binding = v14_record.get("parent_evidence", {}).get("declared_reference_basis", {})
    require(basis_binding.get("record_content_sha256") == basis_record["integrity"]["content_sha256"], "v1.4/v1.3 basis content-hash mismatch")
    require(basis_binding.get("record_file_sha256") == v14.sha256_bytes(basis_raw), "v1.4/v1.3 basis file-hash mismatch")
    require(basis_binding.get("receipt_sha256") == basis_receipt.get("receipt_sha256"), "v1.4/v1.3 basis receipt-hash mismatch")

    source = v14_record["source_identity"]
    parent = basis_record["parent"]
    require(source["source_sha256"] == parent["source_sha256"], "v1.4/v1.3 source SHA-256 mismatch")
    require(source["process_xml_sha256"] == parent["process_xml_sha256"], "v1.4/v1.3 process XML SHA-256 mismatch")
    require(source["process_dataset_uuid"] == parent["process_dataset_uuid"], "v1.4/v1.3 process UUID mismatch")
    require(source["format_version"] == parent["format_version"], "v1.4/v1.3 format-version mismatch")

    v14_basis = v14_record["declared_reference_basis"]
    v13_basis = basis_record["declared_reference_basis"]
    require(v14_basis == v13_basis, "v1.4/v1.3 declared reference basis mismatch")

    semantics = v14_record["amount_semantics"]
    process_ref = basis_record["process_reference"]
    require(semantics["reference_exchange_internal_id"] == process_ref["reference_exchange_internal_id"], "amount-semantics/reference-exchange mismatch")
    require(semantics["mean_amount"]["lexical"] == process_ref["exchange_amount_lexical"], "amount-semantics/process exchange lexical mismatch")
    require(semantics["mean_amount"]["decimal"] == process_ref["exchange_amount_decimal"], "amount-semantics/process exchange Decimal mismatch")
    require(semantics["resulting_amount_present"] is False and semantics["resulting_amount"] is None, "unresolved resultingAmount rejected")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclarationProductIdentityClosure",
        "verdict": VERDICT,
        "source_identity": copy.deepcopy(source),
        "parent_evidence": {
            "v14_bundle_content_sha256": v14_record["integrity"]["content_sha256"],
            "v14_bundle_file_sha256": v14.sha256_bytes(v14_raw),
            "v14_bundle_receipt_sha256": v14_receipt["receipt_sha256"],
            "v13_basis_content_sha256": basis_record["integrity"]["content_sha256"],
            "v13_basis_file_sha256": v14.sha256_bytes(basis_raw),
            "v13_basis_receipt_sha256": basis_receipt["receipt_sha256"],
        },
        "process_reference": copy.deepcopy(process_ref),
        "product_flow": copy.deepcopy(basis_record["product_flow"]),
        "flow_property": copy.deepcopy(basis_record["flow_property"]),
        "reference_unit": copy.deepcopy(basis_record["reference_unit"]),
        "declared_reference_basis": copy.deepcopy(v13_basis),
        "environmental_evidence_binding": {
            "row_count": v14_record["environmental_results"]["row_count"],
            "indicator_scope": copy.deepcopy(v14_record["environmental_results"]["indicator_scope"]),
            "environmental_result_unit": v14_record["dimension_separation"]["environmental_result_unit"],
            "product_reference_unit": v14_record["dimension_separation"]["product_reference_unit"],
            "unit_interchange_permitted": False,
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This record preserves the declaration product/reference identity closure for the exact accepted v1.4/v1.3 evidence only.",
            "The initial gate accepts only the proven identity chain; non-identity process, flow-property, or unit factors require a separate calculation/conversion gate.",
            "No IFC/material identity is inferred or mapped by v1.4.1.",
            "No environmental value is multiplied, divided, aggregated, converted, scientifically validated, professionally reviewed, or certified.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    record["integrity"]["content_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(record))
    validate_schema(record)
    return record


def validate_schema(record: dict[str, Any]) -> None:
    schema, _ = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ClosureError(f"invalid v1.4.1 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise ClosureError(f"product identity-closure schema validation failed: {preview}")


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": v14.sha256_bytes(record_file_bytes),
        "source_identity": copy.deepcopy(record["source_identity"]),
        "parent_evidence": copy.deepcopy(record["parent_evidence"]),
        "process_reference": copy.deepcopy(record["process_reference"]),
        "product_flow": copy.deepcopy(record["product_flow"]),
        "declared_reference_basis": copy.deepcopy(record["declared_reference_basis"]),
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.4.1 declaration product identity closure")
    parser.add_argument("--v14-bundle", type=Path, required=True)
    parser.add_argument("--v14-receipt", type=Path, required=True)
    parser.add_argument("--v13-basis", type=Path, required=True)
    parser.add_argument("--v13-basis-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        v14_record, v14_raw = load_json(args.v14_bundle)
        v14_receipt, _ = load_json(args.v14_receipt)
        basis_record, basis_raw = load_json(args.v13_basis)
        basis_receipt, _ = load_json(args.v13_basis_receipt)
        record = bind(v14_record, v14_raw, v14_receipt, basis_record, basis_raw, basis_receipt)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "declaration-product-identity-closure.json"
        record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        record_path.write_bytes(record_bytes)
        receipt = build_receipt(record, record_bytes)
        (args.output_dir / "declaration-product-identity-closure-receipt.json").write_bytes(
            (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {VERDICT}")
    print(f"PRODUCT FLOW: {record['product_flow']['uuid']} @ {record['product_flow']['version']}")
    print(f"REFERENCE BASIS: {record['declared_reference_basis']['quantity_decimal']} {record['declared_reference_basis']['unit']}")
    print("BUILDING QUANTITY MULTIPLICATION PERFORMED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
