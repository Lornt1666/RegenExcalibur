#!/usr/bin/env python3
"""ProofGrid v1.6 exact-Decimal scaling of one mapped declared result row.

Evidence chain:
  v1.5.1 exact STEP Decimal
    -> v1.5 explicit mapping
    -> v1.4.1 v1.3 declaration product/reference closure
    -> v1.4 v1.3 declaration evidence bundle
    -> one explicitly selected source-declared environmental row
    -> one Decimal-only scaled contribution.

No binary float is calculation authority. There is deliberately no aggregation,
missing-module zeroing, unit conversion, scenario inference, fuzzy mapping, or
complete-building-LCA claim in this gate.
"""

from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
ENGINE_NAME = "RegenExcalibur ProofGrid Exact-Decimal Mapped Declared Result Scaler"
ENGINE_VERSION = "1.6.0"
VERDICT = "MAPPED_DECLARED_RESULT_SCALED_VERIFIABLE"
SCOPE = "SINGLE_MAPPED_DECLARED_RESULT_ROW"
METHOD = "source_authoritative_decimal_reference_basis_scaling"
FORMULA = "(mapped_ifc_quantity_decimal / declaration_reference_quantity_decimal) * declared_environmental_result_decimal"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

V151_VERDICT = "IFC_DECLARED_QUANTITY_EXACT_DECIMAL_VERIFIABLE"
V15_VERDICT = "IFC_DECLARATION_PRODUCT_MAPPING_VERIFIABLE"
V141_VERDICT = "DECLARATION_PRODUCT_IDENTITY_CLOSURE_BOUND_VERIFIABLE"
V14_VERDICT = "DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE"
V15_METHOD = "EXPLICIT_REVIEWED_ARTIFACT"

# Exact accepted parent identities for the first bounded v1.6 control.
EXPECTED_V151 = {
    "content": "fd107f90c7909569a64ce2d456cba8777cb29578f90ff6c7a458edba1ddad41a",
    "file": "4adfdf825e825e8feaa3dd1b3b22b230a72ab02a475bad6b074b9e8aa87fff99",
    "receipt": "9367965c593424bf7855171513cfc1bce0f39c5262e4cdad1d813f7bbdff91f2",
}
EXPECTED_V15 = {
    "content": "194d3cf29b0f674ce5ca26ab1b0ce07f8cb87449d60090bf9271ac3726371fa7",
    "file": "7accde96c1ca5c00b29a827ee6bc21b1b77bab7411e79d2fba756617c4d5eff1",
    "receipt": "834bee35d83872c549552b291d6cdf2e46f4110b161704bf40a22e58e0178a67",
}
EXPECTED_V141 = {
    "content": "cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd",
    "file": "9cdba7a6e512ecaa1d1c5320c1fac55d7e9ad8a74f7cf2a66c75204dd390eca6",
    "receipt": "27abef64ed6e86fb8f555a4b42c9a67f14e74fec584d8c4496446abfd0009921",
}
EXPECTED_V14 = {
    "content": "8e71852027be10c4120f6185e0ae90127da9c72bf1e64f5c50b08442ed2c0aa0",
    "file": "70b03882bda92680851b48b39091dcdb20a4b386a5f3b2b712e8d08d054d359a",
    "receipt": "ac3f22efd3220e7c3e323c3178421af4b45d54c9e6ac5f158c76c6db3422ed84",
}
EXPECTED_IFC_SOURCE_SHA256 = "23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6"

REQUEST_SCHEMA = ROOT / "schemas" / "mapped-declared-result-v16-request.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "mapped-declared-result-v16.schema.json"


class ScalingError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalingError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


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
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def validate_schema(value: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ScalingError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        preview = "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors[:6]
        )
        raise ScalingError(f"{label} failed schema validation: {preview}")


def verify_record(record: dict[str, Any], raw: bytes, *, expected_verdict: str, label: str) -> str:
    require(record.get("verdict") == expected_verdict, f"{label} verdict mismatch")
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), f"{label} missing integrity")
    expected = integrity.get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, f"{label} missing content SHA-256")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow)) == expected, f"{label} content SHA-256 mismatch")
    return expected


def verify_receipt(receipt: dict[str, Any], *, expected_verdict: str, label: str, record_content_sha256: str, record_file_sha256: str) -> str:
    require(receipt.get("verdict") == expected_verdict, f"{label} verdict mismatch")
    claimed = receipt.get("receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing receipt SHA-256")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, f"{label} canonical digest mismatch")
    require(receipt.get("record_content_sha256") == record_content_sha256, f"{label} record-content binding mismatch")
    require(receipt.get("record_file_sha256") == record_file_sha256, f"{label} record-file binding mismatch")
    return claimed


def decimal_from_string(value: Any, label: str, *, positive: bool = False) -> Decimal:
    require(isinstance(value, str) and value, f"{label} must be a non-empty Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ScalingError(f"{label} is not a finite Decimal") from exc
    require(number.is_finite(), f"{label} must be finite")
    if positive:
        require(number > 0, f"{label} must be greater than zero")
    return number


def canonical_decimal(value: Decimal) -> str:
    require(value.is_finite(), "cannot canonicalize non-finite Decimal")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-0", "+0"} else text


def require_canonical_decimal(value: Any, label: str, *, positive: bool = False) -> Decimal:
    number = decimal_from_string(value, label, positive=positive)
    require(canonical_decimal(number) == value, f"{label} is not canonical Decimal")
    return number


def require_false_flags(obj: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        require(obj.get(key) is False, f"{label} {key} promotion rejected")


def exact_scenario_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return isinstance(left, dict) and isinstance(right, dict) and left == right


def verify_v151(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> tuple[str, str]:
    content = verify_record(record, raw, expected_verdict=V151_VERDICT, label="v1.5.1 quantity record")
    receipt_sha = verify_receipt(receipt, expected_verdict=V151_VERDICT, label="v1.5.1 quantity receipt", record_content_sha256=content, record_file_sha256=sha256_bytes(raw))
    require_false_flags(record, ("calculation_performed","environmental_calculation_performed","building_quantity_multiplication_performed","unit_conversion_performed","scientific_validation_performed","professional_review_performed","certified"), "v1.5.1 quantity record")
    require_false_flags(receipt, ("calculation_performed","environmental_calculation_performed","building_quantity_multiplication_performed","unit_conversion_performed","scientific_validation_performed","professional_review_performed","certified"), "v1.5.1 quantity receipt")
    q = record.get("quantity", {})
    require(q.get("source_token_is_authority") is True, "v1.5.1 source token is not quantity authority")
    require(q.get("parser_numeric_value_is_authority") is False, "v1.5.1 parser float is marked as authority")
    require(q.get("mapped_parser_consistent_with_source") is True, "v1.5.1 parser/source consistency not proven")
    require(q.get("unit_identity") == "kg", "v1.5.1 initial quantity unit must be kg")
    canonical = require_canonical_decimal(q.get("quantity_decimal"), "v1.5.1 quantity Decimal", positive=True)
    lexical = decimal_from_string(q.get("quantity_lexical"), "v1.5.1 quantity lexical", positive=True)
    require(lexical == canonical, "v1.5.1 quantity lexical/Decimal mismatch")
    require(record.get("ifc_source", {}).get("sha256") == receipt.get("ifc_source_sha256"), "v1.5.1 IFC source receipt mismatch")
    return content, receipt_sha


def verify_v15(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> tuple[str, str]:
    content = verify_record(record, raw, expected_verdict=V15_VERDICT, label="v1.5 mapping record")
    receipt_sha = verify_receipt(receipt, expected_verdict=V15_VERDICT, label="v1.5 mapping receipt", record_content_sha256=content, record_file_sha256=sha256_bytes(raw))
    require(record.get("mapping_method") == V15_METHOD, "v1.5 mapping method mismatch")
    require_false_flags(record, ("fuzzy_matching_performed","automatic_name_mapping_performed","environmental_calculation_performed","building_quantity_multiplication_performed","unit_conversion_performed","scientific_validation_performed","professional_review_performed","certified"), "v1.5 mapping")
    q = record.get("ifc", {}).get("quantity", {})
    require(q.get("unit_identity") == "kg", "v1.5 mapped quantity unit must be kg")
    require(q.get("numerical_conversion_applied") is False, "v1.5 mapped quantity already applied numerical conversion")
    declaration = record.get("declaration", {})
    require(declaration.get("format_version") == "1.3", "final v1.6 requires v1.5 v1.3 declaration mapping")
    require(declaration.get("reference_unit") == "kg", "v1.5 declaration reference unit must be kg")
    require_canonical_decimal(declaration.get("reference_quantity_decimal"), "v1.5 reference quantity", positive=True)
    return content, receipt_sha


def verify_v141(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> tuple[str, str]:
    content = verify_record(record, raw, expected_verdict=V141_VERDICT, label="v1.4.1 closure record")
    receipt_sha = verify_receipt(receipt, expected_verdict=V141_VERDICT, label="v1.4.1 closure receipt", record_content_sha256=content, record_file_sha256=sha256_bytes(raw))
    require_false_flags(record, ("calculated","environmental_values_transformed","building_quantity_multiplication_performed","aggregation_performed","unit_conversion_performed","scientific_validation_performed","professional_review_performed","certified"), "v1.4.1 closure")
    source = record.get("source_identity", {})
    require(source.get("format_version") == "1.3", "v1.4.1 closure must be v1.3 lineage")
    basis = record.get("declared_reference_basis", {})
    require(basis.get("identity_chain") is True and basis.get("basis_status") == "IDENTITY_CHAIN_VERIFIED", "v1.4.1 reference identity chain not verified")
    require(basis.get("unit") == "kg", "v1.4.1 reference unit must be kg")
    require_canonical_decimal(basis.get("quantity_decimal"), "v1.4.1 reference quantity", positive=True)
    ref_unit = record.get("reference_unit", {})
    require(ref_unit.get("name") == "kg", "v1.4.1 reference-unit identity must be kg")
    require(require_canonical_decimal(ref_unit.get("factor_decimal"), "v1.4.1 reference-unit factor", positive=True) == Decimal("1"), "v1.4.1 reference-unit factor must be identity 1")
    return content, receipt_sha


def verify_v14(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> tuple[str, str]:
    content = verify_record(record, raw, expected_verdict=V14_VERDICT, label="v1.4 bundle")
    receipt_sha = verify_receipt(receipt, expected_verdict=V14_VERDICT, label="v1.4 bundle receipt", record_content_sha256=content, record_file_sha256=sha256_bytes(raw))
    require_false_flags(record, ("aggregation_performed","building_quantity_multiplication_performed","calculated","environmental_values_transformed","unit_conversion_performed","scientific_validation_performed","professional_review_performed","certified"), "v1.4 bundle")
    source = record.get("source_identity", {})
    require(source.get("format_version") == "1.3", "v1.4 bundle must be v1.3 lineage")
    results = record.get("environmental_results", {})
    require(results.get("aggregation_performed") is False, "v1.4 environmental rows were aggregated")
    require(results.get("missing_modules_are_zero") is False, "v1.4 environmental rows treat missing modules as zero")
    basis = record.get("declared_reference_basis", {})
    require(basis.get("unit") == "kg", "v1.4 declaration reference unit must be kg")
    require_canonical_decimal(basis.get("quantity_decimal"), "v1.4 declaration reference quantity", positive=True)
    return content, receipt_sha


def canonical_pretty_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def verify_lineage(quantity, quantity_content, quantity_receipt_sha, mapping, mapping_content, mapping_receipt_sha, closure, closure_content, closure_raw, closure_receipt_sha, bundle, bundle_content, bundle_raw, bundle_receipt_sha) -> None:
    qe = quantity["mapping_evidence"]
    require(qe.get("mapping_content_sha256") == mapping_content, "v1.5.1 quantity is not bound to this v1.5 mapping content")
    require(qe.get("mapping_file_sha256") == sha256_bytes(canonical_pretty_bytes(mapping)), "v1.5.1 mapping file binding mismatch")
    require(qe.get("mapping_receipt_sha256") == mapping_receipt_sha, "v1.5.1 quantity is not bound to this v1.5 mapping receipt")
    require(qe.get("mapping_id") == mapping.get("mapping_id"), "v1.5.1/v1.5 mapping ID mismatch")
    require(qe.get("product_flow_uuid") == mapping["declaration"]["product_flow_uuid"], "v1.5.1/v1.5 product-flow UUID mismatch")
    require(qe.get("product_flow_version") == mapping["declaration"]["product_flow_version"], "v1.5.1/v1.5 product-flow version mismatch")
    require(quantity["ifc_source"]["sha256"] == mapping["ifc"]["source_sha256"], "v1.5.1/v1.5 IFC source mismatch")
    qi = quantity["ifc_identity"]; mi = mapping["ifc"]; mq = mi["quantity"]
    require(qi["element_global_id"] == mi["element"]["global_id"], "v1.5.1/v1.5 element GlobalId mismatch")
    require(qi["element_step_id"] == mi["element"]["step_id"], "v1.5.1/v1.5 element STEP mismatch")
    require(qi["material_step_id"] == mi["material"]["material_step_id"], "v1.5.1/v1.5 material STEP mismatch")
    require(qi["material_association_step_id"] == mi["material"]["association_step_id"], "v1.5.1/v1.5 material association mismatch")
    require(qi["quantity_step_id"] == mq["quantity_step_id"], "v1.5.1/v1.5 quantity STEP mismatch")
    require(qi["quantity_name"] == mq["name"], "v1.5.1/v1.5 quantity name mismatch")
    require(qi["quantity_entity_type"].upper() == mq["ifc_quantity_type"].upper(), "v1.5.1/v1.5 quantity entity type mismatch")
    require(quantity["quantity"]["mapped_parser_numeric_string"] == str(mq["value"]), "v1.5.1 parser consistency string no longer matches v1.5 mapping")
    declaration = mapping["declaration"]
    require(declaration["closure_content_sha256"] == closure_content, "v1.5 mapping closure-content binding mismatch")
    require(declaration["closure_receipt_sha256"] == closure_receipt_sha, "v1.5 mapping closure-receipt binding mismatch")
    require(declaration["format_version"] == closure["source_identity"]["format_version"] == "1.3", "v1.5/v1.4.1 version lineage mismatch")
    require(declaration["process_dataset_uuid"] == closure["source_identity"]["process_dataset_uuid"], "v1.5/v1.4.1 process UUID mismatch")
    require(declaration["process_xml_sha256"] == closure["source_identity"]["process_xml_sha256"], "v1.5/v1.4.1 process SHA mismatch")
    require(declaration["product_flow_uuid"] == closure["product_flow"]["uuid"], "v1.5/v1.4.1 product-flow UUID mismatch")
    require(declaration["product_flow_version"] == closure["product_flow"]["version"], "v1.5/v1.4.1 product-flow version mismatch")
    require(declaration["product_flow_sha256"] == closure["product_flow"]["sha256"], "v1.5/v1.4.1 product-flow SHA mismatch")
    require(declaration["reference_quantity_decimal"] == closure["declared_reference_basis"]["quantity_decimal"], "v1.5/v1.4.1 reference quantity mismatch")
    require(declaration["reference_unit"] == closure["declared_reference_basis"]["unit"], "v1.5/v1.4.1 reference unit mismatch")
    parent = closure["parent_evidence"]
    require(parent["v14_bundle_content_sha256"] == bundle_content, "v1.4.1 closure/v1.4 bundle content mismatch")
    require(parent["v14_bundle_file_sha256"] == sha256_bytes(bundle_raw), "v1.4.1 closure/v1.4 bundle file mismatch")
    require(parent["v14_bundle_receipt_sha256"] == bundle_receipt_sha, "v1.4.1 closure/v1.4 bundle receipt mismatch")
    require(closure["source_identity"] == bundle["source_identity"], "v1.4.1/v1.4 source identity mismatch")
    require(closure["declared_reference_basis"]["product_flow_uuid"] == bundle["declared_reference_basis"]["product_flow_uuid"], "v1.4.1/v1.4 product-flow UUID mismatch")
    require(closure["declared_reference_basis"]["quantity_decimal"] == bundle["declared_reference_basis"]["quantity_decimal"], "v1.4.1/v1.4 reference quantity mismatch")
    require(closure["declared_reference_basis"]["unit"] == bundle["declared_reference_basis"]["unit"], "v1.4.1/v1.4 reference unit mismatch")


def select_row(bundle: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    results = bundle["environmental_results"]; scope = results.get("indicator_scope", {})
    require(scope.get("code") == selection["indicator_code"], "selected indicator code disagrees with bundle indicator scope")
    require(scope.get("indicator_uuid") == selection["indicator_uuid"], "selected indicator UUID disagrees with bundle indicator scope")
    require(scope.get("canonical_unit") == selection["expected_unit"], "selected environmental unit disagrees with bundle indicator scope")
    rows = results.get("rows"); require(isinstance(rows, list), "v1.4 environmental rows missing")
    matches = [row for row in rows if row.get("indicator_uuid") == selection["indicator_uuid"] and row.get("module") == selection["module"] and exact_scenario_equal(row.get("scenario"), selection["scenario"])]
    require(len(matches) == 1, f"exact row selection must resolve to one row; found {len(matches)}")
    row = matches[0]
    require(row.get("value_origin") == "DECLARED_IN_SOURCE", "selected row is not source-declared")
    require(row.get("calculated") is False, "selected source row is marked calculated")
    require(row.get("unit_conversion_performed") is False, "selected source row already applied unit conversion")
    require(row.get("canonical_unit") == selection["expected_unit"], "selected row environmental unit mismatch")
    lexical = decimal_from_string(row.get("value_lexical"), "selected row lexical value")
    canonical = require_canonical_decimal(row.get("value_decimal"), "selected row Decimal")
    require(lexical == canonical, "selected row lexical/Decimal mismatch")
    return row


def scale(quantity_record_path: Path, quantity_receipt_path: Path, mapping_record_path: Path, mapping_receipt_path: Path, closure_record_path: Path, closure_receipt_path: Path, bundle_path: Path, bundle_receipt_path: Path, request_path: Path) -> dict[str, Any]:
    quantity, quantity_raw = load_json(quantity_record_path); quantity_receipt, quantity_receipt_raw = load_json(quantity_receipt_path)
    mapping, mapping_raw = load_json(mapping_record_path); mapping_receipt, mapping_receipt_raw = load_json(mapping_receipt_path)
    closure, closure_raw = load_json(closure_record_path); closure_receipt, closure_receipt_raw = load_json(closure_receipt_path)
    bundle, bundle_raw = load_json(bundle_path); bundle_receipt, bundle_receipt_raw = load_json(bundle_receipt_path)
    request, request_raw = load_json(request_path)
    validate_schema(request, REQUEST_SCHEMA, "v1.6 request")
    q_content, q_receipt_sha = verify_v151(quantity, quantity_raw, quantity_receipt)
    m_content, m_receipt_sha = verify_v15(mapping, mapping_raw, mapping_receipt)
    c_content, c_receipt_sha = verify_v141(closure, closure_raw, closure_receipt)
    b_content, b_receipt_sha = verify_v14(bundle, bundle_raw, bundle_receipt)
    require(q_content == EXPECTED_V151["content"] and sha256_bytes(quantity_raw) == EXPECTED_V151["file"] and q_receipt_sha == EXPECTED_V151["receipt"], "unaccepted v1.5.1 quantity evidence")
    require(m_content == EXPECTED_V15["content"] and sha256_bytes(mapping_raw) == EXPECTED_V15["file"] and m_receipt_sha == EXPECTED_V15["receipt"], "unaccepted v1.5 mapping evidence")
    require(c_content == EXPECTED_V141["content"] and sha256_bytes(closure_raw) == EXPECTED_V141["file"] and c_receipt_sha == EXPECTED_V141["receipt"], "unaccepted v1.4.1 closure evidence")
    require(b_content == EXPECTED_V14["content"] and sha256_bytes(bundle_raw) == EXPECTED_V14["file"] and b_receipt_sha == EXPECTED_V14["receipt"], "unaccepted v1.4 bundle evidence")
    require(quantity.get("ifc_source", {}).get("sha256") == EXPECTED_IFC_SOURCE_SHA256, "unaccepted IFC source identity")
    verify_lineage(quantity, q_content, q_receipt_sha, mapping, m_content, m_receipt_sha, closure, c_content, closure_raw, c_receipt_sha, bundle, b_content, bundle_raw, b_receipt_sha)
    bindings = request["bindings"]
    actual_bindings = {"quantity_record_content_sha256":q_content,"quantity_record_file_sha256":sha256_bytes(quantity_raw),"quantity_receipt_sha256":q_receipt_sha,"mapping_record_content_sha256":m_content,"mapping_record_file_sha256":sha256_bytes(mapping_raw),"mapping_receipt_sha256":m_receipt_sha,"closure_record_content_sha256":c_content,"closure_record_file_sha256":sha256_bytes(closure_raw),"closure_receipt_sha256":c_receipt_sha,"declaration_bundle_content_sha256":b_content,"declaration_bundle_file_sha256":sha256_bytes(bundle_raw),"declaration_bundle_receipt_sha256":b_receipt_sha}
    require(bindings == actual_bindings, "v1.6 request parent bindings do not exactly match supplied evidence")
    row = select_row(bundle, request["selection"])
    mapped_quantity = require_canonical_decimal(quantity["quantity"]["quantity_decimal"], "source-authoritative mapped quantity", positive=True)
    reference_quantity = require_canonical_decimal(closure["declared_reference_basis"]["quantity_decimal"], "declaration reference quantity", positive=True)
    declared_result = require_canonical_decimal(row["value_decimal"], "selected declared environmental result")
    require(quantity["quantity"]["unit_identity"] == "kg", "mapped quantity unit must be exact kg identity")
    require(closure["declared_reference_basis"]["unit"] == "kg", "declaration reference unit must be exact kg identity")
    with localcontext() as ctx:
        ctx.prec = 100
        scale_factor = mapped_quantity / reference_quantity
        require(scale_factor * reference_quantity == mapped_quantity, "scale-factor division would require rounding under v1.6 exact policy")
        scaled = scale_factor * declared_result
        if scale_factor != 0: require(scaled / scale_factor == declared_result, "scaled result would require rounding under v1.6 exact policy")
    record = {"schema_version":"1.0","record_type":"ProofGridMappedDeclaredResultCalculation","verdict":VERDICT,"calculation_scope":SCOPE,"inputs":{**actual_bindings,"quantity_receipt_file_sha256":sha256_bytes(quantity_receipt_raw),"mapping_receipt_file_sha256":sha256_bytes(mapping_receipt_raw),"closure_receipt_file_sha256":sha256_bytes(closure_receipt_raw),"declaration_bundle_receipt_file_sha256":sha256_bytes(bundle_receipt_raw),"request_file_sha256":sha256_bytes(request_raw),"ifc_source_sha256":quantity["ifc_source"]["sha256"],"element_global_id":quantity["ifc_identity"]["element_global_id"],"quantity_step_id":quantity["ifc_identity"]["quantity_step_id"],"product_flow_uuid":mapping["declaration"]["product_flow_uuid"],"product_flow_version":mapping["declaration"]["product_flow_version"],"process_dataset_uuid":closure["source_identity"]["process_dataset_uuid"],"format_version":closure["source_identity"]["format_version"]},"selection":{"indicator_code":request["selection"]["indicator_code"],"indicator_uuid":request["selection"]["indicator_uuid"],"module":request["selection"]["module"],"scenario":copy.deepcopy(request["selection"]["scenario"]),"source_location":copy.deepcopy(row["source_location"])},"calculation":{"method":METHOD,"version":ENGINE_VERSION,"formula":FORMULA,"mapped_quantity":{"value_lexical":quantity["quantity"]["quantity_lexical"],"value_decimal":canonical_decimal(mapped_quantity),"unit":"kg","source_token_is_authority":True,"parser_numeric_value_is_authority":False},"reference_quantity":{"value_decimal":canonical_decimal(reference_quantity),"unit":"kg","identity_chain_verified":True},"declared_result":{"value_lexical":row["value_lexical"],"value_decimal":row["value_decimal"],"unit":row["canonical_unit"],"value_origin":row["value_origin"],"source_calculated":row["calculated"],"source_unit_conversion_performed":row["unit_conversion_performed"]},"scale_factor_decimal":canonical_decimal(scale_factor),"scaled_result_decimal":canonical_decimal(scaled),"scaled_result_unit":row["canonical_unit"]},"calculation_performed":True,"aggregation_performed":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"fuzzy_mapping_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,"limitations":["This record scales exactly one source-declared environmental row for exactly one accepted mapped quantity/reference basis; it is not a complete building LCA.","The mapped quantity Decimal is sourced from the exact STEP token preserved by v1.5.1; the v1.5 JSON/parser float is never calculation authority.","No module/scenario aggregation, missing-module zeroing, fuzzy mapping, unit conversion, scientific validation, professional review, regulatory approval, or certification is performed."],"integrity":{"content_sha256":ZERO_DIGEST,"canonicalization":CANONICALIZATION,"signature":None}}
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record)); validate_schema(record, RESULT_SCHEMA, "v1.6 result"); return record


def write_outputs(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True); record_path=output_dir/"mapped-declared-result-calculation.json"; receipt_path=output_dir/"mapped-declared-result-calculation-receipt.json"; record_bytes=canonical_pretty_bytes(result); record_path.write_bytes(record_bytes)
    receipt={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"calculation_scope":SCOPE,"record_content_sha256":result["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(record_bytes),"quantity_record_content_sha256":result["inputs"]["quantity_record_content_sha256"],"quantity_receipt_sha256":result["inputs"]["quantity_receipt_sha256"],"mapping_record_content_sha256":result["inputs"]["mapping_record_content_sha256"],"mapping_receipt_sha256":result["inputs"]["mapping_receipt_sha256"],"closure_record_content_sha256":result["inputs"]["closure_record_content_sha256"],"closure_receipt_sha256":result["inputs"]["closure_receipt_sha256"],"declaration_bundle_content_sha256":result["inputs"]["declaration_bundle_content_sha256"],"declaration_bundle_receipt_sha256":result["inputs"]["declaration_bundle_receipt_sha256"],"quantity_lexical":result["calculation"]["mapped_quantity"]["value_lexical"],"quantity_decimal":result["calculation"]["mapped_quantity"]["value_decimal"],"reference_quantity_decimal":result["calculation"]["reference_quantity"]["value_decimal"],"declared_result_decimal":result["calculation"]["declared_result"]["value_decimal"],"scale_factor_decimal":result["calculation"]["scale_factor_decimal"],"scaled_result_decimal":result["calculation"]["scaled_result_decimal"],"scaled_result_unit":result["calculation"]["scaled_result_unit"],"source_token_is_authority":True,"parser_numeric_value_is_authority":False,"calculation_performed":True,"aggregation_performed":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"fuzzy_mapping_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    receipt["receipt_sha256"]=sha256_bytes(canonical_json_bytes(receipt)); receipt_bytes=canonical_pretty_bytes(receipt); receipt_path.write_bytes(receipt_bytes); return {"record":str(record_path),"receipt":str(receipt_path),"record_file_sha256":sha256_bytes(record_bytes),"receipt_file_sha256":sha256_bytes(receipt_bytes),"receipt_sha256":receipt["receipt_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ("quantity-record","quantity-receipt","mapping-record","mapping-receipt","closure-record","closure-receipt","bundle","bundle-receipt","request","output-dir"): parser.add_argument(f"--{flag}",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=scale(args.quantity_record,args.quantity_receipt,args.mapping_record,args.mapping_receipt,args.closure_record,args.closure_receipt,args.bundle,args.bundle_receipt,args.request); outputs=write_outputs(result,args.output_dir)
    except ScalingError as exc:
        print(f"FAILED: {exc}"); return 2
    print(f"RESULT: {VERDICT}"); print(f"SCALE_FACTOR={result['calculation']['scale_factor_decimal']}"); print(f"SCALED_RESULT={result['calculation']['scaled_result_decimal']} {result['calculation']['scaled_result_unit']}"); print(f"RECORD_SHA256={outputs['record_file_sha256']}"); print(f"RECEIPT_SHA256={outputs['receipt_sha256']}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
