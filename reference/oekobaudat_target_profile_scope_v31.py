#!/usr/bin/env python3
"""ProofGrid v3.1 target-scoped ÖKOBAUDAT profile evidence.

Consumes the unmodified official validator event stream from batch validation of
the current package plus one historical predecessor reference. It does not
suppress events: all events are normalized and attributed to the current target
or historical predecessor. Compatibility is asserted only for the current
3.1 target when its own error count is zero.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any

VERDICT="OEKOBAUDAT_TARGET_PROFILE_WITH_HISTORICAL_REFERENCE_CLOSURE_VERIFIABLE"
CURRENT="8347f9a7-f4ec-4a36-a266-a0281f5fd16d"
PREDECESSOR="71667cf3-ede8-42d2-b0ff-6f1071ad3b86"
PREDECESSOR_VERSION="00.04.000"
PREDECESSOR_SHA="694f7fe93919ae3889c6958511a85de3f042747ccc518174aa57e1939cb73248"
PREDECESSOR_SIZE=39883
PROFILE_NAME="EPD 1.2 ÖKOBAUDAT"
PROFILE_VERSION="3.8.0"
ZERO="0"*64
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
class ScopeError(ValueError): pass
def require(c,m):
    if not c: raise ScopeError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def subject(reference:str|None)->str:
    ref=reference or ""
    if CURRENT in ref: return "TARGET_CURRENT_DATASET"
    if PREDECESSOR in ref: return "HISTORICAL_PREDECESSOR_CONTEXT"
    return "UNATTRIBUTED"
def normalize_event(e:dict[str,Any])->dict[str,Any]:
    return {"severity":e.get("severity"),"type":e.get("type"),"aspect":e.get("aspect"),"aspect_description":e.get("aspect_description"),"message":e.get("message"),"alt_message":e.get("alt_message"),"subject":subject(e.get("reference"))}
def counts(events:list[dict[str,Any]],subj:str)->dict[str,int]:
    selected=[e for e in events if e["subject"]==subj]
    return {"event_count":len(selected),"error_count":sum(e.get("severity")=="ERROR" for e in selected),"warning_count":sum(e.get("severity")=="WARNING" for e in selected)}
def build(raw:dict[str,Any],closure:dict[str,Any])->dict[str,Any]:
    require(raw.get("profile_name")==PROFILE_NAME,"wrong official profile name"); require(raw.get("profile_version")==PROFILE_VERSION,"wrong official profile version")
    require(raw.get("error_count")==13 and raw.get("warning_count")==20 and raw.get("event_count")==33,"unexpected exact batch validation counts"); require(raw.get("is_positive") is False,"batch unexpectedly positive")
    events=[normalize_event(e) for e in raw.get("events",[])]; require(len(events)==33,"normalized event count mismatch")
    t=counts(events,"TARGET_CURRENT_DATASET"); p=counts(events,"HISTORICAL_PREDECESSOR_CONTEXT"); u=counts(events,"UNATTRIBUTED")
    require(t=={"event_count":12,"error_count":0,"warning_count":12},f"target event counts changed: {t}")
    require(p=={"event_count":21,"error_count":13,"warning_count":8},f"predecessor event counts changed: {p}")
    require(u=={"event_count":0,"error_count":0,"warning_count":0},f"unattributed events present: {u}")
    supplements=closure.get("supplements"); require(isinstance(supplements,list) and len(supplements)==1,"closure supplement mismatch"); s=supplements[0]
    require(s.get("uuid")==PREDECESSOR and s.get("version")==PREDECESSOR_VERSION,"closure predecessor identity mismatch"); require(s.get("process_sha256")==PREDECESSOR_SHA and s.get("process_size_bytes")==PREDECESSOR_SIZE,"closure predecessor byte identity mismatch"); require(s.get("source_authority") is False and s.get("validation_context_only") is True,"closure authority promotion rejected")
    record={"schema_version":"1.0","record_type":"ProofGridTargetScopedOekobaudatProfileEvidence","verdict":VERDICT,"profile":{"name":PROFILE_NAME,"version":PROFILE_VERSION,"validator_library":"com.okworx.ilcd.validation:ilcd-validation:2.12.2"},"batch":{"is_positive":False,"error_count":13,"warning_count":20,"event_count":33},"target":{"dataset_uuid":CURRENT,"profile_compatible":True,**t},"historical_predecessor":{"dataset_uuid":PREDECESSOR,"dataset_version":PREDECESSOR_VERSION,"process_sha256":PREDECESSOR_SHA,"process_size_bytes":PREDECESSOR_SIZE,"profile_compatible":False,"source_authority":False,**p},"unattributed":u,"validation_closure":{"supplement_used":True,"canonical_source_package_mutated":False,"supplement_becomes_source_authority":False,"strategy":"OFFICIAL_BATCH_VALIDATION_WITH_TARGET_SCOPED_EVENT_CLASSIFICATION"},"normalized_events":events,"all_validator_events_preserved_as_normalized_evidence":True,"scientific_validity_inferred":False,"professional_suitability_inferred":False,"certification_authority_inferred":False,"integrity":{"content_sha256":ZERO,"canonicalization":CANON,"signature":None}}
    record["integrity"]["content_sha256"]=sha(cbytes(record)); return record
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--profile-result",type=Path,required=True); p.add_argument("--closure-manifest",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    try:
        raw=json.loads(a.profile_result.read_text(encoding="utf-8")); closure=json.loads(a.closure_manifest.read_text(encoding="utf-8")); out=build(raw,closure); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(pbytes(out))
    except Exception as exc: print(f"FAILED: {exc}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print("TARGET_ERRORS=0"); print("TARGET_WARNINGS=12"); print("HISTORICAL_ERRORS_PRESERVED=13"); print("BATCH_POSITIVE=false"); return 0
if __name__=="__main__": raise SystemExit(main())
