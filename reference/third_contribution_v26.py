#!/usr/bin/env python3
"""ProofGrid v2.6 exact Decimal calculation for the remediated third contribution."""
from __future__ import annotations

import argparse, copy, hashlib, json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from reference import mapped_declared_result_scale as v16

ENGINE_NAME = "RegenExcalibur ProofGrid Third Exact Contribution Scaler"
ENGINE_VERSION = "2.6.0"
VERDICT = "THIRD_MAPPED_DECLARED_RESULT_EXACT_DECIMAL_VERIFIABLE"
CANONICALIZATION = v16.CANONICALIZATION
ZERO = "0" * 64

V25 = {
    "content": "483aaf34ea733d798c748b90ae3de7d2bd82e6f00573576432bdcfd0dc9290fb",
    "file": "90763bd8d4564cde98351de2165903796f71ee717f42bdbf06e0daa8ca4cdeaf",
    "receipt": "70f00cf196db5314b1f760f206a479cead4f651d97c384708a654810d311cdfc",
    "receipt_file": "7ae0b31008a9669c90465f8502d6b23d9f638419f1cb51f11174a54a7931eb73",
    "comparison": "73575f19e34c7632fd739edc25add75315b5fa518d1c186c87aa008758d488a5",
    "comparison_file": "a944a963ac5088608f35c0f37c86bdd3996cbee32481f7c71ff9ac1ec4819e60",
}
V24 = {
    "content": "0a9c1e7e8efc6be240315cf04e87904c468b1bb1406f0b1494cb3c0905f37b12",
    "file": "15afb8f3515fa2835729c998a9b661138ffe60737ab8d072fd97f3480a3ec168",
    "receipt": "a0d7e212f35d7a816bdd003d842059d6f7fed806e35cdac327a5042933da57d7",
    "receipt_file": "b9a61248bd7c2068c450a767f243482a83a899e8a80762c965236d82398ef1f0",
    "comparison": "7eecdc11851b7d542968ac6f5015e6f8b4297d5bd972b70c103f9ab051f90ccf",
}
V141 = v16.EXPECTED_V141
V14 = v16.EXPECTED_V14
SOURCE_SHA = "ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d"
ELEMENT_GLOBAL_ID = "1DXL7DJx51bvggyIPU2Xi7"
QUANTITY_DECIMAL = "250"
EXPECTED_DECLARED = "15.559479677163699"
EXPECTED_RESULT = "3889.86991929092475"
PRODUCT_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
PRODUCT_VERSION = "00.00.001"
SELECTION = {"indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","module":"A1-A3","scenario":None,"expected_unit":"kg CO2 eqv."}

class V26Error(ValueError): pass

def require(c: bool, m: str):
    if not c: raise V26Error(m)

def cbytes(v: Any) -> bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v: Any) -> bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def load(path: Path):
    raw=Path(path).read_bytes(); obj=json.loads(raw.decode()); require(isinstance(obj,dict),f"expected object: {path}"); return obj,raw

def verify_self(record,label):
    integ=record.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content hash")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO; require(sha(cbytes(shadow))==claimed,f"{label} content hash mismatch"); return claimed

def verify_receipt(receipt,field,label):
    claimed=receipt.get(field); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {field}"); shadow=copy.deepcopy(receipt); shadow.pop(field,None); require(sha(cbytes(shadow))==claimed,f"{label} digest mismatch"); return claimed

def verify_v25(record,raw,receipt,receipt_raw,comparison,comparison_raw):
    require(record.get("verdict")=="REMEDIATED_INVENTORY_EXPLICIT_ENVIRONMENTAL_MAPPING_VERIFIABLE","wrong v2.5 verdict"); require(verify_self(record,"v2.5 mapping")==V25["content"],"unaccepted v2.5 content"); require(sha(raw)==V25["file"],"unaccepted v2.5 file")
    require(verify_receipt(receipt,"receipt_sha256","v2.5 receipt")==V25["receipt"],"unaccepted v2.5 receipt"); require(sha(receipt_raw)==V25["receipt_file"],"unaccepted v2.5 receipt file")
    require(verify_receipt(comparison,"comparison_receipt_sha256","v2.5 comparison")==V25["comparison"],"unaccepted v2.5 comparison"); require(sha(comparison_raw)==V25["comparison_file"],"unaccepted v2.5 comparison file")
    require(record.get("mapping_state")=="EXPLICIT_REVIEWED_MAPPING","v2.5 mapping not accepted"); require(record.get("source_identity",{}).get("ifc_source_sha256")==SOURCE_SHA and record.get("source_identity",{}).get("element_global_id")==ELEMENT_GLOBAL_ID,"v2.5 source identity mismatch")
    require(record.get("source_identity",{}).get("quantity_decimal")==QUANTITY_DECIMAL,"v2.5 quantity context mismatch"); require(record.get("declaration_identity",{}).get("product_flow_uuid")==PRODUCT_UUID and record.get("declaration_identity",{}).get("product_flow_version")==PRODUCT_VERSION,"v2.5 declaration identity mismatch")
    require(record.get("environmental_mapping_performed") is True and record.get("environmental_source_identity_selected") is True,"v2.5 environmental mapping not proven")
    for k in ("environmental_factor_selected","impact_calculation_performed","assumed_zero","fuzzy_mapping_performed","name_only_mapping_performed","professional_review_performed","scientific_validation_performed","certified"):
        require(record.get(k) is False,f"v2.5 {k} promotion")

def verify_v24(record,raw,receipt,receipt_raw):
    require(record.get("verdict")=="UNCOVERED_INVENTORY_REMEDIATION_READY_FOR_MAPPING_VERIFIABLE","wrong v2.4 verdict"); require(verify_self(record,"v2.4 readiness")==V24["content"],"unaccepted v2.4 content"); require(sha(raw)==V24["file"],"unaccepted v2.4 file")
    require(verify_receipt(receipt,"receipt_sha256","v2.4 receipt")==V24["receipt"],"unaccepted v2.4 receipt"); require(sha(receipt_raw)==V24["receipt_file"],"unaccepted v2.4 receipt file")
    q=record.get("quantity_evidence",{}); require(q.get("quantity_decimal")==QUANTITY_DECIMAL,"v2.4 quantity mismatch"); require(q.get("source_token_is_authority") is True and q.get("parser_numeric_value_is_authority") is False,"v2.4 quantity authority mismatch"); require(q.get("unit")=="kg","v2.4 quantity unit mismatch")
    require(record.get("successor_source",{}).get("successor_source_sha256")==SOURCE_SHA and record.get("successor_source",{}).get("element_global_id")==ELEMENT_GLOBAL_ID,"v2.4 source identity mismatch")
    return q

def verify_declaration(closure,closure_raw,closure_receipt,bundle,bundle_raw,bundle_receipt):
    try:
        c_content,c_receipt=v16.verify_v141(closure,closure_raw,closure_receipt); b_content,b_receipt=v16.verify_v14(bundle,bundle_raw,bundle_receipt)
    except v16.ScalingError as exc: raise V26Error(str(exc)) from exc
    require(c_content==V141["content"] and sha(closure_raw)==V141["file"] and c_receipt==V141["receipt"],"unaccepted v1.4.1 parent")
    require(b_content==V14["content"] and sha(bundle_raw)==V14["file"] and b_receipt==V14["receipt"],"unaccepted v1.4 parent")
    require(closure.get("product_flow",{}).get("uuid")==PRODUCT_UUID and closure.get("product_flow",{}).get("version")==PRODUCT_VERSION,"declaration product identity mismatch")
    require(closure.get("declared_reference_basis",{}).get("quantity_decimal")=="1" and closure.get("declared_reference_basis",{}).get("unit")=="kg","reference basis mismatch")
    return c_content,c_receipt,b_content,b_receipt

def validate_record(r):
    require(r.get("verdict")==VERDICT,"wrong verdict"); require(r.get("calculation_scope")=="SINGLE_MAPPED_DECLARED_RESULT_ROW","wrong scope"); require(r.get("impact_calculation_performed") is True,"calculation not performed")
    require(r.get("environmental_mapping_verified") is True and r.get("source_declared_result_selected") is True,"mapping/source row not verified")
    require(r.get("calculation",{}).get("scaled_result_decimal")==EXPECTED_RESULT,"result mismatch"); require(r.get("calculation",{}).get("scaled_result_unit")=="kg CO2 eqv.","result unit mismatch")
    require(r.get("environmental_coverage_status")=="CALCULATED_CONTRIBUTION_NOT_YET_ADMITTED","coverage state mismatch")
    for k in ("rxep_binding_performed","contribution_set_admission_performed","aggregate_recomputed","whole_building_completeness_evaluated","scientific_validation_performed","professional_review_performed","certified"):
        require(r.get(k) is False,f"{k} promotion rejected")
    require(r.get("unit_conversion_performed") is False and r.get("scenario_inference_performed") is False,"conversion/inference rejected")

def calculate(v25p,v25rp,v25cp,v24p,v24rp,closurep,closurerp,bundlep,bundlerp):
    v25,v25raw=load(v25p); v25r,v25rraw=load(v25rp); v25c,v25craw=load(v25cp); verify_v25(v25,v25raw,v25r,v25rraw,v25c,v25craw)
    v24,v24raw=load(v24p); v24r,v24rraw=load(v24rp); q=verify_v24(v24,v24raw,v24r,v24rraw)
    closure,closure_raw=load(closurep); closurer,_=load(closurerp); bundle,bundle_raw=load(bundlep); bundler,_=load(bundlerp); c_content,c_receipt,b_content,b_receipt=verify_declaration(closure,closure_raw,closurer,bundle,bundle_raw,bundler)
    try: row=v16.select_row(bundle,SELECTION)
    except v16.ScalingError as exc: raise V26Error(str(exc)) from exc
    require(row.get("value_decimal")==EXPECTED_DECLARED and row.get("canonical_unit")=="kg CO2 eqv.","selected declaration row mismatch")
    mapped=Decimal(q["quantity_decimal"]); lexical=Decimal(q["quantity_lexical"]); ref=Decimal(closure["declared_reference_basis"]["quantity_decimal"]); declared=Decimal(row["value_decimal"]); require(mapped==lexical==Decimal("250"),"exact quantity mismatch")
    with localcontext() as ctx:
        ctx.prec=100; factor=mapped/ref; require(factor*ref==mapped,"hidden quantity rounding"); scaled=factor*declared; require(scaled/factor==declared,"hidden result rounding")
    scaled_text=v16.canonical_decimal(scaled); require(scaled_text==EXPECTED_RESULT,f"unexpected third result: {scaled_text}")
    r={"schema_version":"1.0","record_type":"ProofGridThirdMappedDeclaredResultCalculation","verdict":VERDICT,"calculation_scope":"SINGLE_MAPPED_DECLARED_RESULT_ROW",
       "inputs":{"v25_mapping_content_sha256":V25["content"],"v25_mapping_receipt_sha256":V25["receipt"],"v25_comparison_receipt_sha256":V25["comparison"],"v24_readiness_content_sha256":V24["content"],"ifc_source_sha256":SOURCE_SHA,"element_global_id":ELEMENT_GLOBAL_ID,"closure_content_sha256":c_content,"closure_receipt_sha256":c_receipt,"declaration_bundle_content_sha256":b_content,"declaration_bundle_receipt_sha256":b_receipt,"product_flow_uuid":PRODUCT_UUID,"product_flow_version":PRODUCT_VERSION},
       "selection":{"indicator_code":SELECTION["indicator_code"],"indicator_uuid":SELECTION["indicator_uuid"],"module":"A1-A3","scenario":None,"source_location":copy.deepcopy(row["source_location"])},
       "calculation":{"method":v16.METHOD,"formula":v16.FORMULA,"mapped_quantity":{"value_lexical":q["quantity_lexical"],"value_decimal":"250","unit":"kg","source_token_is_authority":True,"parser_numeric_value_is_authority":False},"reference_quantity":{"value_decimal":"1","unit":"kg"},"declared_result":{"value_lexical":row["value_lexical"],"value_decimal":EXPECTED_DECLARED,"unit":"kg CO2 eqv.","value_origin":"DECLARED_IN_SOURCE","source_calculated":False},"scale_factor_decimal":"250","scaled_result_decimal":scaled_text,"scaled_result_unit":"kg CO2 eqv."},
       "impact_calculation_performed":True,"environmental_mapping_verified":True,"source_declared_result_selected":True,"environmental_coverage_status":"CALCULATED_CONTRIBUTION_NOT_YET_ADMITTED","rxep_binding_performed":False,"contribution_set_admission_performed":False,"aggregate_recomputed":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"whole_building_completeness_evaluated":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
       "limitations":["This is one exact calculated third contribution only; it is not yet admitted into RXEP or the contribution set.","No aggregate or whole-building completeness state is recomputed in this gate.","Exact STEP Decimal and exact source-declared Decimal are arithmetic authority; binary float is not authority."],"integrity":{"content_sha256":ZERO,"canonicalization":CANONICALIZATION,"signature":None}}
    r["integrity"]["content_sha256"]=sha(cbytes(r)); validate_record(r); return r

def make_receipt(r,raw):
    out={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"record_content_sha256":r["integrity"]["content_sha256"],"record_file_sha256":sha(raw),"element_global_id":ELEMENT_GLOBAL_ID,"ifc_source_sha256":SOURCE_SHA,"quantity_lexical":r["calculation"]["mapped_quantity"]["value_lexical"],"quantity_decimal":"250","declared_result_decimal":EXPECTED_DECLARED,"scaled_result_decimal":EXPECTED_RESULT,"scaled_result_unit":"kg CO2 eqv.","impact_calculation_performed":True,"environmental_coverage_status":"CALCULATED_CONTRIBUTION_NOT_YET_ADMITTED","rxep_binding_performed":False,"contribution_set_admission_performed":False,"aggregate_recomputed":False,"certified":False}
    out["receipt_sha256"]=sha(cbytes(out)); return out

def main(argv=None):
    p=argparse.ArgumentParser()
    for n in ("v25-mapping","v25-receipt","v25-comparison","v24-readiness","v24-receipt","closure","closure-receipt","bundle","bundle-receipt","output-dir"): p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args(argv)
    try:
      r=calculate(a.v25_mapping,a.v25_receipt,a.v25_comparison,a.v24_readiness,a.v24_receipt,a.closure,a.closure_receipt,a.bundle,a.bundle_receipt); a.output_dir.mkdir(parents=True,exist_ok=True); raw=pbytes(r); (a.output_dir/"third-mapped-declared-result-calculation.json").write_bytes(raw); rr=make_receipt(r,raw); (a.output_dir/"third-mapped-declared-result-calculation-receipt.json").write_bytes(pbytes(rr)); print(json.dumps(rr,indent=2,sort_keys=True)); return 0
    except Exception as exc: print("FAILED:",exc); return 2
if __name__=="__main__": raise SystemExit(main())
