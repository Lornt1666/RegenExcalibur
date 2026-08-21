#!/usr/bin/env python3
"""ProofGrid v1.5 explicit IFC material -> declaration product-flow mapping.

This gate binds one exact IFC element/material/declared quantity identity to one
exact declaration product-flow identity under an explicit reviewed mapping
artifact. It performs no fuzzy/name matching, environmental calculation,
quantity multiplication, aggregation, or unit conversion.
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
from reference import ifc_lca_map as ifcmap  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid IFC Declaration Product Mapper"
ENGINE_VERSION = "1.5.0"
VERDICT = "IFC_DECLARATION_PRODUCT_MAPPING_VERIFIABLE"
MAPPING_METHOD = "EXPLICIT_REVIEWED_ARTIFACT"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64
MAPPING_SCHEMA = ROOT / "schemas" / "ifc-declaration-product-mapping.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "ifc-declaration-product-mapping-result.schema.json"
IFC_SCHEMA = ROOT / "schemas" / "ifc-extraction.schema.json"
V14_SCHEMA = ROOT / "schemas" / "declaration-evidence-bundle.schema.json"


class ProductMappingError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise ProductMappingError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductMappingError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProductMappingError(f"expected JSON object: {path}")
    return value, raw


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProductMappingError(message)


def validate_schema(value: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ProductMappingError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
        raise ProductMappingError(f"{label} failed schema validation: {preview}")


def canonical_decimal(value: Any, label: str) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ProductMappingError(f"{label} must be a finite Decimal") from exc
    if not number.is_finite() or number <= 0:
        raise ProductMappingError(f"{label} must be finite and greater than zero")
    text = format(number.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def verify_bundle(bundle: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    validate_schema(bundle, V14_SCHEMA, "v1.4 declaration bundle")
    content = v14.verify_record_integrity(bundle, label="v1.4 declaration bundle")
    v14.verify_receipt(receipt, label="v1.4 declaration bundle receipt", verdict=v14.VERDICT)
    require(receipt.get("record_content_sha256") == content, "v1.4 bundle receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "v1.4 bundle receipt/file mismatch")
    require(receipt.get("building_quantity_multiplication_performed") is False, "v1.4 multiplication promotion rejected")
    require(receipt.get("calculated") is False, "v1.4 calculated promotion rejected")
    require(receipt.get("unit_conversion_performed") is False, "v1.4 conversion promotion rejected")
    require(receipt.get("certified") is False, "v1.4 certification promotion rejected")


def verify_basis_parent(bundle: dict[str, Any], basis: dict[str, Any], basis_raw: bytes, receipt: dict[str, Any]) -> None:
    content = v14.verify_record_integrity(basis, label="v1.3 reference basis")
    v14.verify_receipt(receipt, label="v1.3 reference-basis receipt", verdict="DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE")
    require(receipt.get("record_content_sha256") == content, "basis receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(basis_raw), "basis receipt/file mismatch")
    parent = bundle.get("parent_evidence", {}).get("declared_reference_basis", {})
    require(parent.get("record_content_sha256") == content, "v1.4 does not bind this basis record content")
    require(parent.get("record_file_sha256") == sha256_bytes(basis_raw), "v1.4 does not bind this basis record file")
    require(parent.get("receipt_sha256") == receipt.get("receipt_sha256"), "v1.4 does not bind this basis receipt")
    require(basis.get("certified") is False, "basis certification promotion rejected")
    require(basis.get("calculated") is False, "basis calculated promotion rejected")
    require(basis.get("unit_conversion_performed") is False, "basis conversion promotion rejected")


def resolve_declaration(bundle: dict[str, Any], bundle_receipt: dict[str, Any], basis: dict[str, Any], basis_receipt: dict[str, Any]) -> dict[str, Any]:
    source = bundle["source_identity"]
    basis_parent = basis["parent"]
    require(source["source_sha256"] == basis_parent["source_sha256"], "v1.4/basis source SHA mismatch")
    require(source["process_xml_sha256"] == basis_parent["process_xml_sha256"], "v1.4/basis process XML mismatch")
    require(source["process_dataset_uuid"] == basis_parent["process_dataset_uuid"], "v1.4/basis process UUID mismatch")
    require(source["format_version"] == basis_parent["format_version"], "v1.4/basis format version mismatch")

    declared = bundle["declared_reference_basis"]
    basis_declared = basis["declared_reference_basis"]
    require(declared == basis_declared, "v1.4/reference-basis declaration mismatch")
    product = basis.get("product_flow")
    require(isinstance(product, dict), "basis product-flow evidence missing")
    require(product.get("uuid") == declared.get("product_flow_uuid"), "basis product-flow UUID mismatch")
    version = product.get("version")
    require(isinstance(version, str) and version, "basis product-flow version missing")
    reference_unit = declared.get("unit")
    require(reference_unit == "kg", f"v1.5 initial unit gate requires declaration reference unit kg, got {reference_unit!r}")
    quantity_decimal = canonical_decimal(declared.get("quantity_decimal"), "declaration reference quantity")

    return {
        "bundle_content_sha256": bundle["integrity"]["content_sha256"],
        "bundle_receipt_sha256": bundle_receipt["receipt_sha256"],
        "source_sha256": source["source_sha256"],
        "process_dataset_uuid": source["process_dataset_uuid"],
        "basis_record_content_sha256": basis["integrity"]["content_sha256"],
        "basis_receipt_sha256": basis_receipt["receipt_sha256"],
        "product_flow_uuid": product["uuid"],
        "product_flow_version": version,
        "reference_quantity_decimal": quantity_decimal,
        "reference_unit": reference_unit,
    }


def map_product(
    extraction_path: Path,
    mapping_path: Path,
    bundle_path: Path,
    bundle_receipt_path: Path,
    basis_path: Path,
    basis_receipt_path: Path,
) -> dict[str, Any]:
    extraction, extraction_raw = load_json(extraction_path)
    mapping_artifact, mapping_raw = load_json(mapping_path)
    bundle, bundle_raw = load_json(bundle_path)
    bundle_receipt, _ = load_json(bundle_receipt_path)
    basis, basis_raw = load_json(basis_path)
    basis_receipt, _ = load_json(basis_receipt_path)

    validate_schema(extraction, IFC_SCHEMA, "IFC extraction")
    validate_schema(mapping_artifact, MAPPING_SCHEMA, "explicit mapping artifact")
    try:
        verify_bundle(bundle, bundle_raw, bundle_receipt)
        verify_basis_parent(bundle, basis, basis_raw, basis_receipt)
    except v14.BundleError as exc:
        raise ProductMappingError(str(exc)) from exc
    declaration = resolve_declaration(bundle, bundle_receipt, basis, basis_receipt)

    mapping = mapping_artifact["mapping"]
    require(mapping["review"]["state"] == "REVIEWED_MAPPING_DECISION", "mapping decision is not REVIEWED_MAPPING_DECISION")
    require(mapping["source_ifc"]["sha256"] == extraction["source_sha256"], "mapping IFC source SHA mismatch")
    require(mapping["source_ifc"]["schema"] == extraction["schema"], "mapping IFC schema mismatch")
    require(mapping["declaration"] == declaration, "mapping declaration target does not exactly match accepted v1.4/v1.3 evidence")

    try:
        element = ifcmap._find_element(extraction, mapping)
        material = ifcmap._find_material(element, mapping)
        quantity = ifcmap._find_quantity(element, mapping)
        unit_identity = ifcmap.explicit_unit_identity(quantity["unit"])
    except ifcmap.MappingError as exc:
        raise ProductMappingError(str(exc)) from exc

    require(unit_identity == declaration["reference_unit"], "IFC quantity unit is not identical to declaration product/reference unit")
    require(mapping["quantity"]["value"] == quantity["value"], "mapping quantity changed after extraction")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridIFCDeclarationProductMapping",
        "verdict": VERDICT,
        "mapping_id": mapping["id"],
        "ifc": {
            "extraction_file_sha256": sha256_bytes(extraction_raw),
            "source_sha256": extraction["source_sha256"],
            "schema": extraction["schema"],
            "element": {
                "step_id": element["step_id"],
                "global_id": element["global_id"],
                "ifc_type": element["ifc_type"],
                "name": element.get("name"),
            },
            "material": {
                "association_step_id": material["association_step_id"],
                "material_step_id": material["material_step_id"],
                "declared_name": material["name"],
                "source_type": material["source_type"],
            },
            "quantity": {
                "set_step_id": quantity["set_step_id"],
                "quantity_step_id": quantity["quantity_step_id"],
                "name": quantity["name"],
                "ifc_quantity_type": quantity["ifc_quantity_type"],
                "value": quantity["value"],
                "unit_identity": unit_identity,
                "unit": quantity["unit"],
                "value_source": quantity["value_source"],
                "numerical_conversion_applied": False,
            },
        },
        "declaration": declaration,
        "review": copy.deepcopy(mapping["review"]),
        "mapping_artifact": {
            "file_sha256": sha256_bytes(mapping_raw),
            "artifact_version": mapping_artifact["artifact_version"],
        },
        "mapping_method": MAPPING_METHOD,
        "fuzzy_matching_performed": False,
        "automatic_name_mapping_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": list(mapping["limitations"]) + [
            "The mapping is authorized by the explicit reviewed artifact and exact identifiers, not by material/product display-name similarity.",
            "The IFC declared quantity is preserved as evidence only; v1.5 does not multiply it by any environmental result.",
            "kg-to-kg is treated only as an identity unit relationship; no numerical conversion is performed.",
            "Mapping review state does not imply professional licensure, scientific validity, engineering approval, programme-operator/BBSR approval, regulatory approval, or certification.",
        ],
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    validate_schema(record, RESULT_SCHEMA, "mapping result")
    return record


def build_receipt(record: dict[str, Any], record_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "mapping_id": record["mapping_id"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "ifc_source_sha256": record["ifc"]["source_sha256"],
        "declaration_bundle_content_sha256": record["declaration"]["bundle_content_sha256"],
        "declaration_bundle_receipt_sha256": record["declaration"]["bundle_receipt_sha256"],
        "basis_record_content_sha256": record["declaration"]["basis_record_content_sha256"],
        "basis_receipt_sha256": record["declaration"]["basis_receipt_sha256"],
        "product_flow_uuid": record["declaration"]["product_flow_uuid"],
        "product_flow_version": record["declaration"]["product_flow_version"],
        "reference_unit": record["declaration"]["reference_unit"],
        "mapping_method": MAPPING_METHOD,
        "fuzzy_matching_performed": False,
        "automatic_name_mapping_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def write_outputs(output_dir: Path, record: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "ifc-declaration-product-mapping.json"
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt = build_receipt(record, record_bytes)
    receipt_path = output_dir / "ifc-declaration-product-mapping-receipt.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return record_path, receipt_path, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.5 explicit IFC declaration product-flow mapping")
    parser.add_argument("--ifc-extraction", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--declaration-bundle", type=Path, required=True)
    parser.add_argument("--declaration-bundle-receipt", type=Path, required=True)
    parser.add_argument("--basis-record", type=Path, required=True)
    parser.add_argument("--basis-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = map_product(
            args.ifc_extraction,
            args.mapping,
            args.declaration_bundle,
            args.declaration_bundle_receipt,
            args.basis_record,
            args.basis_receipt,
        )
        _, _, receipt = write_outputs(args.output_dir, record)
    except (ProductMappingError, SchemaError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {receipt['verdict']}")
    print(f"PRODUCT FLOW: {receipt['product_flow_uuid']} @ {receipt['product_flow_version']}")
    print(f"REFERENCE UNIT: {receipt['reference_unit']}")
    print("ENVIRONMENTAL CALCULATION: false")
    print("BUILDING QUANTITY MULTIPLICATION: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
