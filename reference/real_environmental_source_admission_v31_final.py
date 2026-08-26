#!/usr/bin/env python3
"""ProofGrid v3.1 final real environmental-source admission.

Composes the proven v3.1 source/rights/identity parser with target-scoped
ÖKOBAUDAT profile evidence. The current dataset may be profile-compatible under
an explicit historical reference-closure context even when the validator batch
is non-positive because the historical context record itself predates the
modern profile. All historical errors remain preserved in canonical evidence.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from typing import Any
from reference import real_environmental_source_admission_v31 as base
from reference import oekobaudat_target_profile_scope_v31 as scope

ENGINE_NAME="RegenExcalibur ProofGrid Final Real ÖKOBAUDAT Environmental Source Admission"
ENGINE_VERSION="3.1.0"
VERDICT=base.VERDICT
ZERO="0"*64
CANON=base.CANON
CLOSURE_SHA="694f7fe93919ae3889c6958511a85de3f042747ccc518174aa57e1939cb73248"
CLOSURE_SIZE=39883
CLOSURE_UUID="71667cf3-ede8-42d2-b0ff-6f1071ad3b86"
CLOSURE_VERSION="00.04.000"

class FinalAdmissionError(base.AdmissionError): pass
def require(c,m):
    if not c: raise FinalAdmissionError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def load(path:Path):
    raw=Path(path).read_bytes(); obj=json.loads(raw.decode()); require(isinstance(obj,dict),f"expected JSON object: {path}"); return obj,raw

def verify_self_hash(record:dict[str,Any],label:str)->str:
    integ=record.get("integrity"); require(isinstance(integ,dict),f"{label} missing integrity"); claimed=integ.get("content_sha256"); require(isinstance(claimed,str) and len(claimed)==64,f"{label} missing content SHA")
    shadow=copy.deepcopy(record); shadow["integrity"]["content_sha256"]=ZERO
    require(sha(cbytes(shadow))==claimed,f"{label} content digest mismatch"); return claimed

def verify_closure_manifest(c:dict[str,Any])->dict[str,Any]:
    require(c.get("manifest_version")=="3.1.0","closure manifest version mismatch"); require(c.get("role")=="VALIDATION_ONLY_REFERENCE_CLOSURE","closure role mismatch")
    target=c.get("target",{}); require(target.get("uuid")==base.EXPECTED["uuid"] and target.get("version")==base.EXPECTED["version"],"closure target identity mismatch"); require(target.get("process_sha256")==base.EXPECTED["process_sha256"],"closure target digest mismatch")
    supplements=c.get("supplements"); require(isinstance(supplements,list) and len(supplements)==1,"closure must contain exactly one supplement"); s=supplements[0]
    require(s.get("uuid")==CLOSURE_UUID and s.get("version")==CLOSURE_VERSION,"closure predecessor identity mismatch"); require(s.get("process_sha256")==CLOSURE_SHA and s.get("process_size_bytes")==CLOSURE_SIZE,"closure predecessor byte identity mismatch"); require(s.get("source_authority") is False and s.get("validation_context_only") is True,"closure authority promotion rejected")
    method=c.get("validation_method",{}); require(method.get("validator_library")=="com.okworx.ilcd.validation:ilcd-validation:2.12.2","closure validator mismatch"); require(method.get("profile")=="com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0","closure profile mismatch"); require(method.get("strategy")=="OFFICIAL_BATCH_VALIDATION_WITH_TARGET_SCOPED_EVENT_CLASSIFICATION","closure strategy mismatch"); require(method.get("canonical_source_package_mutated") is False and method.get("supplement_becomes_source_authority") is False and method.get("all_validator_events_preserved") is True,"closure method overclaim")
    diagnostic=c.get("diagnostic_control",{}).get("with_supplement",{}); require(diagnostic=={"batch_error_count":13,"batch_warning_count":20,"batch_event_count":33,"target_error_count":0,"target_warning_count":12,"predecessor_error_count":13,"predecessor_warning_count":8,"unattributed_event_count":0},"closure diagnostic contract mismatch")
    boundary=c.get("claim_boundary",{}); require(boundary.get("target_profile_compatible_under_reference_closure") is True,"target closure compatibility missing"); require(boundary.get("closure_supplement_profile_compatible") is False and boundary.get("batch_is_positive") is False and boundary.get("historical_errors_suppressed") is False,"closure/batch overclaim")
    return {"predecessor_uuid":CLOSURE_UUID,"predecessor_version":CLOSURE_VERSION,"predecessor_process_sha256":CLOSURE_SHA,"predecessor_process_size_bytes":CLOSURE_SIZE,"role":"VALIDATION_ONLY_REFERENCE_CLOSURE"}

def verify_target_profile(p:dict[str,Any])->dict[str,Any]:
    require(p.get("verdict")==scope.VERDICT,"wrong target-scoped profile verdict"); verify_self_hash(p,"target-scoped profile evidence")
    prof=p.get("profile",{}); require(prof.get("name")==scope.PROFILE_NAME and prof.get("version")==scope.PROFILE_VERSION,"target profile identity mismatch")
    batch=p.get("batch",{}); require(batch=={"is_positive":False,"error_count":13,"warning_count":20,"event_count":33},"batch profile evidence mismatch")
    target=p.get("target",{}); require(target.get("dataset_uuid")==base.EXPECTED["uuid"],"target profile dataset mismatch"); require(target.get("profile_compatible") is True and target.get("error_count")==0 and target.get("warning_count")==12 and target.get("event_count")==12,"target profile result mismatch")
    pred=p.get("historical_predecessor",{}); require(pred.get("dataset_uuid")==CLOSURE_UUID and pred.get("dataset_version")==CLOSURE_VERSION and pred.get("process_sha256")==CLOSURE_SHA,"target profile predecessor mismatch"); require(pred.get("profile_compatible") is False and pred.get("source_authority") is False and pred.get("error_count")==13 and pred.get("warning_count")==8 and pred.get("event_count")==21,"historical profile result mismatch")
    require(p.get("unattributed")=={"event_count":0,"error_count":0,"warning_count":0},"unattributed validator events present"); vc=p.get("validation_closure",{}); require(vc.get("supplement_used") is True and vc.get("canonical_source_package_mutated") is False and vc.get("supplement_becomes_source_authority") is False,"validation closure promotion rejected"); require(p.get("all_validator_events_preserved_as_normalized_evidence") is True,"validator events not preserved")
    events=p.get("normalized_events"); require(isinstance(events,list) and len(events)==33,"normalized validator event evidence mismatch")
    return {"profile_name":scope.PROFILE_NAME,"profile_version":scope.PROFILE_VERSION,"target_profile_compatible":True,"target_error_count":0,"target_warning_count":12,"target_event_count":12,"batch_profile_positive":False,"batch_error_count":13,"batch_warning_count":20,"batch_event_count":33,"historical_predecessor_error_count":13,"historical_predecessor_warning_count":8,"historical_errors_preserved":True,"validation_closure_supplement_used":True,"validation_closure_predecessor_sha256":CLOSURE_SHA,"all_validator_events_preserved":True,"target_profile_evidence_content_sha256":p["integrity"]["content_sha256"]}

def build_record(source,package,process_bytes,terms,extended,target_profile,closure):
    base.verify_manifest(source); base.verify_package_manifest(package); base.verify_external_bytes(terms,extended); process=base.parse_process(process_bytes); closure_summary=verify_closure_manifest(closure); profile_summary=verify_target_profile(target_profile); discrepancy=bool(process["declared_reference"]["source_internal_name_differs_from_process_title"])
    record={"schema_version":"1.0","record_type":"ProofGridRealEnvironmentalSourceAdmission","verdict":VERDICT,"source":{"provider":"ÖKOBAUDAT","dataset_uuid":base.EXPECTED["uuid"],"dataset_version":base.EXPECTED["version"],"package_content_manifest_sha256":base.EXPECTED["package_content_manifest_sha256"],"package_member_count":base.EXPECTED["package_member_count"],"target_process_path":base.EXPECTED["process_path"],"target_process_sha256":base.EXPECTED["process_sha256"],"terms_sha256":base.EXPECTED["terms_sha256"],"extended_view_sha256":base.EXPECTED["extended_sha256"],"zip_wrapper_sha256_is_authority":False},"dataset_identity":process,"rights":{"read_use":"ALLOWED","storage_for_analysis":"ALLOWED","transformation_for_analysis":"ALLOWED","commercial_analysis_use":"ALLOWED_BY_PUBLISHED_UNRESTRICTED_USE_TERMS","unmodified_redistribution":"ALLOWED_WITH_SOURCE_ATTRIBUTION","modified_or_raw_redistribution":"UNKNOWN_REQUIRES_SEPARATE_EVIDENCE","source_attribution_required_for_unmodified_redistribution":True},"conformance":{"format":"ILCD+EPD v1.2","official_oekobaudat_profile":profile_summary,"profile_validation_performed":True,"profile_compatible":True,"compatibility_scope":"TARGET_CURRENT_DATASET_UNDER_EXPLICIT_HISTORICAL_REFERENCE_CLOSURE","batch_profile_positive":False,"historical_reference_closure":closure_summary},"admission":{"admitted_for_normalization":True,"mapping_eligible":False,"mapping_block_reason":"EXPLICIT_SUITABILITY_REVIEW_REQUIRED","source_internal_naming_discrepancy_present":discrepancy,"impact_calculation_allowed_by_this_record":False},"authority_boundaries":{"scientific_validity_proven_by_admission":False,"professional_suitability_proven_by_admission":False,"regulator_acceptance_implied":False,"certified":False,"building_result_reviewed":False,"ifc_mapping_performed":False,"building_impact_calculation_performed":False},"limitations":["Admission establishes exact-source rights, identity, and target-scoped format/profile conformance only.","Official batch validation remains non-positive because the historical predecessor validation context predates the modern profile; its 13 errors are preserved and are not attributed to the current dataset.","The current dataset has zero profile errors and 12 C4-module warnings under the explicit historical reference closure.","The source reference-flow short description is preserved verbatim; its naming differs from the process title and requires explicit suitability review before mapping.","Published dataset third-party review metadata is source metadata and is not independent review of any future ProofGrid building result.","No IFC mapping, building impact calculation, whole-building completeness, regulator acceptance, or certification follows from this record."],"integrity":{"content_sha256":ZERO,"canonicalization":CANON,"signature":None}}
    record["integrity"]["content_sha256"]=sha(cbytes(record)); base.validate_record(record); require(record["conformance"]["batch_profile_positive"] is False,"batch profile promotion rejected"); return record

def make_receipt(record,raw):
    p=record["conformance"]["official_oekobaudat_profile"]
    receipt={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"record_content_sha256":record["integrity"]["content_sha256"],"record_file_sha256":sha(raw),"dataset_uuid":base.EXPECTED["uuid"],"dataset_version":base.EXPECTED["version"],"package_content_manifest_sha256":base.EXPECTED["package_content_manifest_sha256"],"target_process_sha256":base.EXPECTED["process_sha256"],"terms_sha256":base.EXPECTED["terms_sha256"],"extended_view_sha256":base.EXPECTED["extended_sha256"],"profile_validation_performed":True,"profile_compatible":True,"compatibility_scope":"TARGET_CURRENT_DATASET_UNDER_EXPLICIT_HISTORICAL_REFERENCE_CLOSURE","target_profile_error_count":p["target_error_count"],"target_profile_warning_count":p["target_warning_count"],"batch_profile_positive":False,"batch_profile_error_count":p["batch_error_count"],"historical_errors_preserved":True,"validation_closure_predecessor_sha256":CLOSURE_SHA,"admitted_for_normalization":True,"mapping_eligible":False,"certified":False}; receipt["receipt_sha256"]=sha(cbytes(receipt)); return receipt

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--source-manifest",type=Path,required=True); p.add_argument("--package-manifest",type=Path,required=True); p.add_argument("--process-xml",type=Path,required=True); p.add_argument("--terms-page",type=Path,required=True); p.add_argument("--extended-view",type=Path,required=True); p.add_argument("--target-profile-result",type=Path,required=True); p.add_argument("--validation-closure-manifest",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(argv)
    try:
        source,_=load(a.source_manifest); package,_=load(a.package_manifest); target_profile,_=load(a.target_profile_result); closure,_=load(a.validation_closure_manifest); record=build_record(source,package,a.process_xml.read_bytes(),a.terms_page.read_bytes(),a.extended_view.read_bytes(),target_profile,closure); a.output_dir.mkdir(parents=True,exist_ok=True); raw=pbytes(record); (a.output_dir/"real-environmental-source-admission.json").write_bytes(raw); receipt=make_receipt(record,raw); (a.output_dir/"real-environmental-source-admission-receipt.json").write_bytes(pbytes(receipt))
    except Exception as exc: print(f"FAILED: {exc}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print("TARGET_PROFILE_COMPATIBLE=true"); print("BATCH_PROFILE_POSITIVE=false"); print("HISTORICAL_ERRORS_PRESERVED=13"); print("ADMITTED_FOR_NORMALIZATION=true"); print("MAPPING_ELIGIBLE=false"); return 0
if __name__=="__main__": raise SystemExit(main())
