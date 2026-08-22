#!/usr/bin/env python3
"""ProofGrid v2.11 declared synthetic inventory evidence refresh.

Refreshes the accepted v2.3 three-entry synthetic inventory from 2/3 evidence
covered to 3/3 evidence covered by proving v2.4 source-revision continuity,
v2.8 three-member contribution admission, and v2.10 RXEP aggregate membership.

This is declared-inventory evidence coverage only. It does not establish whole-
building/model completeness, whole-building LCA, scientific validity, or
certification.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
ENGINE_NAME="RegenExcalibur ProofGrid Declared Inventory Evidence Refresh"
ENGINE_VERSION="2.11.0"
VERDICT="DECLARED_SYNTHETIC_INVENTORY_EVIDENCE_REFRESH_3_OF_3_VERIFIABLE"
ZERO="0"*64
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
V23={"record_content":"8e286f5b796eab2b8de325c547b8c87404042478ee110aefeb4fcad8d5965a1a","record_file":"98ea953159818f4f85f7ccfdf73216e5aeb22366fc14c017b4030286141b2be0","receipt":"e6f0ecb4017c7dd742fc8c1b0fd64148390048a5c9c604e6659a387cd888ab4e","receipt_file":"99ab39796c67dc3dfe0dd86972e0e0d3272fa65eba697d9d208f1d21c2d706af","comparison":"597f713088d31d00ce1cc5f81d4200f19fd58da7a7e1149f31c226190a0ade0c","comparison_file":"9fef0f13f10197f47ea824a1fbd8c6188f0e8550acb1dca2be426f395120472d"}
V24={"record_content":"0a9c1e7e8efc6be240315cf04e87904c468b1bb1406f0b1494cb3c0905f37b12","record_file":"15afb8f3515fa2835729c998a9b661138ffe60737ab8d072fd97f3480a3ec168","receipt":"a0d7e212f35d7a816bdd003d842059d6f7fed806e35cdac327a5042933da57d7","receipt_file":"b9a61248bd7c2068c450a767f243482a83a899e8a80762c965236d82398ef1f0","comparison":"7eecdc11851b7d542968ac6f5015e6f8b4297d5bd972b70c103f9ab051f90ccf","comparison_file":"e38e463d3454ab465d1de1bfc0776a84c9eb525dd68a48ed51feb649cc45d384"}
V28={"record_content":"9ad3fe620f995d316ac620998fae9bf6fcd75e72151286cc544edf0c2bdad7e4","record_file":"01b01df63e346148d4d76e8a145a82d80b9b138ea59cc1b647b43af95fd86946","receipt":"6c581cd0a60a051e2efe25924eb6dc1b9bf379fc7a1d7c60d5e9d69d0e082846","receipt_file":"b87433764127ebd53551df81fd98b28fae205ec015fc605f072299dee7fcecba","comparison":"21deb1d90846f441f9f4ff5fc5f95ca12cdc7fd0c1a53fcfc0cb5fd02fe1a7d4","comparison_file":"dd7e6bea0665b34995ea31b2a0661dcf7bdc6bb5db8b1e2fa515494a8ad2f6ec"}
V210={"record_content":"5e36627c3ad5428ff578cf2579ac488772cec3ba860c52a14f32785f1e2f855d","record_file":"e5628402e768f2bd231a266bb319508827cc2b2eaea63d17adbde0d973673b06","receipt":"2ba162ceb12b0205472fe6b3dc97d52bfb8bbad0ef705dc2b798239033838c1a","receipt_file":"99a0c71db67b12681e2bbe3f8f23ef2e4b8f8b9afd4290823bf97b40972c9637","comparison":"5272f5be1605c2e33f9a6bad8b6c37fc8c3e3184082c1c0027c2325c720b22b1","comparison_file":"0189b6c05139a05d7bcde22e3263ad304a1343ccd46159043efde410efa866cb"}
FIRST={"entry_id":"covered-first","element":"1BXL7DJx51bvggyIPU2Xi5","source":"23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6","sid":"b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc"}
SECOND={"entry_id":"covered-second","element":"1CXL7DJx51bvggyIPU2Xi6","source":"14c4be5561131bd6213d45dd0e00064ac916da28f825450133b5dd48d1fcd54d","sid":"75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950"}
THIRD={"entry_id":"uncovered-third","element":"1DXL7DJx51bvggyIPU2Xi7","predecessor":"42443f2f45f9bc122814a07c711cd67e6fc5d9033a7c17bf5ce20be70a24dcd3","successor":"ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d","sid":"2a67655f18b9cd8d776335e886dc324c9911dd9e1090e8852752235ecb958905"}

class InventoryRefreshError(ValueError): pass
def require(c:bool,m:str)->None:
    if not c: raise InventoryRefreshError(m)
def canonical_json_bytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def pretty_json_bytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
def sha256_bytes(v:bytes)->str: return hashlib.sha256(v).hexdigest()
def load(path:Path)->tuple[dict[str,Any],bytes]:
    try: raw=Path(path).read_bytes()
    except FileNotFoundError as e: raise InventoryRefreshError(f"missing file: {path}") from e
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception as e: raise InventoryRefreshError(f"invalid JSON: {path}: {e}") from e
    require(isinstance(obj,dict),f"expected object: {path}"); return obj,raw
def self_hash(obj:dict[str,Any],label:str)->str:
    integ=obj.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content hash")
    shadow=copy.deepcopy(obj); shadow["integrity"]["content_sha256"]=ZERO; require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} content digest mismatch"); return claimed
def receipt_hash(obj:dict[str,Any],label:str,key:str)->str:
    claimed=obj.get(key); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing {key}"); shadow=copy.deepcopy(obj); shadow.pop(key,None); require(sha256_bytes(canonical_json_bytes(shadow))==claimed,f"{label} digest mismatch"); return claimed
def expect_file(raw:bytes,expected:str,label:str)->None: require(sha256_bytes(raw)==expected,f"{label} file identity mismatch")
def load_triplet(root:Path,names:tuple[str,str,str])->tuple:
    a,ar=load(root/names[0]); b,br=load(root/names[1]); c,cr=load(root/names[2]); return a,ar,b,br,c,cr

def verify_v23(root:Path)->dict[str,Any]:
    rec,rr,receipt,rraw,cmp,craw=load_triplet(root,("declared-source-inventory-gap-ledger.json","declared-source-inventory-gap-ledger-receipt.json","v23-independent-comparison-receipt.json"))
    require(self_hash(rec,"v2.3 ledger")==V23["record_content"],"unaccepted v2.3 ledger content"); expect_file(rr,V23["record_file"],"v2.3 ledger")
    require(receipt_hash(receipt,"v2.3 receipt","receipt_sha256")==V23["receipt"],"unaccepted v2.3 receipt"); expect_file(rraw,V23["receipt_file"],"v2.3 receipt")
    require(receipt_hash(cmp,"v2.3 comparison","comparison_receipt_sha256")==V23["comparison"],"unaccepted v2.3 comparison"); expect_file(craw,V23["comparison_file"],"v2.3 comparison")
    require(rec.get("inventory_scope",{}).get("inventory_entry_count")==3,"v2.3 inventory count mismatch"); require(rec.get("coverage",{}).get("covered_entry_count")==2 and rec.get("coverage",{}).get("uncovered_entry_count")==1,"v2.3 coverage state mismatch")
    entries={e["inventory_entry_id"]:e for e in rec.get("entries",[])}; require(set(entries)=={FIRST["entry_id"],SECOND["entry_id"],THIRD["entry_id"]},"v2.3 inventory identities mismatch")
    require(entries[FIRST["entry_id"]]["ifc_source_sha256"]==FIRST["source"] and entries[FIRST["entry_id"]]["semantic_identity_sha256"]==FIRST["sid"],"first inventory evidence mismatch")
    require(entries[SECOND["entry_id"]]["ifc_source_sha256"]==SECOND["source"] and entries[SECOND["entry_id"]]["semantic_identity_sha256"]==SECOND["sid"],"second inventory evidence mismatch")
    t=entries[THIRD["entry_id"]]; require(t["ifc_source_sha256"]==THIRD["predecessor"] and t["element_global_id"]==THIRD["element"],"third predecessor inventory identity mismatch"); require(t["evidence_status"]=="EVIDENCE_UNCOVERED" and t.get("assumed_zero") is False,"v2.3 uncovered state mismatch"); return rec

def verify_v24(root:Path)->dict[str,Any]:
    rec,rr,receipt,rraw,cmp,craw=load_triplet(root,("uncovered-remediation-readiness.json","uncovered-remediation-readiness-receipt.json","v24-independent-comparison-receipt.json"))
    require(self_hash(rec,"v2.4 remediation")==V24["record_content"],"unaccepted v2.4 record"); expect_file(rr,V24["record_file"],"v2.4 record")
    require(receipt_hash(receipt,"v2.4 receipt","receipt_sha256")==V24["receipt"],"unaccepted v2.4 receipt"); expect_file(rraw,V24["receipt_file"],"v2.4 receipt")
    require(receipt_hash(cmp,"v2.4 comparison","comparison_receipt_sha256")==V24["comparison"],"unaccepted v2.4 comparison"); expect_file(craw,V24["comparison_file"],"v2.4 comparison")
    s=rec.get("successor_source",{}); require(s.get("predecessor_source_sha256")==THIRD["predecessor"],"v2.4 predecessor mismatch"); require(s.get("successor_source_sha256")==THIRD["successor"],"v2.4 successor mismatch"); require(s.get("element_global_id")==THIRD["element"],"v2.4 element continuity mismatch"); require(rec.get("assumed_zero") is False and rec.get("certified") is False,"v2.4 state promotion rejected"); return rec

def verify_v28(root:Path)->dict[str,Any]:
    rec,rr,receipt,rraw,cmp,craw=load_triplet(root,("three-member-environmental-contribution-set.json","three-member-environmental-contribution-set-receipt.json","v28-independent-comparison-receipt.json"))
    require(self_hash(rec,"v2.8 set")==V28["record_content"],"unaccepted v2.8 set"); expect_file(rr,V28["record_file"],"v2.8 set")
    require(receipt_hash(receipt,"v2.8 receipt","receipt_sha256")==V28["receipt"],"unaccepted v2.8 receipt"); expect_file(rraw,V28["receipt_file"],"v2.8 receipt")
    require(receipt_hash(cmp,"v2.8 comparison","comparison_receipt_sha256")==V28["comparison"],"unaccepted v2.8 comparison"); expect_file(craw,V28["comparison_file"],"v2.8 comparison")
    require(rec.get("member_count")==3 and rec.get("completeness_status")=="PARTIAL","v2.8 set state mismatch"); by_element={m["semantic_identity"]["element_global_id"]:m for m in rec.get("members",[])}
    for x in (FIRST,SECOND):
        m=by_element.get(x["element"]); require(m and m["semantic_identity_sha256"]==x["sid"] and m["semantic_identity"]["ifc_source_sha256"]==x["source"],f"v2.8 {x['entry_id']} mismatch")
    t=by_element.get(THIRD["element"]); require(t and t["semantic_identity_sha256"]==THIRD["sid"] and t["semantic_identity"]["ifc_source_sha256"]==THIRD["successor"],"v2.8 third successor evidence mismatch"); require(rec.get("aggregation_performed") is False and rec.get("sum_performed") is False,"v2.8 aggregation promotion rejected"); return rec

def verify_v210(root:Path)->dict[str,Any]:
    rec,rr,receipt,rraw,cmp,craw=load_triplet(root,("rxep-three-member-partial-aggregate.json","rxep-three-member-partial-aggregate-receipt.json","v210-independent-comparison-receipt.json"))
    require(self_hash(rec,"v2.10 RXEP")==V210["record_content"],"unaccepted v2.10 RXEP"); expect_file(rr,V210["record_file"],"v2.10 RXEP")
    require(receipt_hash(receipt,"v2.10 receipt","receipt_sha256")==V210["receipt"],"unaccepted v2.10 receipt"); expect_file(rraw,V210["receipt_file"],"v2.10 receipt")
    require(receipt_hash(cmp,"v2.10 comparison","comparison_receipt_sha256")==V210["comparison"],"unaccepted v2.10 comparison"); expect_file(craw,V210["comparison_file"],"v2.10 comparison")
    require(rec.get("member_count")==3 and rec.get("member_semantic_identity_sha256")==[THIRD["sid"],SECOND["sid"],FIRST["sid"]],"v2.10 member identities mismatch"); require(rec.get("measurement",{}).get("value_decimal")=="27229.08943503647325","v2.10 aggregate value mismatch"); require(rec.get("completeness_status")=="PARTIAL" and rec.get("whole_building_lca_claimed") is False,"v2.10 completeness promotion rejected"); return rec

def verify_output(out:dict[str,Any])->None:
    require(out.get("verdict")==VERDICT,"wrong v2.11 verdict"); inv=out.get("inventory_scope",{}); require(inv.get("inventory_scope_type")=="DECLARED_SYNTHETIC_SOURCE_INVENTORY" and inv.get("inventory_entry_count")==3,"inventory state mismatch"); require(inv.get("whole_building_scope") is False and inv.get("whole_model_inventory_claimed") is False,"whole scope promotion rejected")
    cov=out.get("coverage",{}); require(cov.get("covered_entry_count")==3 and cov.get("uncovered_entry_count")==0,"coverage count mismatch"); require(cov.get("coverage_ratio_rational")=={"numerator":"3","denominator":"3"},"coverage ratio mismatch"); require(cov.get("declared_inventory_evidence_coverage_complete") is True,"declared inventory coverage must be complete"); require(cov.get("whole_building_completeness_evaluated") is False,"whole-building completeness promotion rejected")
    entries={e["inventory_entry_id"]:e for e in out.get("entries",[])}; require(set(entries)=={FIRST["entry_id"],SECOND["entry_id"],THIRD["entry_id"]},"entry identities mismatch")
    for x in (FIRST,SECOND):
        e=entries[x["entry_id"]]; require(e["element_global_id"]==x["element"] and e["predecessor_inventory_source_sha256"]==x["source"] and e["covered_successor_source_sha256"]==x["source"] and e["semantic_identity_sha256"]==x["sid"],f"{x['entry_id']} refreshed identity mismatch"); require(e["source_revision_changed"] is False and e["source_revision_continuity_verified"] is True and e["assumed_zero"] is False,f"{x['entry_id']} state mismatch")
    third=entries[THIRD["entry_id"]]; require(third.get("predecessor_inventory_source_sha256")==THIRD["predecessor"],"third predecessor mismatch"); require(third.get("covered_successor_source_sha256")==THIRD["successor"],"third successor mismatch"); require(third.get("element_global_id")==THIRD["element"],"third element mismatch"); require(third.get("semantic_identity_sha256")==THIRD["sid"],"third semantic identity mismatch"); require(third.get("source_revision_continuity_verified") is True and third.get("source_revision_changed") is True,"source continuity missing"); require(third.get("assumed_zero") is False,"third assumed-zero promotion rejected")
    for key in ("whole_building_completeness_evaluated","whole_building_lca_claimed","declared_scope_complete_claimed","missing_contributions_are_zero","uncovered_inventory_is_zero","aggregation_recomputed","scientific_validation_performed","professional_review_performed","certified"): require(out.get(key) is False,f"{key} promotion rejected")

def build_refresh(v23:dict[str,Any],v24:dict[str,Any],v28:dict[str,Any],v210:dict[str,Any])->dict[str,Any]:
    entries=[]
    for x in (FIRST,SECOND): entries.append({"inventory_entry_id":x["entry_id"],"element_global_id":x["element"],"predecessor_inventory_source_sha256":x["source"],"covered_successor_source_sha256":x["source"],"source_revision_changed":False,"source_revision_continuity_verified":True,"evidence_status":"EVIDENCE_COVERED","coverage_source":"ACCEPTED_V2_8_SEMANTIC_CONTRIBUTION","semantic_identity_sha256":x["sid"],"assumed_zero":False})
    entries.append({"inventory_entry_id":THIRD["entry_id"],"element_global_id":THIRD["element"],"predecessor_inventory_source_sha256":THIRD["predecessor"],"covered_successor_source_sha256":THIRD["successor"],"source_revision_changed":True,"source_revision_continuity_verified":True,"evidence_status":"EVIDENCE_COVERED_VIA_SUCCESSOR_SOURCE","coverage_source":"ACCEPTED_V2_8_SEMANTIC_CONTRIBUTION","semantic_identity_sha256":THIRD["sid"],"assumed_zero":False}); entries.sort(key=lambda e:e["inventory_entry_id"])
    out={"schema_version":"1.0","record_type":"ProofGridDeclaredSyntheticInventoryEvidenceRefresh","verdict":VERDICT,"inventory_scope":{"inventory_id":v23["inventory_scope"]["inventory_id"],"inventory_scope_type":"DECLARED_SYNTHETIC_SOURCE_INVENTORY","inventory_entry_count":3,"whole_building_scope":False,"whole_model_inventory_claimed":False},"coverage":{"covered_entry_count":3,"uncovered_entry_count":0,"coverage_ratio_rational":{"numerator":"3","denominator":"3"},"rounded_decimal_coverage_authority_present":False,"declared_inventory_evidence_coverage_complete":True,"whole_building_completeness_evaluated":False},"entries":entries,"aggregate_evidence":{"rxep_record_content_sha256":V210["record_content"],"value_decimal":"27229.08943503647325","unit":"kg CO2 eqv.","member_count":3,"member_semantic_identity_sha256":[THIRD["sid"],SECOND["sid"],FIRST["sid"]],"completeness_status":"PARTIAL","whole_building_lca_claimed":False},"parent_evidence":{"v23_inventory_content_sha256":V23["record_content"],"v24_remediation_content_sha256":V24["record_content"],"v28_set_content_sha256":V28["record_content"],"v210_rxep_content_sha256":V210["record_content"]},"limitations":["3/3 refers only to the three explicitly declared synthetic inventory entries.","The third entry is covered through an accepted successor source; the predecessor source remains a historical uncovered revision.","Declared inventory evidence coverage does not establish whole-building/model completeness or a whole-building LCA."],"whole_building_completeness_evaluated":False,"whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"uncovered_inventory_is_zero":False,"aggregation_recomputed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,"integrity":{"content_sha256":ZERO,"canonicalization":CANON,"signature":None}}
    out["integrity"]["content_sha256"]=sha256_bytes(canonical_json_bytes(out)); verify_output(out); return out

def build_receipt(out:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"inventory_entry_count":3,"covered_entry_count":3,"uncovered_entry_count":0,"coverage_ratio_rational":{"numerator":"3","denominator":"3"},"declared_inventory_evidence_coverage_complete":True,"whole_building_completeness_evaluated":False,"whole_building_lca_claimed":False,"record_content_sha256":out["integrity"]["content_sha256"],"record_file_sha256":sha256_bytes(raw),"third_predecessor_source_sha256":THIRD["predecessor"],"third_successor_source_sha256":THIRD["successor"],"third_semantic_identity_sha256":THIRD["sid"],"aggregate_rxep_content_sha256":V210["record_content"],"certified":False}; r["receipt_sha256"]=sha256_bytes(canonical_json_bytes(r)); return r

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--v23-dir",type=Path,required=True); p.add_argument("--v24-dir",type=Path,required=True); p.add_argument("--v28-dir",type=Path,required=True); p.add_argument("--v210-dir",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(argv)
    try:
        v23=verify_v23(a.v23_dir); v24=verify_v24(a.v24_dir); v28=verify_v28(a.v28_dir); v210=verify_v210(a.v210_dir); out=build_refresh(v23,v24,v28,v210); a.output_dir.mkdir(parents=True,exist_ok=True); rp=a.output_dir/"declared-inventory-evidence-refresh.json"; rr=a.output_dir/"declared-inventory-evidence-refresh-receipt.json"; raw=pretty_json_bytes(out); rp.write_bytes(raw); rr.write_bytes(pretty_json_bytes(build_receipt(out,raw)))
    except Exception as e:
        print(f"FAILED: {e}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print("DECLARED INVENTORY COVERAGE: 3/3"); print("WHOLE-BUILDING COMPLETENESS: NOT EVALUATED"); return 0
if __name__=="__main__": raise SystemExit(main())
