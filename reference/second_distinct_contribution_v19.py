#!/usr/bin/env python3
"""ProofGrid v1.9 dedicated second-distinct-contribution control.

This module deliberately does not weaken the hard-pinned first v1.6/v1.7 path.
It creates one separately bounded second synthetic contribution from:
  generic v1.5 mapping -> generic v1.5.1 exact STEP Decimal
  -> accepted v1.4.1/v1.4 declaration lineage
  -> one exact GWP-total/A1-A3/scenario=null row
  -> Decimal-only scaling
  -> RXEP CALCULATED envelope after two-replica reproduction.

No set summation, aggregation, unit conversion, scientific validation,
professional review, regulatory approval, or certification is performed.
"""
from __future__ import annotations

import argparse, copy, hashlib, json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from reference import mapped_declared_result_scale as v16
from reference import rxep_calculated_contribution as v17

ENGINE_NAME = "RegenExcalibur ProofGrid Second Distinct Contribution Control"
ENGINE_VERSION = "1.9.0"
CALC_VERDICT = v16.VERDICT
RXEP_VERDICT = v17.VERDICT
REPRO_VERDICT = "SECOND_DISTINCT_CONTRIBUTION_INDEPENDENTLY_REPRODUCED"
SECOND_ELEMENT_GLOBAL_ID = "1CXL7DJx51bvggyIPU2Xi6"
SECOND_MAPPING_ID = "rx-v19-second-explicit-mapping"
SECOND_QUANTITY_DECIMAL = "500"
EXPECTED_RESULT_DECIMAL = "7779.7398385818495"
EXPECTED_PRODUCT_FLOW_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
EXPECTED_PRODUCT_FLOW_VERSION = "00.00.001"
EXPECTED_V141 = {"content":"cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd","file":"9cdba7a6e512ecaa1d1c5320c1fac55d7e9ad8a74f7cf2a66c75204dd390eca6","receipt":"27abef64ed6e86fb8f555a4b42c9a67f14e74fec584d8c4496446abfd0009921"}
EXPECTED_V14 = {"content":"8e71852027be10c4120f6185e0ae90127da9c72bf1e64f5c50b08442ed2c0aa0","file":"70b03882bda92680851b48b39091dcdb20a4b386a5f3b2b712e8d08d054d359a","receipt":"ac3f22efd3220e7c3e323c3178421af4b45d54c9e6ac5f158c76c6db3422ed84"}
SELECTION = {"indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","module":"A1-A3","scenario":None,"expected_unit":"kg CO2 eqv."}
ZERO_DIGEST = "0" * 64
CANONICALIZATION = v16.CANONICALIZATION

class SecondContributionError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SecondContributionError(message)

def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = Path(path).read_bytes()
    value = json.loads(raw.decode("utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw

def verify_second_lineage(quantity, quantity_raw, quantity_receipt, mapping, mapping_raw, mapping_receipt, closure, closure_raw, closure_receipt, bundle, bundle_raw, bundle_receipt):
    try:
        q_content, q_receipt_sha = v16.verify_v151(quantity, quantity_raw, quantity_receipt)
        m_content, m_receipt_sha = v16.verify_v15(mapping, mapping_raw, mapping_receipt)
        c_content, c_receipt_sha = v16.verify_v141(closure, closure_raw, closure_receipt)
        b_content, b_receipt_sha = v16.verify_v14(bundle, bundle_raw, bundle_receipt)
    except v16.ScalingError as exc:
        raise SecondContributionError(str(exc)) from exc
    require(c_content == EXPECTED_V141["content"] and sha256_bytes(closure_raw) == EXPECTED_V141["file"] and c_receipt_sha == EXPECTED_V141["receipt"], "unaccepted v1.4.1 parent")
    require(b_content == EXPECTED_V14["content"] and sha256_bytes(bundle_raw) == EXPECTED_V14["file"] and b_receipt_sha == EXPECTED_V14["receipt"], "unaccepted v1.4 parent")
    require(mapping.get("mapping_id") == SECOND_MAPPING_ID, "second mapping ID mismatch")
    require(mapping.get("ifc", {}).get("element", {}).get("global_id") == SECOND_ELEMENT_GLOBAL_ID, "second element GlobalId mismatch")
    require(quantity.get("ifc_identity", {}).get("element_global_id") == SECOND_ELEMENT_GLOBAL_ID, "second quantity element GlobalId mismatch")
    require(quantity.get("quantity", {}).get("quantity_decimal") == SECOND_QUANTITY_DECIMAL, "second quantity Decimal mismatch")
    require(quantity.get("quantity", {}).get("source_token_is_authority") is True, "source STEP token must be quantity authority")
    require(quantity.get("quantity", {}).get("parser_numeric_value_is_authority") is False, "parser numeric value cannot be quantity authority")
    require(mapping.get("declaration", {}).get("product_flow_uuid") == EXPECTED_PRODUCT_FLOW_UUID, "second mapping product-flow UUID mismatch")
    require(mapping.get("declaration", {}).get("product_flow_version") == EXPECTED_PRODUCT_FLOW_VERSION, "second mapping product-flow version mismatch")
    try:
        v16.verify_lineage(quantity, q_content, q_receipt_sha, mapping, m_content, m_receipt_sha, closure, c_content, closure_raw, c_receipt_sha, bundle, b_content, bundle_raw, b_receipt_sha)
    except v16.ScalingError as exc:
        raise SecondContributionError(str(exc)) from exc
    return q_content, q_receipt_sha, m_content, m_receipt_sha, c_content, c_receipt_sha, b_content, b_receipt_sha

def calculate(quantity_record: Path, quantity_receipt: Path, mapping_record: Path, mapping_receipt: Path, closure_record: Path, closure_receipt: Path, bundle_path: Path, bundle_receipt: Path) -> dict[str, Any]:
    quantity, quantity_raw = load_json(quantity_record); q_receipt, q_receipt_raw = load_json(quantity_receipt)
    mapping, mapping_raw = load_json(mapping_record); m_receipt, m_receipt_raw = load_json(mapping_receipt)
    closure, closure_raw = load_json(closure_record); c_receipt, c_receipt_raw = load_json(closure_receipt)
    bundle, bundle_raw = load_json(bundle_path); b_receipt, b_receipt_raw = load_json(bundle_receipt)
    q_content, q_receipt_sha, m_content, m_receipt_sha, c_content, c_receipt_sha, b_content, b_receipt_sha = verify_second_lineage(quantity, quantity_raw, q_receipt, mapping, mapping_raw, m_receipt, closure, closure_raw, c_receipt, bundle, bundle_raw, b_receipt)
    try:
        row = v16.select_row(bundle, SELECTION)
    except v16.ScalingError as exc:
        raise SecondContributionError(str(exc)) from exc
    mapped = Decimal(quantity["quantity"]["quantity_decimal"]); reference = Decimal(closure["declared_reference_basis"]["quantity_decimal"]); declared = Decimal(row["value_decimal"])
    require(mapped == Decimal("500"), "second quantity must be exactly 500 kg")
    require(reference == Decimal("1"), "reference quantity must be exactly 1 kg")
    with localcontext() as ctx:
        ctx.prec = 100
        factor = mapped / reference
        require(factor * reference == mapped, "scale factor requires rounding")
        scaled = factor * declared
        require(scaled / factor == declared, "scaled result requires rounding")
    scaled_text = v16.canonical_decimal(scaled)
    require(scaled_text == EXPECTED_RESULT_DECIMAL, f"unexpected second result: {scaled_text}")
    inputs = {
        "quantity_record_content_sha256": q_content, "quantity_record_file_sha256": sha256_bytes(quantity_raw), "quantity_receipt_sha256": q_receipt_sha, "quantity_receipt_file_sha256": sha256_bytes(q_receipt_raw),
        "mapping_record_content_sha256": m_content, "mapping_record_file_sha256": sha256_bytes(mapping_raw), "mapping_receipt_sha256": m_receipt_sha, "mapping_receipt_file_sha256": sha256_bytes(m_receipt_raw),
        "closure_record_content_sha256": c_content, "closure_record_file_sha256": sha256_bytes(closure_raw), "closure_receipt_sha256": c_receipt_sha, "closure_receipt_file_sha256": sha256_bytes(c_receipt_raw),
        "declaration_bundle_content_sha256": b_content, "declaration_bundle_file_sha256": sha256_bytes(bundle_raw), "declaration_bundle_receipt_sha256": b_receipt_sha, "declaration_bundle_receipt_file_sha256": sha256_bytes(b_receipt_raw),
        "ifc_source_sha256": quantity["ifc_source"]["sha256"], "element_global_id": SECOND_ELEMENT_GLOBAL_ID, "quantity_step_id": quantity["ifc_identity"]["quantity_step_id"],
        "product_flow_uuid": EXPECTED_PRODUCT_FLOW_UUID, "product_flow_version": EXPECTED_PRODUCT_FLOW_VERSION, "process_dataset_uuid": closure["source_identity"]["process_dataset_uuid"], "format_version": "1.3"
    }
    record = {
        "schema_version":"1.0", "record_type":"ProofGridMappedDeclaredResultCalculation", "verdict":CALC_VERDICT, "calculation_scope":"SINGLE_MAPPED_DECLARED_RESULT_ROW",
        "inputs":inputs,
        "selection":{"indicator_code":SELECTION["indicator_code"], "indicator_uuid":SELECTION["indicator_uuid"], "module":"A1-A3", "scenario":None, "source_location":copy.deepcopy(row["source_location"])},
        "calculation":{"method":v16.METHOD, "version":"1.6.0", "formula":v16.FORMULA, "mapped_quantity":{"value_lexical":quantity["quantity"]["quantity_lexical"], "value_decimal":"500", "unit":"kg", "source_token_is_authority":True, "parser_numeric_value_is_authority":False}, "reference_quantity":{"value_decimal":"1", "unit":"kg", "identity_chain_verified":True}, "declared_result":{"value_lexical":row["value_lexical"], "value_decimal":row["value_decimal"], "unit":row["canonical_unit"], "value_origin":"DECLARED_IN_SOURCE", "source_calculated":False, "source_unit_conversion_performed":False}, "scale_factor_decimal":"500", "scaled_result_decimal":scaled_text, "scaled_result_unit":row["canonical_unit"]},
        "calculation_performed":True, "aggregation_performed":False, "missing_modules_are_zero":False, "unit_conversion_performed":False, "scenario_inference_performed":False, "fuzzy_mapping_performed":False, "scientific_validation_performed":False, "professional_review_performed":False, "certified":False,
        "limitations":["Dedicated synthetic second contribution for v1.9; no complete-building-LCA claim.", "Exact STEP Decimal is arithmetic authority; parser float is consistency evidence only.", "No aggregation, unit conversion, scenario inference, scientific validation, professional review, regulatory approval, or certification is performed."],
        "integrity":{"content_sha256":ZERO_DIGEST, "canonicalization":CANONICALIZATION, "signature":None}
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    try:
        v16.validate_schema(record, v16.RESULT_SCHEMA, "v1.9 second calculation")
    except v16.ScalingError as exc:
        raise SecondContributionError(str(exc)) from exc
    return record

def calculation_receipt(record: dict[str, Any], raw: bytes) -> dict[str, Any]:
    receipt = {"verdict":CALC_VERDICT, "engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION}, "calculation_scope":"SINGLE_MAPPED_DECLARED_RESULT_ROW", "record_content_sha256":record["integrity"]["content_sha256"], "record_file_sha256":sha256_bytes(raw), "quantity_record_content_sha256":record["inputs"]["quantity_record_content_sha256"], "mapping_record_content_sha256":record["inputs"]["mapping_record_content_sha256"], "closure_record_content_sha256":record["inputs"]["closure_record_content_sha256"], "declaration_bundle_content_sha256":record["inputs"]["declaration_bundle_content_sha256"], "quantity_lexical":record["calculation"]["mapped_quantity"]["value_lexical"], "quantity_decimal":"500", "scaled_result_decimal":EXPECTED_RESULT_DECIMAL, "scaled_result_unit":"kg CO2 eqv.", "source_token_is_authority":True, "parser_numeric_value_is_authority":False, "calculation_performed":True, "aggregation_performed":False, "missing_modules_are_zero":False, "unit_conversion_performed":False, "scenario_inference_performed":False, "fuzzy_mapping_performed":False, "scientific_validation_performed":False, "professional_review_performed":False, "certified":False}
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt

def verify_reproduction(reproduction: dict[str, Any], calc: dict[str, Any], calc_raw: bytes, receipt: dict[str, Any], receipt_raw: bytes) -> None:
    claimed = reproduction.get("receipt_sha256"); require(isinstance(claimed, str) and len(claimed) == 64, "reproduction receipt missing SHA")
    shadow = dict(reproduction); shadow.pop("receipt_sha256", None); require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, "reproduction receipt digest mismatch")
    require(reproduction.get("verdict") == REPRO_VERDICT, "wrong reproduction verdict")
    require(reproduction.get("independent_runner_count") == 2 and reproduction.get("byte_identical") is True, "independent reproduction not proven")
    require(reproduction.get("calculation_record_content_sha256") == calc["integrity"]["content_sha256"], "reproduction/calculation content mismatch")
    require(reproduction.get("calculation_record_file_sha256") == sha256_bytes(calc_raw), "reproduction/calculation file mismatch")
    require(reproduction.get("calculation_receipt_sha256") == receipt["receipt_sha256"], "reproduction/calculation receipt mismatch")
    require(reproduction.get("calculation_receipt_file_sha256") == sha256_bytes(receipt_raw), "reproduction/calculation receipt file mismatch")
    require(reproduction.get("scaled_result_decimal") == EXPECTED_RESULT_DECIMAL, "reproduction result mismatch")
    require(reproduction.get("certified") is False, "reproduction certification promotion rejected")

def bind_rxep(calculation_path: Path, receipt_path: Path, reproduction_path: Path) -> dict[str, Any]:
    calc, calc_raw = load_json(calculation_path); receipt, receipt_raw = load_json(receipt_path); reproduction, reproduction_raw = load_json(reproduction_path)
    try:
        content = v16.verify_record(calc, calc_raw, expected_verdict=CALC_VERDICT, label="second calculation")
        receipt_sha = v16.verify_receipt(receipt, expected_verdict=CALC_VERDICT, label="second calculation receipt", record_content_sha256=content, record_file_sha256=sha256_bytes(calc_raw))
    except v16.ScalingError as exc:
        raise SecondContributionError(str(exc)) from exc
    require(calc["inputs"]["element_global_id"] == SECOND_ELEMENT_GLOBAL_ID, "second RXEP element mismatch")
    require(calc["calculation"]["mapped_quantity"]["value_decimal"] == "500", "second RXEP quantity mismatch")
    require(calc["calculation"]["scaled_result_decimal"] == EXPECTED_RESULT_DECIMAL, "second RXEP result mismatch")
    verify_reproduction(reproduction, calc, calc_raw, receipt, receipt_raw)
    envelope = {
        "id":f"rxep:v19-second:{content}",
        "subject":{"id":SECOND_ELEMENT_GLOBAL_ID,"type":"ifc-declaration-environmental-contribution","name":"Second distinct exact mapped IFC declared environmental contribution"},
        "claim":{"type":"scaled_declared_environmental_contribution","statement":"A second distinct synthetic IFC quantity was independently mapped and scaled against one exact source-declared environmental result row."},
        "measurement":{"value":float(Decimal(EXPECTED_RESULT_DECIMAL)),"value_decimal":EXPECTED_RESULT_DECIMAL,"decimal_value_is_authority":True,"numeric_value_is_authority":False,"numeric_value_role":"NON_AUTHORITATIVE_DISPLAY","unit":"kg CO2 eqv.","indicator_code":"GWP-total","indicator_uuid":SELECTION["indicator_uuid"],"module":"A1-A3","scenario":None},
        "methodology":{"name":v16.METHOD,"version":"1.6.0","formula":v16.FORMULA,"calculation_scope":"SINGLE_MAPPED_DECLARED_RESULT_ROW"},
        "sources":[{"path":"v19-second/mapped-declared-result-calculation.json","sha256":sha256_bytes(calc_raw),"kind":"calculation-record","content_sha256":content},{"path":"v19-second/mapped-declared-result-calculation-receipt.json","sha256":sha256_bytes(receipt_raw),"kind":"calculation-receipt","receipt_sha256":receipt_sha},{"path":"v19-second/v19-second-independent-reproduction-receipt.json","sha256":sha256_bytes(reproduction_raw),"kind":"software-reproduction-receipt","receipt_sha256":reproduction["receipt_sha256"]}],
        "software":{"name":ENGINE_NAME,"version":ENGINE_VERSION}, "jurisdiction":"UNSPECIFIED_SYNTHETIC_TEST_CONTEXT", "review":{"state":"CALCULATED","reviewer":None},
        "limitations":["Independent reproduction applies to software calculation/canonical bytes only; environmental claim remains CALCULATED.","This is the second distinct synthetic contribution, not a complete building LCA.","No aggregation, unit conversion, scientific validation, professional review, regulatory approval, or certification is performed."],
        "aggregation_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
        "software_reproduction":{"independent_runner_count":2,"byte_identical":True,"comparison_receipt_sha256":reproduction["receipt_sha256"]},
        "integrity":{"content_sha256":ZERO_DIGEST,"canonicalization":CANONICALIZATION,"signature":None}
    }
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    try:
        v17.validate_rxep(envelope)
    except v17.RXEPContributionError as exc:
        raise SecondContributionError(str(exc)) from exc
    require(envelope["review"] == {"state":"CALCULATED","reviewer":None}, "second RXEP review promotion")
    return envelope

def rxep_receipt(envelope: dict[str, Any], raw: bytes, calc: dict[str, Any], calc_receipt: dict[str, Any], reproduction: dict[str, Any]) -> dict[str, Any]:
    receipt = {"verdict":RXEP_VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"review_state":"CALCULATED","record_content_sha256":envelope["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw),"value_decimal":EXPECTED_RESULT_DECIMAL,"unit":"kg CO2 eqv.","v16_record_content_sha256":calc["integrity"]["content_sha256"],"v16_calculation_receipt_sha256":calc_receipt["receipt_sha256"],"v161_comparison_receipt_sha256":reproduction["receipt_sha256"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"aggregation_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="cmd", required=True)
    calc = sub.add_parser("calculate")
    for flag in ("quantity-record","quantity-receipt","mapping-record","mapping-receipt","closure-record","closure-receipt","bundle","bundle-receipt","output-dir"):
        calc.add_argument("--"+flag, type=Path, required=True)
    bind = sub.add_parser("bind-rxep")
    for flag in ("calculation-record","calculation-receipt","reproduction-receipt","output-dir"):
        bind.add_argument("--"+flag, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "calculate":
            record = calculate(args.quantity_record,args.quantity_receipt,args.mapping_record,args.mapping_receipt,args.closure_record,args.closure_receipt,args.bundle,args.bundle_receipt)
            args.output_dir.mkdir(parents=True, exist_ok=True); raw = pretty_json_bytes(record); (args.output_dir/"mapped-declared-result-calculation.json").write_bytes(raw)
            receipt = calculation_receipt(record, raw); (args.output_dir/"mapped-declared-result-calculation-receipt.json").write_bytes(pretty_json_bytes(receipt))
            print("RESULT:", CALC_VERDICT); print("SECOND EXACT RESULT:", EXPECTED_RESULT_DECIMAL)
        else:
            calc_record, calc_raw = load_json(args.calculation_record); calc_receipt, calc_receipt_raw = load_json(args.calculation_receipt); reproduction, _ = load_json(args.reproduction_receipt)
            envelope = bind_rxep(args.calculation_record,args.calculation_receipt,args.reproduction_receipt)
            args.output_dir.mkdir(parents=True, exist_ok=True); raw = pretty_json_bytes(envelope); (args.output_dir/"rxep-exact-decimal-calculated-contribution.json").write_bytes(raw)
            receipt = rxep_receipt(envelope, raw, calc_record, calc_receipt, reproduction); (args.output_dir/"rxep-exact-decimal-calculated-contribution-receipt.json").write_bytes(pretty_json_bytes(receipt))
            print("RESULT:", RXEP_VERDICT); print("SECOND RXEP EXACT DECIMAL:", EXPECTED_RESULT_DECIMAL)
        return 0
    except Exception as exc:
        print("FAILED:", exc)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
