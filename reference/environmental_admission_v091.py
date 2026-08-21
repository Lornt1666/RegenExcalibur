#!/usr/bin/env python3
"""ProofGrid v0.9.1 exact-stack admission consumer for downstream gates."""
from __future__ import annotations
from datetime import datetime, timezone
import argparse, json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from reference import environmental_admission as base  # noqa: E402
from reference import source_import  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Declaration Admission"
ENGINE_VERSION = "0.9.1"
VERDICT = "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE"
ROUTER_NAME=base.ROUTER_NAME; ROUTER_VERSION=base.ROUTER_VERSION; ROUTER_PROFILE=base.ROUTER_PROFILE
FORMAT_NAME=base.FORMAT_NAME; EPD_2019_NS=base.EPD_2019_NS; PROCESS_NS=base.PROCESS_NS
V12_ROUTE=base.V12_ROUTE; V13_ROUTE=base.V13_ROUTE; V12_CLAIM=base.V12_CLAIM; V13_VERDICT=base.V13_VERDICT
AdmissionError=base.AdmissionError; canonical_json_bytes=base.canonical_json_bytes; sha256_bytes=base.sha256_bytes; sha256_file=base.sha256_file
load_json=base.load_json; verify_canonical_receipt=base.verify_canonical_receipt; safe_zip_name=base.safe_zip_name; safe_xml_root=base.safe_xml_root
process_version=base.process_version; zip_content_manifest=base.zip_content_manifest; detect_source=base.detect_source; route_for=base.route_for; preflight=base.preflight

V12_OFFICIAL_VALIDATOR={
 "coordinate":"com.okworx.ilcd.validation:ilcd-validation:2.12.2",
 "jar_sha256":"55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b",
 "pom_sha256":"16430562fe6ebb6da3e4afea4a8c6cce98d822d61f59eb33e0b5dc98a4eb1fc1"}
V12_OFFICIAL_PROFILE={
 "coordinate":"com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
 "jar_sha256":"96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
 "pom_sha256":"0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a",
 "generic_include_sha256":"31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25",
 "en15804_include_sha256":"a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147"}

def validate_v12_conformance(pre:dict[str,Any], conf:dict[str,Any])->dict[str,Any]:
    verify_canonical_receipt(conf,"v1.2 conformance")
    if conf.get("claim_token")!=V12_CLAIM: raise AdmissionError("wrong v1.2 conformance claim token")
    if conf.get("compatibility_claim") is not True: raise AdmissionError("v1.2 conformance receipt does not assert bounded compatibility")
    if conf.get("certified") is not False: raise AdmissionError("v1.2 conformance receipt must remain certified=false")
    if conf.get("authority_inference_allowed") is not False: raise AdmissionError("v1.2 conformance receipt permits an authority inference")
    validator=conf.get("official_validator"); profile=conf.get("official_profile")
    if validator!=V12_OFFICIAL_VALIDATOR: raise AdmissionError("v1.2 conformance receipt does not match the exact accepted official validator stack")
    if profile!=V12_OFFICIAL_PROFILE: raise AdmissionError("v1.2 conformance receipt does not match the exact accepted ÖKOBAUDAT profile stack")
    positive=conf.get("positive_control",{})
    if positive.get("error_count")!=0 or positive.get("is_positive") is not True: raise AdmissionError("v1.2 official-profile conformance is not positive with zero errors")
    expected=pre["source"].get("package_manifest_sha256")
    if not expected or conf.get("package_manifest_sha256")!=expected: raise AdmissionError("v1.2 conformance receipt is not bound to the admitted package manifest")
    return {"receipt_sha256":conf["receipt_sha256"],"claim_token":V12_CLAIM,"official_validator":validator,"official_profile":profile,"profile_validation_performed":True,"profile_positive":True,"error_count":0,"warning_count":positive.get("warning_count")}

def validate_v13_conformance(pre:dict[str,Any],conf:dict[str,Any])->dict[str,Any]: return base.validate_v13_conformance(pre,conf)

def finalize(pre:dict[str,Any],conf:dict[str,Any])->dict[str,Any]:
    verify_canonical_receipt(pre,"admission preflight")
    if pre.get("verdict")!="ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE" or pre.get("state")!="AWAITING_CONFORMANCE": raise AdmissionError("invalid admission preflight state")
    if pre.get("normalization_permitted") is not False or pre.get("certified") is not False: raise AdmissionError("invalid admission preflight policy")
    if pre.get("rights",{}).get("transformation")!="ALLOWED": raise AdmissionError("normalization cannot be admitted without explicit transformation permission")
    route=pre["routing"]["route"]
    binding=validate_v12_conformance(pre,conf) if route==V12_ROUTE else validate_v13_conformance(pre,conf) if route==V13_ROUTE else (_ for _ in ()).throw(AdmissionError("unsupported preflight route"))
    receipt={"verdict":VERDICT,"state":"ADMITTED_FOR_NORMALIZATION","admitted":True,"normalization_permitted":True,"certified":False,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"preflight_receipt_sha256":pre["receipt_sha256"],"source":{"sha256":pre["source"]["source_sha256"],"package_manifest_sha256":pre["source"].get("package_manifest_sha256"),"detected_version":pre["source"]["detected_version"],"container":pre["source"]["container"]},"rights":{"decision":pre["rights"]["decision"],"status":pre["rights"]["status"],"transformation":pre["rights"]["transformation"],"redistribution":pre["rights"]["redistribution"]},"routing":pre["routing"],"conformance":binding,"evidence_dimensions":{"source_authority":"VERIFIED_FOR_DECLARED_IMPORT","source_integrity":"VERIFIED","format_version":"VERIFIED","format_or_profile_conformance":"VERIFIED_FOR_SELECTED_ROUTE","normalization_permission":"GRANTED_FOR_THIS_EXACT_SOURCE_IDENTITY","scientific_validity":"NOT_EVALUATED","professional_review":"NOT_EVALUATED","certification":"NOT_EVALUATED"},"limitations":["v0.9.1 rejects self-consistent v1.2 receipts unless the complete accepted validator/profile fingerprint matches.","Admission does not establish scientific validity, professional review, provider/programme authority, or certification."]}
    receipt["receipt_sha256"]=sha256_bytes(canonical_json_bytes(receipt)); return receipt
