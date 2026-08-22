#!/usr/bin/env python3
"""ProofGrid v2.5 explicit reviewed mapping for the remediated uncovered element.

This gate binds the accepted v2.4 successor source/material/quantity identities to
one accepted v1.4.1 declaration product identity through an explicit synthetic
REVIEWED_MAPPING_DECISION. No environmental factor is selected and no impact
calculation is performed.
"""
from __future__ import annotations

import argparse, copy, hashlib, json
from pathlib import Path
from typing import Any

from adapters.ifc.extract import extract_ifc_declared_data
from reference import ifc_declaration_product_map as v15

ENGINE_NAME = "RegenExcalibur ProofGrid Remediated Explicit Mapping Binder"
ENGINE_VERSION = "2.5.0"
VERDICT = "REMEDIATED_INVENTORY_EXPLICIT_ENVIRONMENTAL_MAPPING_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO = "0" * 64

V24 = {
    "record_content": "0a9c1e7e8efc6be240315cf04e87904c468b1bb1406f0b1494cb3c0905f37b12",
    "record_file": "15afb8f3515fa2835729c998a9b661138ffe60737ab8d072fd97f3480a3ec168",
    "receipt": "a0d7e212f35d7a816bdd003d842059d6f7fed806e35cdac327a5042933da57d7",
    "receipt_file": "b9a61248bd7c2068c450a767f243482a83a899e8a80762c965236d82398ef1f0",
    "comparison": "7eecdc11851b7d542968ac6f5015e6f8b4297d5bd972b70c103f9ab051f90ccf",
}
SUCCESSOR_SOURCE_SHA = "ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d"
ELEMENT_GLOBAL_ID = "1DXL7DJx51bvggyIPU2Xi7"
MATERIAL_NAME = "RX-MATERIAL-THIRD-REMEDIATION-CONTROL"
MATERIAL_ASSOCIATION_STEP_ID = 6
MATERIAL_STEP_ID = 5
QUANTITY_SET_STEP_ID = 8
QUANTITY_STEP_ID = 7
QUANTITY_DECIMAL = "250"

V141 = {
    "content": "cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd",
    "file": "9cdba7a6e512ecaa1d1c5320c1fac55d7e9ad8a74f7cf2a66c75204dd390eca6",
    "receipt": "27abef64ed6e86fb8f555a4b42c9a67f14e74fec584d8c4496446abfd0009921",
    "product_flow_uuid": "a7432abd-0881-4977-a817-f8aaf627fb91",
    "product_flow_version": "00.00.001",
}

class MappingV25Error(ValueError): pass

def require(c: bool, m: str) -> None:
    if not c: raise MappingV25Error(m)

def cbytes(v: Any) -> bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v: Any) -> bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def load(path: Path):
    raw=Path(path).read_bytes(); obj=json.loads(raw.decode()); require(isinstance(obj,dict),f"expected object: {path}"); return obj,raw

def verify_self(record,label):
    integ=record.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content hash")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO; require(sha(cbytes(shadow))==claimed,f"{label} content digest mismatch"); return claimed

def verify_receipt(receipt,field,label):
    claimed=receipt.get(field); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {field}"); shadow=copy.deepcopy(receipt); shadow.pop(field,None); require(sha(cbytes(shadow))==claimed,f"{label} digest mismatch"); return claimed

def verify_v24(record,record_raw,receipt,receipt_raw,comparison):
    require(record.get("verdict")=="UNCOVERED_INVENTORY_REMEDIATION_READY_FOR_MAPPING_VERIFIABLE","wrong v2.4 verdict")
    require(verify_self(record,"v2.4 record")==V24["record_content"],"unaccepted v2.4 content"); require(sha(record_raw)==V24["record_file"],"unaccepted v2.4 file")
    require(verify_receipt(receipt,"receipt_sha256","v2.4 receipt")==V24["receipt"],"unaccepted v2.4 receipt"); require(sha(receipt_raw)==V24["receipt_file"],"unaccepted v2.4 receipt file")
    require(verify_receipt(comparison,"comparison_receipt_sha256","v2.4 comparison")==V24["comparison"],"unaccepted v2.4 comparison")
    require(record.get("remediation_state")=="READY_FOR_EXPLICIT_MAPPING","v2.4 readiness lost"); require(record.get("environmental_coverage_status")=="EVIDENCE_UNCOVERED","v2.4 coverage promotion")
    s=record.get("successor_source",{}); require(s.get("successor_source_sha256")==SUCCESSOR_SOURCE_SHA,"v2.4 successor source mismatch"); require(s.get("element_global_id")==ELEMENT_GLOBAL_ID,"v2.4 element mismatch")
    m=record.get("material_evidence",{}); q=record.get("quantity_evidence",{})
    require(m.get("association_step_id")==MATERIAL_ASSOCIATION_STEP_ID and m.get("material_step_id")==MATERIAL_STEP_ID and m.get("declared_name")==MATERIAL_NAME,"v2.4 material identity mismatch")
    require(q.get("set_step_id")==QUANTITY_SET_STEP_ID and q.get("quantity_step_id")==QUANTITY_STEP_ID and q.get("quantity_decimal")==QUANTITY_DECIMAL,"v2.4 quantity identity mismatch")
    require(q.get("source_token_is_authority") is True and q.get("parser_numeric_value_is_authority") is False,"v2.4 quantity authority mismatch")
    for k in ("environmental_mapping_performed","environmental_factor_selected","impact_calculation_performed","assumed_zero","professional_review_performed","scientific_validation_performed","certified"):
        require(record.get(k) is False,f"v2.4 {k} promotion")

def verify_successor(path: Path):
    raw=path.read_bytes(); require(sha(raw)==SUCCESSOR_SOURCE_SHA,"unaccepted successor IFC bytes")
    ex=extract_ifc_declared_data(path); require(ex.get("source_sha256")==SUCCESSOR_SOURCE_SHA,"successor extraction source mismatch")
    elems=[e for e in ex.get("elements",[]) if e.get("global_id")==ELEMENT_GLOBAL_ID]; require(len(elems)==1,"expected one remediated element"); e=elems[0]
    require(len(e.get("materials",[]))==1 and len(e.get("quantities",[]))==1,"ambiguous remediated material/quantity evidence")
    m=e["materials"][0]; q=e["quantities"][0]
    require(m.get("association_step_id")==MATERIAL_ASSOCIATION_STEP_ID and m.get("material_step_id")==MATERIAL_STEP_ID and m.get("name")==MATERIAL_NAME,"successor material mismatch")
    require(q.get("set_step_id")==QUANTITY_SET_STEP_ID and q.get("quantity_step_id")==QUANTITY_STEP_ID and q.get("ifc_quantity_type")=="IfcQuantityWeight","successor quantity mismatch")
    return ex,e,m,q

def verify_closure(path: Path, receipt_path: Path):
    record,raw=v15.load_json(path); receipt,_=v15.load_json(receipt_path)
    declaration=v15.verify_closure(record,raw,receipt)
    require(declaration["closure_content_sha256"]==V141["content"],"unaccepted v1.4.1 closure content"); require(sha(raw)==V141["file"],"unaccepted v1.4.1 closure file")
    require(declaration["closure_receipt_sha256"]==V141["receipt"],"unaccepted v1.4.1 closure receipt")
    require(declaration["product_flow_uuid"]==V141["product_flow_uuid"] and declaration["product_flow_version"]==V141["product_flow_version"],"unaccepted declaration product identity")
    return declaration

def validate_record(r):
    require(r.get("verdict")==VERDICT,"wrong verdict"); require(r.get("mapping_state")=="EXPLICIT_REVIEWED_MAPPING","wrong mapping state")
    review=r.get("mapping_decision",{}).get("review",{}); require(review.get("state")=="REVIEWED_MAPPING_DECISION","mapping review state missing"); require(review.get("role")=="synthetic_test_mapping_decision","mapping review role mismatch"); require(bool(review.get("rationale")),"mapping rationale missing")
    require(r.get("environmental_mapping_performed") is True,"explicit mapping not recorded"); require(r.get("environmental_source_identity_selected") is True,"source identity selection not recorded")
    for k in ("environmental_factor_selected","impact_calculation_performed","assumed_zero","fuzzy_mapping_performed","name_only_mapping_performed","professional_review_performed","scientific_validation_performed","certified"):
        require(r.get(k) is False,f"{k} promotion rejected")
    require(r.get("environmental_coverage_status")=="EVIDENCE_UNCOVERED","coverage must remain uncovered")
    src=r.get("source_identity",{}); require(src.get("ifc_source_sha256")==SUCCESSOR_SOURCE_SHA and src.get("element_global_id")==ELEMENT_GLOBAL_ID,"source identity mismatch")
    require(src.get("material_association_step_id")==MATERIAL_ASSOCIATION_STEP_ID and src.get("material_step_id")==MATERIAL_STEP_ID,"material identity mismatch")
    require(src.get("quantity_set_step_id")==QUANTITY_SET_STEP_ID and src.get("quantity_step_id")==QUANTITY_STEP_ID and src.get("quantity_decimal")==QUANTITY_DECIMAL,"quantity identity mismatch")
    d=r.get("declaration_identity",{}); require(d.get("product_flow_uuid")==V141["product_flow_uuid"] and d.get("product_flow_version")==V141["product_flow_version"],"declaration identity mismatch")

def build(v24_record_path:Path,v24_receipt_path:Path,v24_comparison_path:Path,successor_ifc:Path,closure_path:Path,closure_receipt_path:Path):
    v24,v24raw=load(v24_record_path); v24r,v24rraw=load(v24_receipt_path); v24c,_=load(v24_comparison_path); verify_v24(v24,v24raw,v24r,v24rraw,v24c)
    ex,e,m,q=verify_successor(successor_ifc); declaration=verify_closure(closure_path,closure_receipt_path)
    record={
      "schema_version":"1.0","record_type":"ProofGridRemediatedExplicitEnvironmentalMapping","verdict":VERDICT,"mapping_state":"EXPLICIT_REVIEWED_MAPPING",
      "source_identity":{"ifc_source_sha256":SUCCESSOR_SOURCE_SHA,"ifc_schema":ex["schema"],"element_global_id":ELEMENT_GLOBAL_ID,"element_step_id":e["step_id"],"material_association_step_id":m["association_step_id"],"material_step_id":m["material_step_id"],"material_declared_name":m["name"],"quantity_set_step_id":q["set_step_id"],"quantity_step_id":q["quantity_step_id"],"quantity_decimal":QUANTITY_DECIMAL,"unit":"kg"},
      "declaration_identity":declaration,
      "mapping_decision":{"method":"EXPLICIT_REVIEWED_ARTIFACT","review":{"state":"REVIEWED_MAPPING_DECISION","reviewer":"RegenExcalibur v2.5 synthetic conformance harness","role":"synthetic_test_mapping_decision","rationale":"Exact accepted source, element, material, quantity, and declaration identifiers are mapping authority; display-name similarity is not authority.","reference":"ProofGrid issue #79"}},
      "parent_v24":{"record_content_sha256":V24["record_content"],"receipt_sha256":V24["receipt"],"comparison_receipt_sha256":V24["comparison"]},
      "environmental_mapping_performed":True,"environmental_source_identity_selected":True,"environmental_factor_selected":False,"impact_calculation_performed":False,"environmental_coverage_status":"EVIDENCE_UNCOVERED","assumed_zero":False,"fuzzy_mapping_performed":False,"name_only_mapping_performed":False,"professional_review_performed":False,"scientific_validation_performed":False,"certified":False,
      "limitations":["REVIEWED_MAPPING_DECISION is a synthetic workflow state and does not imply professional, scientific, programme-operator, or regulatory review.","No environmental result row or factor is selected in this gate.","No impact calculation, coverage promotion, whole-building completeness, scientific validation, professional review, or certification is performed."],
      "integrity":{"content_sha256":ZERO,"canonicalization":CANONICALIZATION,"signature":None}}
    record["integrity"]["content_sha256"]=sha(cbytes(record)); validate_record(record); return record

def make_receipt(r,raw):
    out={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"record_content_sha256":r["integrity"]["content_sha256"],"record_file_sha256":sha(raw),"mapping_state":"EXPLICIT_REVIEWED_MAPPING","ifc_source_sha256":SUCCESSOR_SOURCE_SHA,"element_global_id":ELEMENT_GLOBAL_ID,"quantity_decimal":QUANTITY_DECIMAL,"product_flow_uuid":V141["product_flow_uuid"],"product_flow_version":V141["product_flow_version"],"environmental_mapping_performed":True,"environmental_source_identity_selected":True,"environmental_factor_selected":False,"impact_calculation_performed":False,"environmental_coverage_status":"EVIDENCE_UNCOVERED","fuzzy_mapping_performed":False,"professional_review_performed":False,"certified":False}
    out["receipt_sha256"]=sha(cbytes(out)); return out

def main(argv=None):
    p=argparse.ArgumentParser()
    for n in ("v24-record","v24-receipt","v24-comparison","successor-ifc","closure","closure-receipt","output-dir"): p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args(argv)
    try:
      r=build(a.v24_record,a.v24_receipt,a.v24_comparison,a.successor_ifc,a.closure,a.closure_receipt); a.output_dir.mkdir(parents=True,exist_ok=True); raw=pbytes(r); (a.output_dir/"remediated-explicit-environmental-mapping.json").write_bytes(raw); rr=make_receipt(r,raw); (a.output_dir/"remediated-explicit-environmental-mapping-receipt.json").write_bytes(pbytes(rr)); print(json.dumps(rr,indent=2,sort_keys=True)); return 0
    except Exception as exc: print("FAILED:",exc); return 2
if __name__=="__main__": raise SystemExit(main())
