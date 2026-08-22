#!/usr/bin/env python3
"""ProofGrid v2.4 remediation readiness for the accepted uncovered inventory entry."""
from __future__ import annotations

import argparse, copy, hashlib, json, re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from adapters.ifc.extract import extract_ifc_declared_data

ENGINE_NAME = "RegenExcalibur ProofGrid Uncovered Inventory Remediation Readiness"
ENGINE_VERSION = "2.4.0"
VERDICT = "UNCOVERED_INVENTORY_REMEDIATION_READY_FOR_MAPPING_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO = "0" * 64

V23 = {
    "content": "8e286f5b796eab2b8de325c547b8c87404042478ee110aefeb4fcad8d5965a1a",
    "file": "98ea953159818f4f85f7ccfdf73216e5aeb22366fc14c017b4030286141b2be0",
    "receipt": "e6f0ecb4017c7dd742fc8c1b0fd64148390048a5c9c604e6659a387cd888ab4e",
    "receipt_file": "99ab39796c67dc3dfe0dd86972e0e0d3272fa65eba697d9d208f1d21c2d706af",
    "comparison": "597f713088d31d00ce1cc5f81d4200f19fd58da7a7e1149f31c226190a0ade0c",
    "comparison_file": "9fef0f13f10197f47ea824a1fbd8c6188f0e8550acb1dca2be426f395120472d",
}
PREDECESSOR_SOURCE_SHA = "42443f2f45f9bc122814a07c711cd67e6fc5d9033a7c17bf5ce20be70a24dcd3"
ELEMENT_GLOBAL_ID = "1DXL7DJx51bvggyIPU2Xi7"
MATERIAL_NAME = "RX-MATERIAL-THIRD-REMEDIATION-CONTROL"
EXPECTED_DECIMAL = "250"

class RemediationError(ValueError): pass

def require(c: bool, m: str):
    if not c: raise RemediationError(m)

def cbytes(v: Any) -> bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v: Any) -> bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def load(path: Path):
    raw=Path(path).read_bytes(); obj=json.loads(raw.decode()); require(isinstance(obj,dict),f"expected object: {path}"); return obj,raw

def verify_self(record,label):
    integ=record.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing hash")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO; require(sha(cbytes(shadow))==claimed,f"{label} hash mismatch"); return claimed

def verify_receipt(receipt,field,label):
    claimed=receipt.get(field); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {field}"); shadow=copy.deepcopy(receipt); shadow.pop(field,None); require(sha(cbytes(shadow))==claimed,f"{label} digest mismatch"); return claimed

def verify_v23(ledger,ledger_raw,receipt,receipt_raw,comparison,comparison_raw):
    require(ledger.get("verdict")=="DECLARED_SOURCE_INVENTORY_GAP_LEDGER_VERIFIABLE","wrong v2.3 verdict")
    require(verify_self(ledger,"v2.3 ledger")==V23["content"],"unaccepted v2.3 content"); require(sha(ledger_raw)==V23["file"],"unaccepted v2.3 file")
    require(verify_receipt(receipt,"receipt_sha256","v2.3 receipt")==V23["receipt"],"unaccepted v2.3 receipt"); require(sha(receipt_raw)==V23["receipt_file"],"unaccepted v2.3 receipt file")
    require(verify_receipt(comparison,"comparison_receipt_sha256","v2.3 comparison")==V23["comparison"],"unaccepted v2.3 comparison"); require(sha(comparison_raw)==V23["comparison_file"],"unaccepted v2.3 comparison file")
    u=[e for e in ledger.get("entries",[]) if e.get("evidence_status")=="EVIDENCE_UNCOVERED"]
    require(len(u)==1,"expected one v2.3 uncovered entry"); u=u[0]
    require(u.get("ifc_source_sha256")==PREDECESSOR_SOURCE_SHA,"predecessor source mismatch"); require(u.get("element_global_id")==ELEMENT_GLOBAL_ID,"predecessor element mismatch"); require(u.get("assumed_zero") is False,"predecessor assumed-zero promotion")

def build_successor_ifc(path: Path):
    import ifcopenshell
    m=ifcopenshell.file(schema="IFC4")
    mass=m.create_entity("IfcSIUnit",UnitType="MASSUNIT",Prefix="KILO",Name="GRAM")
    units=m.create_entity("IfcUnitAssignment",Units=[mass])
    m.create_entity("IfcProject",GlobalId="0kS$wWKLjAuhSPZ5IG0yTz",Name="ProofGrid v2.4 remediation successor",UnitsInContext=units)
    wall=m.create_entity("IfcWall",GlobalId=ELEMENT_GLOBAL_ID,Name="Remediated Uncovered Wall")
    mat=m.create_entity("IfcMaterial",Name=MATERIAL_NAME)
    m.create_entity("IfcRelAssociatesMaterial",GlobalId="2EXL7DJx51bvggyIPU2Xi9",RelatedObjects=[wall],RelatingMaterial=mat)
    q=m.create_entity("IfcQuantityWeight",Name="Mass",WeightValue=250.0)
    qset=m.create_entity("IfcElementQuantity",GlobalId="3EXL7DJx51bvggyIPU2Xj0",Name="Qto_WallBaseQuantities",Quantities=[q])
    m.create_entity("IfcRelDefinesByProperties",GlobalId="0EXL7DJx51bvggyIPU2Xj1",RelatedObjects=[wall],RelatingPropertyDefinition=qset)
    m.write(str(path))
    text=path.read_text(encoding="utf-8")
    text,count=re.subn(r"FILE_NAME\('[^']*','[^']*'","FILE_NAME('proofgrid-v24-successor.ifc','2026-01-01T00:00:00'",text,count=1)
    require(count==1,"failed IFC header canonicalization")
    path.write_text(text,encoding="utf-8",newline="\n")

def exact_weight_token(path: Path, qid: int) -> str:
    text=path.read_text(encoding="utf-8")
    pat=re.compile(rf"#{qid}=IFCQUANTITYWEIGHT\([^,]*,[^,]*,[^,]*,([^,]+),",re.I)
    m=pat.search(text); require(m is not None,"quantity STEP token not found")
    token=m.group(1).strip(); require(token not in {"$","*",""},"invalid quantity STEP token")
    return token

def canonical_decimal(token: str) -> str:
    try: n=Decimal(token)
    except InvalidOperation as exc: raise RemediationError("quantity token is not Decimal") from exc
    require(n.is_finite(),"quantity must be finite")
    rendered=format(n,"f"); rendered=rendered.rstrip("0").rstrip(".") if "." in rendered else rendered
    if rendered in {"","-0"}: rendered="0"
    return rendered

def validate_record(r):
    require(r.get("verdict")==VERDICT,"wrong verdict"); require(r.get("remediation_state")=="READY_FOR_EXPLICIT_MAPPING","wrong remediation state")
    require(r.get("environmental_coverage_status")=="EVIDENCE_UNCOVERED","environmental coverage promotion")
    for k in ("environmental_mapping_performed","environmental_factor_selected","impact_calculation_performed","assumed_zero","whole_building_scope","whole_building_completeness_evaluated","whole_building_lca_claimed","scientific_validation_performed","professional_review_performed","certified"):
        require(r.get(k) is False,f"{k} promotion rejected")
    s=r.get("successor_source",{}); require(s.get("predecessor_source_sha256")==PREDECESSOR_SOURCE_SHA,"predecessor mismatch"); require(s.get("successor_source_sha256")!=PREDECESSOR_SOURCE_SHA,"successor must differ from predecessor"); require(s.get("element_global_id")==ELEMENT_GLOBAL_ID,"successor element identity changed")
    q=r.get("quantity_evidence",{}); require(q.get("quantity_decimal")==EXPECTED_DECIMAL,"quantity Decimal mismatch"); require(q.get("source_token_is_authority") is True,"source token must be authority"); require(q.get("parser_numeric_value_is_authority") is False,"parser float authority promotion"); require(q.get("unit")=="kg","mass unit mismatch")
    m=r.get("material_evidence",{}); require(m.get("declared_name")==MATERIAL_NAME,"material mismatch")

def build_record(v23_ledger:Path,v23_receipt:Path,v23_comparison:Path,successor_ifc:Path):
    ledger,lr=load(v23_ledger); receipt,rr=load(v23_receipt); comparison,cr=load(v23_comparison); verify_v23(ledger,lr,receipt,rr,comparison,cr)
    successor_sha=sha(successor_ifc.read_bytes()); require(successor_sha!=PREDECESSOR_SOURCE_SHA,"successor source equals predecessor")
    extracted=extract_ifc_declared_data(successor_ifc)
    elements=[e for e in extracted["elements"] if e.get("global_id")==ELEMENT_GLOBAL_ID]; require(len(elements)==1,"expected one successor element"); e=elements[0]
    require(len(e.get("materials",[]))==1,"expected exactly one material association"); require(len(e.get("quantities",[]))==1,"expected exactly one declared quantity")
    mat=e["materials"][0]; q=e["quantities"][0]; require(q.get("ifc_quantity_type")=="IfcQuantityWeight","expected IfcQuantityWeight")
    unit=q.get("unit") or {}; require(unit.get("unit_type")=="MASSUNIT" and unit.get("name")=="GRAM" and unit.get("prefix")=="KILO","expected kg project unit context")
    token=exact_weight_token(successor_ifc,int(q["quantity_step_id"])); dec=canonical_decimal(token); require(dec==EXPECTED_DECIMAL,"unexpected successor exact Decimal")
    r={
      "schema_version":"1.0","record_type":"ProofGridUncoveredInventoryRemediationReadiness","verdict":VERDICT,"remediation_state":"READY_FOR_EXPLICIT_MAPPING","environmental_coverage_status":"EVIDENCE_UNCOVERED",
      "parent_v23":{"ledger_content_sha256":V23["content"],"ledger_receipt_sha256":V23["receipt"],"comparison_receipt_sha256":V23["comparison"]},
      "successor_source":{"predecessor_source_sha256":PREDECESSOR_SOURCE_SHA,"successor_source_sha256":successor_sha,"element_global_id":ELEMENT_GLOBAL_ID,"ifc_schema":extracted["schema"]},
      "material_evidence":{"association_step_id":mat["association_step_id"],"material_step_id":mat["material_step_id"],"declared_name":mat["name"],"source_type":mat["source_type"]},
      "quantity_evidence":{"set_step_id":q["set_step_id"],"quantity_step_id":q["quantity_step_id"],"ifc_quantity_type":q["ifc_quantity_type"],"quantity_lexical":token,"quantity_decimal":dec,"parser_numeric_value":q["value"],"source_token_is_authority":True,"parser_numeric_value_is_authority":False,"unit":"kg","unit_identity":{"unit_type":unit["unit_type"],"name":unit["name"],"prefix":unit["prefix"],"source":unit["source"]}},
      "environmental_mapping_performed":False,"environmental_factor_selected":False,"impact_calculation_performed":False,"assumed_zero":False,"whole_building_scope":False,"whole_building_completeness_evaluated":False,"whole_building_lca_claimed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
      "limitations":["This successor source is ready for explicit mapping only; it has no accepted environmental source or impact result.","Exact STEP Decimal is quantity authority; parser numeric value is consistency evidence only.","No environmental mapping, factor selection, impact calculation, whole-building completeness, scientific validation, professional review, or certification is performed."],
      "integrity":{"content_sha256":ZERO,"canonicalization":CANONICALIZATION,"signature":None}}
    r["integrity"]["content_sha256"]=sha(cbytes(r)); validate_record(r); return r

def make_receipt(r,raw):
    out={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"record_content_sha256":r["integrity"]["content_sha256"],"record_file_sha256":sha(raw),"remediation_state":"READY_FOR_EXPLICIT_MAPPING","predecessor_source_sha256":PREDECESSOR_SOURCE_SHA,"successor_source_sha256":r["successor_source"]["successor_source_sha256"],"element_global_id":ELEMENT_GLOBAL_ID,"quantity_lexical":r["quantity_evidence"]["quantity_lexical"],"quantity_decimal":EXPECTED_DECIMAL,"material_name":MATERIAL_NAME,"environmental_coverage_status":"EVIDENCE_UNCOVERED","environmental_mapping_performed":False,"impact_calculation_performed":False,"assumed_zero":False,"certified":False}
    out["receipt_sha256"]=sha(cbytes(out)); return out

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True); b=sub.add_parser("build-successor"); b.add_argument("--output",type=Path,required=True); r=sub.add_parser("record")
    for n in ("v23-ledger","v23-receipt","v23-comparison","successor-ifc","output-dir"): r.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args(argv)
    try:
      if a.cmd=="build-successor": a.output.parent.mkdir(parents=True,exist_ok=True); build_successor_ifc(a.output); print("SUCCESSOR_SHA="+sha(a.output.read_bytes())); return 0
      rec=build_record(a.v23_ledger,a.v23_receipt,a.v23_comparison,a.successor_ifc); a.output_dir.mkdir(parents=True,exist_ok=True); raw=pbytes(rec); (a.output_dir/"uncovered-remediation-readiness.json").write_bytes(raw); receipt=make_receipt(rec,raw); (a.output_dir/"uncovered-remediation-readiness-receipt.json").write_bytes(pbytes(receipt)); print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
    except Exception as exc: print("FAILED:",exc); return 2
if __name__=="__main__": raise SystemExit(main())
