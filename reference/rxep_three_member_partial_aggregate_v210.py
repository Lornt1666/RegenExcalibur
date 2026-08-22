#!/usr/bin/env python3
"""ProofGrid v2.10 RXEP binder for the accepted three-member PARTIAL aggregate.

No arithmetic occurs in this layer. The exact accepted v2.9 aggregate record,
receipt, and independent-reproduction receipt are hard-pinned and rebound into
RXEP while preserving exact Decimal authority, PARTIAL completeness, and
CALCULATED review state.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, SchemaError

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
RXEP_SCHEMA=ROOT/"specs"/"rxep"/"evidence-envelope.schema.json"
ENGINE_NAME="RegenExcalibur ProofGrid RXEP Three-Member Partial Aggregate Binder"
ENGINE_VERSION="2.10.0"
VERDICT="RXEP_EXACT_DECIMAL_THREE_MEMBER_PARTIAL_AGGREGATE_EVIDENCE_VERIFIABLE"
PARENT_VERDICT="THREE_MEMBER_PARTIAL_SET_EXACT_DECIMAL_TOTAL_VERIFIABLE"
COMPARISON_VERDICT="THREE_MEMBER_PARTIAL_SET_EXACT_DECIMAL_TOTAL_INDEPENDENTLY_REPRODUCED"
ZERO_DIGEST="0"*64
CANONICALIZATION="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
EXPECTED={
 "head":"7c0b701e39140b9ad1f0e978f356bd6e81c3bddc",
 "record_content":"a8bc307f8fc1932ca852404b7722372619666308904829b4297cb06c10ca3a16",
 "record_file":"e5dabfd18e64ec8d0d4749d481caf799975c9ca32608f91667ab42d60b460b91",
 "receipt":"8c5050c45bcdd24eab9b9a1b6d10d5e6404c25137e16eb4efbf9ed9b7548ae39",
 "receipt_file":"1ba6880ede8a12775376704b48f2d77fb9cc0cdfd032c3a46485e0ce10cec804",
 "comparison":"c2a19b7426d20d62a01a2bdebdb04e66bf29fb62da5e0e3588baa5a35e6d1c5f",
 "comparison_file":"71828d0eda13558e4d9e5ac6362711876a81af501df721b1cc3442b655c95131",
 "value_decimal":"27229.08943503647325",
 "unit":"kg CO2 eqv.",
 "member_ids":[
  "2a67655f18b9cd8d776335e886dc324c9911dd9e1090e8852752235ecb958905",
  "75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950",
  "b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc"
 ]
}
COMPAT={"indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","module":"A1-A3","scenario":None,"unit":"kg CO2 eqv."}

class RXEPThreeAggregateError(ValueError): pass

def require(c:bool,m:str)->None:
    if not c: raise RXEPThreeAggregateError(m)

def canonical_json_bytes(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def pretty_json_bytes(v:Any)->bytes:
    return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")

def sha256_bytes(v:bytes)->str: return hashlib.sha256(v).hexdigest()

def load_json(path:Path)->tuple[dict[str,Any],bytes]:
    try: raw=Path(path).read_bytes()
    except FileNotFoundError as e: raise RXEPThreeAggregateError(f"missing required file: {path}") from e
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception as e: raise RXEPThreeAggregateError(f"invalid UTF-8 JSON in {path}: {e}") from e
    require(isinstance(obj,dict),f"expected JSON object: {path}")
    return obj,raw

def canonical_decimal(v:Any,label:str)->str:
    require(isinstance(v,str) and v,f"{label} must be a non-empty Decimal string")
    try: d=Decimal(v)
    except InvalidOperation as e: raise RXEPThreeAggregateError(f"{label} is not Decimal-compatible") from e
    require(d.is_finite(),f"{label} must be finite")
    rendered="0" if d==0 else format(d,"f")
    if "." in rendered: rendered=rendered.rstrip("0").rstrip(".")
    require(rendered==v,f"{label} is not canonical Decimal")
    return v

def verify_self_hash(record:dict[str,Any],label:str)->str:
    integ=record.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity")
    claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content SHA")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} content digest mismatch")
    return claimed

def verify_receipt_digest(r:dict[str,Any],label:str,key:str)->str:
    claimed=r.get(key); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {key}")
    shadow=copy.deepcopy(r); shadow.pop(key,None)
    require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} digest mismatch")
    return claimed

def validate_rxep(env:dict[str,Any])->None:
    schema=json.loads(RXEP_SCHEMA.read_text(encoding="utf-8"))
    try: Draft202012Validator.check_schema(schema)
    except SchemaError as e: raise RXEPThreeAggregateError(f"invalid RXEP schema: {e.message}") from e
    errors=sorted(Draft202012Validator(schema).iter_errors(env),key=lambda e:list(e.path))
    if errors: raise RXEPThreeAggregateError("RXEP schema validation failed: "+"; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6]))

def verify_parents(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)->None:
    require(record.get("verdict")==PARENT_VERDICT,"wrong v2.9 aggregate verdict")
    content=verify_self_hash(record,"v2.9 aggregate")
    require(content==EXPECTED["record_content"],"unaccepted v2.9 aggregate content")
    require(sha256_bytes(record_raw)==EXPECTED["record_file"],"unaccepted v2.9 aggregate file")
    rsha=verify_receipt_digest(receipt,"v2.9 aggregate receipt","receipt_sha256")
    require(rsha==EXPECTED["receipt"],"unaccepted v2.9 aggregate receipt")
    require(sha256_bytes(receipt_raw)==EXPECTED["receipt_file"],"unaccepted v2.9 aggregate receipt file")
    require(receipt.get("record_content_sha256")==EXPECTED["record_content"],"v2.9 receipt/content mismatch")
    require(receipt.get("record_file_sha256")==EXPECTED["record_file"],"v2.9 receipt/file mismatch")
    require(canonical_decimal(record.get("aggregation",{}).get("total_value_decimal"),"v2.9 total")==EXPECTED["value_decimal"],"v2.9 total mismatch")
    require(record.get("aggregation",{}).get("unit")==EXPECTED["unit"],"v2.9 unit mismatch")
    require(record.get("compatibility")==COMPAT,"v2.9 compatibility mismatch")
    require(record.get("member_count")==3 and receipt.get("member_count")==3,"v2.9 member count mismatch")
    ids=record.get("aggregation",{}).get("member_order")
    require(ids==EXPECTED["member_ids"],"v2.9 member semantic identities mismatch")
    require(receipt.get("member_semantic_identity_sha256")==EXPECTED["member_ids"],"v2.9 receipt member identities mismatch")
    require(record.get("completeness_status")=="PARTIAL" and receipt.get("completeness_status")=="PARTIAL","v2.9 completeness promotion rejected")
    for obj,label in ((record,"v2.9 record"),(receipt,"v2.9 receipt")):
        require(obj.get("aggregation_performed") is True,f"{label} lost aggregation flag")
        require(obj.get("sum_performed") is True,f"{label} lost sum flag")
        require(obj.get("whole_building_lca_claimed") is False,f"{label} whole-building promotion rejected")
        require(obj.get("declared_scope_complete_claimed") is False,f"{label} declared-scope promotion rejected")
        for key in ("missing_contributions_are_zero","missing_modules_are_zero","unit_conversion_performed","scenario_inference_performed","duplicate_members_permitted","scientific_validation_performed","professional_review_performed","certified"):
            require(obj.get(key) is False,f"{label} {key} promotion rejected")
    require(comparison.get("verdict")==COMPARISON_VERDICT,"wrong v2.9 comparison verdict")
    csha=verify_receipt_digest(comparison,"v2.9 comparison","comparison_receipt_sha256")
    require(csha==EXPECTED["comparison"],"unaccepted v2.9 comparison receipt")
    require(sha256_bytes(comparison_raw)==EXPECTED["comparison_file"],"unaccepted v2.9 comparison file")
    require(comparison.get("accepted_v28_head")=="45e0191d4c21b13bd394ddcebddee547c4eee650","v2.9 comparison parent-head mismatch")
    require(comparison.get("byte_identical") is True and comparison.get("independent_runner_count")==2,"v2.9 reproduction not proven")
    require(comparison.get("record_content_sha256")==EXPECTED["record_content"],"v2.9 comparison record mismatch")
    require(comparison.get("receipt_sha256")==EXPECTED["receipt"],"v2.9 comparison receipt mismatch")
    require(comparison.get("total_value_decimal")==EXPECTED["value_decimal"],"v2.9 comparison total mismatch")
    require(comparison.get("member_count")==3 and comparison.get("completeness_status")=="PARTIAL","v2.9 comparison state mismatch")
    require(comparison.get("whole_building_lca_claimed") is False and comparison.get("certified") is False,"v2.9 comparison promotion rejected")

def verify_profile(env:dict[str,Any])->None:
    validate_rxep(env)
    require(env.get("review")=={"state":"CALCULATED","reviewer":None},"RXEP review state must remain CALCULATED/null")
    m=env.get("measurement",{})
    require(m.get("value_decimal")==EXPECTED["value_decimal"],"RXEP Decimal mismatch")
    require(m.get("decimal_value_is_authority") is True,"RXEP Decimal authority missing")
    require(m.get("numeric_value_is_authority") is False,"RXEP numeric authority promotion rejected")
    require(m.get("numeric_value_role")=="NON_AUTHORITATIVE_DISPLAY","RXEP numeric display role mismatch")
    require({k:m.get(k) for k in ("indicator_code","indicator_uuid","module","scenario","unit")}==COMPAT,"RXEP compatibility mismatch")
    require(env.get("aggregation_performed") is True and env.get("sum_performed") is True,"RXEP aggregation state mismatch")
    require(env.get("aggregation_scope")=="ADMITTED_SET_MEMBERS_ONLY","RXEP aggregation scope mismatch")
    require(env.get("member_count")==3,"RXEP member count mismatch")
    require(env.get("member_semantic_identity_sha256")==EXPECTED["member_ids"],"RXEP member identities mismatch")
    require(env.get("completeness_status")=="PARTIAL","RXEP completeness promotion rejected")
    require(env.get("whole_building_lca_claimed") is False and env.get("declared_scope_complete_claimed") is False,"RXEP completeness claim promotion rejected")
    for key in ("missing_contributions_are_zero","missing_modules_are_zero","unit_conversion_performed","scenario_inference_performed","duplicate_members_permitted","scientific_validation_performed","professional_review_performed","certified"):
        require(env.get(key) is False,f"RXEP {key} promotion rejected")

def build_envelope(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)->dict[str,Any]:
    verify_parents(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)
    total=Decimal(EXPECTED["value_decimal"])
    env={
      "id":f"rxep:v210:three-member-partial-aggregate:{EXPECTED['record_content']}",
      "subject":{"id":record["source_set"]["scope_id"],"type":"partial-environmental-contribution-set","name":"Exact Decimal total of three admitted PARTIAL environmental contributions"},
      "claim":{"type":"three_member_partial_contribution_set_exact_decimal_total","statement":"The accepted exact Decimal total of three admitted compatible members is bound as RXEP evidence; no whole-building or declared-scope completeness is claimed."},
      "measurement":{"value":float(total),"value_decimal":EXPECTED["value_decimal"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"numeric_value_role":"NON_AUTHORITATIVE_DISPLAY",**COMPAT},
      "methodology":{"name":"canonical_decimal_sum","version":"2.9.0","formula":"sum(admitted_member.value_decimal)","aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY"},
      "sources":[
        {"path":"accepted-v2.9/three-member-partial-set-exact-decimal-total.json","sha256":EXPECTED["record_file"],"kind":"aggregate-record","content_sha256":EXPECTED["record_content"]},
        {"path":"accepted-v2.9/three-member-partial-set-exact-decimal-total-receipt.json","sha256":EXPECTED["receipt_file"],"kind":"aggregate-receipt","receipt_sha256":EXPECTED["receipt"]},
        {"path":"accepted-v2.9/v29-independent-comparison-receipt.json","sha256":EXPECTED["comparison_file"],"kind":"software-reproduction-receipt","receipt_sha256":EXPECTED["comparison"]}
      ],
      "software":{"name":ENGINE_NAME,"version":ENGINE_VERSION},
      "jurisdiction":"UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
      "review":{"state":"CALCULATED","reviewer":None},
      "limitations":["This envelope binds an already accepted exact Decimal three-member sum; it performs no new arithmetic.","The generic numeric measurement value is non-authoritative display/interoperability data; value_decimal is exact authority.","PARTIAL completeness is preserved; this is not a whole-building or declared-scope-complete LCA.","No missing contribution/module is treated as zero and no unit conversion or scenario inference is performed.","Software reproduction and evidence binding do not establish scientific validity, professional review, regulatory approval, or certification."],
      "aggregation_performed":True,"sum_performed":True,"aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY","member_count":3,"member_semantic_identity_sha256":list(EXPECTED["member_ids"]),"completeness_status":"PARTIAL","whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
      "aggregate_reproduction":{"independent_runner_count":2,"byte_identical":True,"comparison_receipt_sha256":EXPECTED["comparison"],"accepted_v29_head":EXPECTED["head"]},
      "integrity":{"content_sha256":ZERO_DIGEST,"canonicalization":CANONICALIZATION,"signature":None}
    }
    env["integrity"]["content_sha256"]=sha256_bytes(canonical_json_bytes(env)); verify_profile(env); return env

def build_receipt(env:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"review_state":"CALCULATED","value_decimal":EXPECTED["value_decimal"],"unit":EXPECTED["unit"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"member_count":3,"member_semantic_identity_sha256":EXPECTED["member_ids"],"completeness_status":"PARTIAL","aggregation_performed":True,"sum_performed":True,"aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY","whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,"parent_record_content_sha256":EXPECTED["record_content"],"parent_receipt_sha256":EXPECTED["receipt"],"parent_comparison_receipt_sha256":EXPECTED["comparison"],"record_content_sha256":env["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw)}
    r["receipt_sha256"]=sha256_bytes(canonical_json_bytes(r)); return r

def write_outputs(env:dict[str,Any],outdir:Path)->None:
    outdir.mkdir(parents=True,exist_ok=True); rp=outdir/"rxep-three-member-partial-aggregate.json"; rr=outdir/"rxep-three-member-partial-aggregate-receipt.json"; raw=pretty_json_bytes(env); rp.write_bytes(raw); rr.write_bytes(pretty_json_bytes(build_receipt(env,raw)))

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--aggregate-record",type=Path,required=True); p.add_argument("--aggregate-receipt",type=Path,required=True); p.add_argument("--comparison-receipt",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(argv)
    try:
        rec,rec_raw=load_json(a.aggregate_record); rr,rr_raw=load_json(a.aggregate_receipt); cmp,cmp_raw=load_json(a.comparison_receipt); env=build_envelope(rec,rec_raw,rr,rr_raw,cmp,cmp_raw); write_outputs(env,a.output_dir)
    except Exception as e:
        print(f"FAILED: {e}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print(f"EXACT RXEP AGGREGATE: {EXPECTED['value_decimal']} {EXPECTED['unit']}"); print("REVIEW: CALCULATED"); print("COMPLETENESS: PARTIAL"); print("NOT A WHOLE-BUILDING LCA"); return 0
if __name__=="__main__": raise SystemExit(main())
