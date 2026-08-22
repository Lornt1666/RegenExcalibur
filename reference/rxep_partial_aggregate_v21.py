#!/usr/bin/env python3
"""ProofGrid v2.1 RXEP binder for one accepted exact-Decimal PARTIAL aggregate.

This layer performs no aggregation arithmetic. It verifies the exact accepted
v2.0 aggregate record/receipt plus its independent reproduction receipt, then
binds that accepted result into RXEP while preserving PARTIAL completeness and
CALCULATED review state.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
RXEP_SCHEMA = ROOT / "specs" / "rxep" / "evidence-envelope.schema.json"
ENGINE_NAME = "RegenExcalibur ProofGrid RXEP Exact-Decimal Partial Aggregate Binder"
ENGINE_VERSION = "2.1.0"
VERDICT = "RXEP_EXACT_DECIMAL_PARTIAL_AGGREGATE_EVIDENCE_VERIFIABLE"
PARENT_VERDICT = "PARTIAL_CONTRIBUTION_SET_EXACT_DECIMAL_TOTAL_VERIFIABLE"
COMPARISON_VERDICT = "PARTIAL_CONTRIBUTION_SET_EXACT_DECIMAL_TOTAL_INDEPENDENTLY_REPRODUCED"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64
EXPECTED = {
    "head":"2fc2c450b1f37cb2c355ff12d09622ad5f094eec",
    "record_content":"8b47dfb87f1be4e1979666f85f7da58c41c00e48c92b7cd4a2f3c9fdd62e8ed0",
    "record_file":"3e50fc30562b0611170b78baf1cf8b52a0cd39ba052f1398c7463a700ba9e6d8",
    "receipt":"991de0efd5c71c067391c8e5fa7bbf81fd55febb72a4cfe8cf5a10f09ac238d4",
    "receipt_file":"17ee6da67b9c549f6b53346fa49e4bf8d30d4d459a4f2c17566d286521cb8f2d",
    "comparison":"74f5ef72a9f1fdd6c8145bc3291e0bfbb9373c94cbf1b048822e291266b7f839",
    "comparison_file":"ff6f4a09678f9f9647df06fa6d28dc30aef6346ee81aeb6169ecf2c187c2ee7a",
    "value_decimal":"23339.2195157455485",
    "unit":"kg CO2 eqv.",
    "member_semantic_identity_sha256":["75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950","b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc"]
}
INDICATOR_CODE="GWP-total"
INDICATOR_UUID="6a37f984-a4b3-458a-a20a-64418c145fa2"
MODULE="A1-A3"

class RXEPPartialAggregateError(ValueError): pass

def require(c: bool, m: str) -> None:
    if not c: raise RXEPPartialAggregateError(m)

def canonical_json_bytes(v: Any) -> bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def pretty_json_bytes(v: Any) -> bytes:
    return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")

def sha256_bytes(v: bytes) -> str: return hashlib.sha256(v).hexdigest()

def load_json(path: Path) -> tuple[dict[str,Any],bytes]:
    try: raw=Path(path).read_bytes()
    except FileNotFoundError as exc: raise RXEPPartialAggregateError(f"missing required file: {path}") from exc
    try: value=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise RXEPPartialAggregateError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value,dict),f"expected JSON object: {path}")
    return value,raw

def canonical_decimal(v: Any,label:str)->str:
    require(isinstance(v,str) and v,f"{label} must be a non-empty Decimal string")
    try: d=Decimal(v)
    except InvalidOperation as exc: raise RXEPPartialAggregateError(f"{label} is not Decimal-compatible") from exc
    require(d.is_finite(),f"{label} must be finite")
    if d == 0:
        rendered = "0"
    else:
        rendered = format(d,"f")
        if "." in rendered: rendered = rendered.rstrip("0").rstrip(".")
    require(rendered==v,f"{label} is not canonical Decimal")
    return v

def verify_self_hash(record:dict[str,Any],label:str)->str:
    integrity=record.get("integrity"); require(isinstance(integrity,dict),f"{label} missing integrity")
    claimed=integrity.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content SHA-256")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} content digest mismatch")
    return claimed

def verify_receipt_digest(receipt:dict[str,Any],label:str,key:str="receipt_sha256")->str:
    claimed=receipt.get(key); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {key}")
    shadow=copy.deepcopy(receipt); shadow.pop(key,None)
    require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} canonical digest mismatch")
    return claimed

def validate_rxep(envelope:dict[str,Any])->None:
    schema=json.loads(RXEP_SCHEMA.read_text(encoding="utf-8"))
    try: Draft202012Validator.check_schema(schema)
    except SchemaError as exc: raise RXEPPartialAggregateError(f"invalid RXEP schema: {exc.message}") from exc
    errors=sorted(Draft202012Validator(schema).iter_errors(envelope),key=lambda e:list(e.path))
    if errors:
        raise RXEPPartialAggregateError("RXEP schema validation failed: "+"; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6]))

def verify_parents(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)->None:
    require(record.get("verdict")==PARENT_VERDICT,"wrong v2.0 aggregate verdict")
    content=verify_self_hash(record,"v2.0 aggregate")
    require(content==EXPECTED["record_content"],"unaccepted v2.0 aggregate content")
    require(sha256_bytes(record_raw)==EXPECTED["record_file"],"unaccepted v2.0 aggregate file")
    receipt_sha=verify_receipt_digest(receipt,"v2.0 aggregate receipt")
    require(receipt_sha==EXPECTED["receipt"],"unaccepted v2.0 aggregate receipt")
    require(sha256_bytes(receipt_raw)==EXPECTED["receipt_file"],"unaccepted v2.0 aggregate receipt file")
    require(receipt.get("record_content_sha256")==content and receipt.get("record_file_sha256")==EXPECTED["record_file"],"v2.0 receipt/record binding mismatch")
    require(canonical_decimal(record.get("aggregation",{}).get("total_value_decimal"),"v2.0 total")==EXPECTED["value_decimal"],"v2.0 exact total mismatch")
    require(record.get("aggregation",{}).get("unit")==EXPECTED["unit"],"v2.0 unit mismatch")
    require(record.get("member_count")==2 and receipt.get("member_count")==2,"v2.0 member count mismatch")
    require(record.get("completeness_status")=="PARTIAL" and receipt.get("completeness_status")=="PARTIAL","v2.0 completeness promotion rejected")
    require(record.get("compatibility")=={"indicator_code":INDICATOR_CODE,"indicator_uuid":INDICATOR_UUID,"module":MODULE,"scenario":None,"unit":EXPECTED["unit"]},"v2.0 compatibility mismatch")
    ids=[m.get("semantic_identity_sha256") for m in record.get("members",[])]
    require(ids==EXPECTED["member_semantic_identity_sha256"],"v2.0 semantic member identity mismatch")
    for obj,label in ((record,"v2.0 record"),(receipt,"v2.0 receipt")):
        require(obj.get("aggregation_performed") is True,f"{label} lost aggregation flag")
        require(obj.get("sum_performed") is True,f"{label} lost sum flag")
        require(obj.get("whole_building_lca_claimed") is False,f"{label} whole-building promotion rejected")
        require(obj.get("declared_scope_complete_claimed") is False,f"{label} declared-scope promotion rejected")
        for key in ("missing_contributions_are_zero","missing_modules_are_zero","unit_conversion_performed","scenario_inference_performed","duplicate_members_permitted","scientific_validation_performed","professional_review_performed","certified"):
            require(obj.get(key) is False,f"{label} {key} promotion rejected")
    require(comparison.get("verdict")==COMPARISON_VERDICT,"wrong v2.0 comparison verdict")
    comparison_sha=verify_receipt_digest(comparison,"v2.0 comparison receipt","comparison_receipt_sha256")
    require(comparison_sha==EXPECTED["comparison"],"unaccepted v2.0 comparison receipt")
    require(sha256_bytes(comparison_raw)==EXPECTED["comparison_file"],"unaccepted v2.0 comparison receipt file")
    require(comparison.get("byte_identical") is True and comparison.get("independent_runner_count")==2,"v2.0 independent reproduction not proven")
    require(comparison.get("record_content_sha256")==EXPECTED["record_content"] and comparison.get("receipt_sha256")==EXPECTED["receipt"],"v2.0 comparison parent binding mismatch")
    require(comparison.get("total_value_decimal")==EXPECTED["value_decimal"],"v2.0 comparison total mismatch")
    require(comparison.get("completeness_status")=="PARTIAL" and comparison.get("whole_building_lca_claimed") is False,"v2.0 comparison completeness promotion rejected")

def verify_profile(envelope:dict[str,Any])->None:
    validate_rxep(envelope)
    require(envelope.get("review")=={"state":"CALCULATED","reviewer":None},"RXEP aggregate review state must remain CALCULATED/null")
    m=envelope.get("measurement",{})
    require(m.get("value_decimal")==EXPECTED["value_decimal"],"RXEP aggregate Decimal mismatch")
    require(m.get("decimal_value_is_authority") is True,"RXEP aggregate Decimal authority missing")
    require(m.get("numeric_value_is_authority") is False,"RXEP aggregate numeric authority promotion rejected")
    require(m.get("numeric_value_role")=="NON_AUTHORITATIVE_DISPLAY","RXEP aggregate numeric role mismatch")
    require(m.get("unit")==EXPECTED["unit"] and m.get("indicator_code")==INDICATOR_CODE and m.get("indicator_uuid")==INDICATOR_UUID and m.get("module")==MODULE and m.get("scenario") is None,"RXEP aggregate compatibility mismatch")
    require(envelope.get("aggregation_performed") is True and envelope.get("sum_performed") is True,"RXEP aggregate must preserve accepted aggregation")
    require(envelope.get("aggregation_scope")=="ADMITTED_SET_MEMBERS_ONLY","RXEP aggregate scope mismatch")
    require(envelope.get("member_count")==2,"RXEP aggregate member count mismatch")
    require(envelope.get("member_semantic_identity_sha256")==EXPECTED["member_semantic_identity_sha256"],"RXEP aggregate member identities mismatch")
    require(envelope.get("completeness_status")=="PARTIAL","RXEP aggregate completeness promotion rejected")
    require(envelope.get("whole_building_lca_claimed") is False and envelope.get("declared_scope_complete_claimed") is False,"RXEP aggregate completeness claim promotion rejected")
    for key in ("missing_contributions_are_zero","missing_modules_are_zero","unit_conversion_performed","scenario_inference_performed","duplicate_members_permitted","scientific_validation_performed","professional_review_performed","certified"):
        require(envelope.get(key) is False,f"RXEP aggregate {key} promotion rejected")

def build_envelope(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)->dict[str,Any]:
    verify_parents(record,record_raw,receipt,receipt_raw,comparison,comparison_raw)
    total=Decimal(EXPECTED["value_decimal"])
    envelope={
        "id":f"rxep:v21:partial-aggregate:{EXPECTED['record_content']}",
        "subject":{"id":record["source_set"]["scope_id"],"type":"partial-environmental-contribution-set","name":"Exact Decimal total of two admitted PARTIAL environmental contributions"},
        "claim":{"type":"partial_contribution_set_exact_decimal_total","statement":"The exact Decimal total of the two admitted compatible members in the accepted PARTIAL contribution set is bound as RXEP evidence; no whole-building or declared-scope completeness is claimed."},
        "measurement":{"value":float(total),"value_decimal":EXPECTED["value_decimal"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"numeric_value_role":"NON_AUTHORITATIVE_DISPLAY","unit":EXPECTED["unit"],"indicator_code":INDICATOR_CODE,"indicator_uuid":INDICATOR_UUID,"module":MODULE,"scenario":None},
        "methodology":{"name":"canonical_decimal_sum","version":"2.0.0","formula":"sum(admitted_member.value_decimal)","aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY"},
        "sources":[
            {"path":"accepted-v2.0/partial-contribution-set-exact-decimal-total.json","sha256":EXPECTED["record_file"],"kind":"aggregate-record","content_sha256":EXPECTED["record_content"]},
            {"path":"accepted-v2.0/partial-contribution-set-exact-decimal-total-receipt.json","sha256":EXPECTED["receipt_file"],"kind":"aggregate-receipt","receipt_sha256":EXPECTED["receipt"]},
            {"path":"accepted-v2.0/v20-independent-comparison-receipt.json","sha256":EXPECTED["comparison_file"],"kind":"software-reproduction-receipt","receipt_sha256":EXPECTED["comparison"]}
        ],
        "software":{"name":ENGINE_NAME,"version":ENGINE_VERSION},
        "jurisdiction":"UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
        "review":{"state":"CALCULATED","reviewer":None},
        "limitations":[
            "This RXEP envelope binds an already accepted exact Decimal sum; it performs no new aggregation arithmetic.",
            "The generic numeric measurement value is non-authoritative display/interoperability data; value_decimal is the exact evidence authority.",
            "PARTIAL completeness is preserved; this is not a complete building LCA or declared-scope-complete result.",
            "No missing contribution/module is treated as zero and no unit conversion or scenario inference is performed.",
            "Software reproduction and evidence binding do not establish scientific validity, professional review, regulatory approval, or certification."
        ],
        "aggregation_performed":True,"sum_performed":True,"aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY","member_count":2,"member_semantic_identity_sha256":list(EXPECTED["member_semantic_identity_sha256"]),"completeness_status":"PARTIAL","whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
        "aggregate_reproduction":{"independent_runner_count":2,"byte_identical":True,"comparison_receipt_sha256":EXPECTED["comparison"],"accepted_v20_head":EXPECTED["head"]},
        "integrity":{"content_sha256":ZERO_DIGEST,"canonicalization":CANONICALIZATION,"signature":None}
    }
    envelope["integrity"]["content_sha256"]=sha256_bytes(canonical_json_bytes(envelope))
    verify_profile(envelope)
    return envelope

def write_outputs(envelope:dict[str,Any],output_dir:Path)->dict[str,str]:
    output_dir.mkdir(parents=True,exist_ok=True)
    record_path=output_dir/"rxep-exact-decimal-partial-aggregate.json"; receipt_path=output_dir/"rxep-exact-decimal-partial-aggregate-receipt.json"
    raw=pretty_json_bytes(envelope); record_path.write_bytes(raw)
    receipt={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"review_state":"CALCULATED","record_content_sha256":envelope["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw),"value_decimal":EXPECTED["value_decimal"],"unit":EXPECTED["unit"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"v20_record_content_sha256":EXPECTED["record_content"],"v20_aggregate_receipt_sha256":EXPECTED["receipt"],"v20_comparison_receipt_sha256":EXPECTED["comparison"],"aggregation_performed":True,"sum_performed":True,"aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY","member_count":2,"member_semantic_identity_sha256":list(EXPECTED["member_semantic_identity_sha256"]),"completeness_status":"PARTIAL","whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    receipt["receipt_sha256"]=sha256_bytes(canonical_json_bytes(receipt)); receipt_raw=pretty_json_bytes(receipt); receipt_path.write_bytes(receipt_raw)
    return {"record":str(record_path),"receipt":str(receipt_path),"record_content_sha256":envelope["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw),"receipt_sha256":receipt["receipt_sha256"],"receipt_file_sha256":sha256_bytes(receipt_raw)}

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--aggregate-record",type=Path,required=True); p.add_argument("--aggregate-receipt",type=Path,required=True); p.add_argument("--comparison-receipt",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(argv)
    try:
        record,rr=load_json(a.aggregate_record); receipt,rcr=load_json(a.aggregate_receipt); comparison,cr=load_json(a.comparison_receipt)
        envelope=build_envelope(record,rr,receipt,rcr,comparison,cr); outputs=write_outputs(envelope,a.output_dir)
    except RXEPPartialAggregateError as exc:
        print("FAILED:",exc); return 2
    print("RESULT:",VERDICT); print("EXACT PARTIAL AGGREGATE:",EXPECTED["value_decimal"],EXPECTED["unit"]); print(json.dumps(outputs,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
