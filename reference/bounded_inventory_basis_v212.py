#!/usr/bin/env python3
"""ProofGrid v2.12 bounded synthetic inventory basis closure.

Verifies that the accepted v2.11 3/3 declared-inventory evidence refresh matches
one immutable three-member synthetic test-scope manifest exactly once. This gate
proves completeness only relative to that manifest; it does not establish whole-
model or whole-building completeness.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
ENGINE_NAME="RegenExcalibur ProofGrid Bounded Inventory Basis Closure"
ENGINE_VERSION="2.12.0"
VERDICT="BOUNDED_SYNTHETIC_INVENTORY_BASIS_CLOSURE_VERIFIABLE"
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO="0"*64
EXPECTED_V211={
 "record_content":"33756f6fe4dd9c2e63ca4f2711a65ee193d2e75c9983a17ec7e60a4fa707fce9",
 "record_file":"47ced747615c54fb2e22d5ac901d67769e13879a719221e09e52301d40333374",
 "receipt":"2ab5a30fa3d985f744db8d3604c1d5dd54d5410289fa3328686d468c19783a7a",
 "receipt_file":"15bc0abf14ad12001b7449a19ab04f2b2690cf0ae01fdf2c59a33a43d4640f85",
 "comparison":"220a640f57f5b9ca4be1e05508b3f296ae7fe838f66084736810ae582453920f",
 "comparison_file":"be80a6a067c500f8c612c0a2560d34b805487fd93d8b8f52eacea5b890c356f1"
}
EXPECTED_MANIFEST_ID="proofgrid:v212:bounded-synthetic-test-inventory"
EXPECTED_MEMBERS={
 "covered-first":("1BXL7DJx51bvggyIPU2Xi5","23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6","23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6","b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc"),
 "covered-second":("1CXL7DJx51bvggyIPU2Xi6","14c4be5561131bd6213d45dd0e00064ac916da28f825450133b5dd48d1fcd54d","14c4be5561131bd6213d45dd0e00064ac916da28f825450133b5dd48d1fcd54d","75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950"),
 "uncovered-third":("1DXL7DJx51bvggyIPU2Xi7","42443f2f45f9bc122814a07c711cd67e6fc5d9033a7c17bf5ce20be70a24dcd3","ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d","2a67655f18b9cd8d776335e886dc324c9911dd9e1090e8852752235ecb958905")
}

class BasisClosureError(ValueError): pass
def require(c:bool,m:str)->None:
    if not c: raise BasisClosureError(m)
def canonical_json_bytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def pretty_json_bytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
def sha256_bytes(v:bytes)->str: return hashlib.sha256(v).hexdigest()
def load(path:Path)->tuple[dict[str,Any],bytes]:
    try: raw=Path(path).read_bytes()
    except FileNotFoundError as e: raise BasisClosureError(f"missing file: {path}") from e
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception as e: raise BasisClosureError(f"invalid JSON: {path}: {e}") from e
    require(isinstance(obj,dict),f"expected JSON object: {path}"); return obj,raw
def self_hash(obj:dict[str,Any],label:str)->str:
    integ=obj.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content hash")
    shadow=copy.deepcopy(obj); shadow["integrity"]["content_sha256"]=ZERO; require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} content digest mismatch"); return claimed
def receipt_hash(obj:dict[str,Any],label:str,key:str)->str:
    claimed=obj.get(key); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {key}"); shadow=copy.deepcopy(obj); shadow.pop(key,None); require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} digest mismatch"); return claimed

def verify_manifest(manifest:dict[str,Any])->dict[str,dict[str,Any]]:
    require(manifest.get("schema_version")=="1.0","manifest schema mismatch")
    require(manifest.get("manifest_id")==EXPECTED_MANIFEST_ID,"manifest id mismatch")
    require(manifest.get("basis_scope_type")=="BOUNDED_SYNTHETIC_TEST_INVENTORY","basis scope mismatch")
    require(manifest.get("membership_closed") is True,"manifest membership must be closed")
    require(manifest.get("member_count")==3,"manifest member count must be 3")
    members=manifest.get("members"); require(isinstance(members,list) and len(members)==3,"manifest must contain exactly three members")
    by_id={}
    for m in members:
        mid=m.get("inventory_entry_id"); require(mid in EXPECTED_MEMBERS,f"unexpected manifest member: {mid}"); require(mid not in by_id,f"duplicate manifest member: {mid}")
        expected=EXPECTED_MEMBERS[mid]
        require((m.get("element_global_id"),m.get("predecessor_inventory_source_sha256"),m.get("covered_successor_source_sha256"),m.get("semantic_identity_sha256"))==expected,f"manifest member identity mismatch: {mid}")
        by_id[mid]=m
    require(set(by_id)==set(EXPECTED_MEMBERS),"manifest membership incomplete")
    for key in ("whole_model_inventory_claimed","whole_model_completeness_evaluated","whole_building_scope","whole_building_completeness_evaluated","whole_building_lca_claimed"):
        require(manifest.get(key) is False,f"manifest {key} promotion rejected")
    return by_id

def verify_v211(root:Path)->tuple[dict[str,Any],dict[str,Any]]:
    rec,rr=load(root/"declared-inventory-evidence-refresh.json"); receipt,rraw=load(root/"declared-inventory-evidence-refresh-receipt.json"); cmp,craw=load(root/"v211-independent-comparison-receipt.json")
    require(self_hash(rec,"v2.11 refresh")==EXPECTED_V211["record_content"],"unaccepted v2.11 record"); require(sha256_bytes(rr)==EXPECTED_V211["record_file"],"unaccepted v2.11 record file")
    require(receipt_hash(receipt,"v2.11 receipt","receipt_sha256")==EXPECTED_V211["receipt"],"unaccepted v2.11 receipt"); require(sha256_bytes(rraw)==EXPECTED_V211["receipt_file"],"unaccepted v2.11 receipt file")
    require(receipt_hash(cmp,"v2.11 comparison","comparison_receipt_sha256")==EXPECTED_V211["comparison"],"unaccepted v2.11 comparison"); require(sha256_bytes(craw)==EXPECTED_V211["comparison_file"],"unaccepted v2.11 comparison file")
    cov=rec.get("coverage",{}); require(cov.get("covered_entry_count")==3 and cov.get("uncovered_entry_count")==0,"v2.11 coverage mismatch"); require(cov.get("coverage_ratio_rational")=={"numerator":"3","denominator":"3"},"v2.11 rational coverage mismatch"); require(cov.get("declared_inventory_evidence_coverage_complete") is True,"v2.11 declared inventory coverage not complete")
    require(rec.get("whole_building_completeness_evaluated") is False and rec.get("whole_building_lca_claimed") is False,"v2.11 whole-building promotion rejected")
    return rec,receipt

def verify_closure(out:dict[str,Any])->None:
    require(out.get("verdict")==VERDICT,"wrong closure verdict")
    basis=out.get("basis",{}); require(basis.get("basis_scope_type")=="BOUNDED_SYNTHETIC_TEST_INVENTORY","closure basis scope mismatch"); require(basis.get("manifest_member_count")==3 and basis.get("manifest_membership_closed") is True,"closure manifest state mismatch")
    require(out.get("v211_covered_member_count")==3,"closure covered member count mismatch"); require(out.get("one_to_one_membership_match") is True,"one-to-one membership not proven"); require(out.get("bounded_scope_membership_complete") is True,"bounded scope membership incomplete"); require(out.get("bounded_scope_evidence_coverage_complete") is True,"bounded scope evidence incomplete")
    require(out.get("coverage_ratio_rational")=={"numerator":"3","denominator":"3"},"closure coverage ratio mismatch")
    members=out.get("members"); require(isinstance(members,list) and len(members)==3,"closure member count mismatch")
    by_id={m["inventory_entry_id"]:m for m in members}; require(set(by_id)==set(EXPECTED_MEMBERS),"closure members mismatch")
    for mid,expected in EXPECTED_MEMBERS.items():
        m=by_id[mid]; require((m.get("element_global_id"),m.get("predecessor_inventory_source_sha256"),m.get("covered_successor_source_sha256"),m.get("semantic_identity_sha256"))==expected,f"closure member identity mismatch: {mid}")
    for key in ("whole_model_inventory_claimed","whole_model_completeness_evaluated","whole_building_scope","whole_building_completeness_evaluated","whole_building_lca_claimed","declared_scope_complete_claimed","missing_contributions_are_zero","scientific_validation_performed","professional_review_performed","certified"):
        require(out.get(key) is False,f"closure {key} promotion rejected")

def build_closure(manifest:dict[str,Any],manifest_raw:bytes,refresh:dict[str,Any])->dict[str,Any]:
    declared=verify_manifest(manifest)
    covered={e["inventory_entry_id"]:e for e in refresh.get("entries",[])}; require(set(covered)==set(declared),"v2.11/manifest membership mismatch")
    members=[]
    for mid in sorted(declared):
        d=declared[mid]; r=covered[mid]
        for key in ("element_global_id","predecessor_inventory_source_sha256","covered_successor_source_sha256","semantic_identity_sha256"):
            require(r.get(key)==d.get(key),f"v2.11/manifest {key} mismatch: {mid}")
        require(r.get("assumed_zero") is False,f"manifest member assumed zero: {mid}")
        members.append(copy.deepcopy(d))
    out={"schema_version":"1.0","record_type":"ProofGridBoundedSyntheticInventoryBasisClosure","verdict":VERDICT,"basis":{"manifest_id":manifest["manifest_id"],"basis_scope_type":manifest["basis_scope_type"],"manifest_file_sha256":sha256_bytes(manifest_raw),"manifest_member_count":3,"manifest_membership_closed":True},"parent_v211":{"record_content_sha256":EXPECTED_V211["record_content"],"receipt_sha256":EXPECTED_V211["receipt"],"comparison_receipt_sha256":EXPECTED_V211["comparison"]},"members":members,"v211_covered_member_count":3,"coverage_ratio_rational":{"numerator":"3","denominator":"3"},"one_to_one_membership_match":True,"bounded_scope_membership_complete":True,"bounded_scope_evidence_coverage_complete":True,"whole_model_inventory_claimed":False,"whole_model_completeness_evaluated":False,"whole_building_scope":False,"whole_building_completeness_evaluated":False,"whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,"limitations":["Completeness applies only to the immutable three-member bounded synthetic test manifest.","This gate does not establish a complete real IFC model or whole-building inventory.","No scientific validity, professional review, regulatory approval, or certification is established."],"integrity":{"content_sha256":ZERO,"canonicalization":CANON,"signature":None}}
    out["integrity"]["content_sha256"]=sha256_bytes(canonical_json_bytes(out)); verify_closure(out); return out

def build_receipt(out:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"manifest_id":EXPECTED_MANIFEST_ID,"manifest_file_sha256":out["basis"]["manifest_file_sha256"],"manifest_member_count":3,"v211_covered_member_count":3,"coverage_ratio_rational":{"numerator":"3","denominator":"3"},"one_to_one_membership_match":True,"bounded_scope_membership_complete":True,"bounded_scope_evidence_coverage_complete":True,"whole_model_inventory_claimed":False,"whole_building_lca_claimed":False,"record_content_sha256":out["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw),"certified":False}; r["receipt_sha256"]=sha256_bytes(canonical_json_bytes(r)); return r

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--manifest",type=Path,required=True); p.add_argument("--v211-dir",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(argv)
    try:
        manifest,mraw=load(a.manifest); refresh,_=verify_v211(a.v211_dir); out=build_closure(manifest,mraw,refresh); a.output_dir.mkdir(parents=True,exist_ok=True); rp=a.output_dir/"bounded-inventory-basis-closure.json"; rr=a.output_dir/"bounded-inventory-basis-closure-receipt.json"; raw=pretty_json_bytes(out); rp.write_bytes(raw); rr.write_bytes(pretty_json_bytes(build_receipt(out,raw)))
    except Exception as e:
        print(f"FAILED: {e}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print("BOUNDED SYNTHETIC SCOPE MEMBERSHIP: COMPLETE 3/3"); print("WHOLE MODEL/BUILDING COMPLETENESS: NOT EVALUATED"); return 0
if __name__=="__main__": raise SystemExit(main())
