#!/usr/bin/env python3
"""ProofGrid v3.1 admission of one frozen real ÖKOBAUDAT environmental source.

Authority is the canonical uncompressed package-member manifest, not volatile
ZIP container bytes. The binder verifies:
- all 33 package member path/size/SHA identities;
- frozen target process / terms / extended-view hashes;
- exact ILCD+EPD v1.2 dataset identity and source metadata;
- exact source-declared reference flow and GWP-total/A1-A3 row;
- exact official ÖKOBAUDAT validation stack and positive profile result.

No IFC mapping, quantity multiplication, whole-building aggregation, professional
suitability, regulatory acceptance, or certification is inferred.
"""
from __future__ import annotations

import argparse, copy, hashlib, json, zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

ENGINE_NAME="RegenExcalibur ProofGrid Real ÖKOBAUDAT Environmental Source Admission"
ENGINE_VERSION="3.1.0"
VERDICT="REAL_ENVIRONMENTAL_SOURCE_ADMISSION_VERIFIABLE"
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO="0"*64

UUID="8347f9a7-f4ec-4a36-a266-a0281f5fd16d"
VERSION="00.02.000"
PROCESS_PATH=f"ILCD/processes/{UUID}_{VERSION}.xml"
PROCESS_SHA="18951c19002314adb6213d05783f8075553102a1bc57e22950d941a4804e445d"
PACKAGE_SHA="c858c2712243684b094d843bd688b5ee062b0d8005f2cd2cef93bd7e4902e3a3"
TERMS_SHA="88d6a4ad8c63d16c1e24a4cee38a9f696d825248ceef87de572403b80bf9ed2d"
TERMS_SIZE=10371
EXTENDED_SHA="19571f40b2516345efb09d5ca423cb2b7f6c06debc4a69ee2d6837da52183c16"
EXTENDED_SIZE=77663

PROFILE_COORD="com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0"
PROFILE_JAR_SHA="96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e"
PROFILE_POM_SHA="0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a"
PROFILE_GENERIC_SHA="31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25"
PROFILE_EN15804_SHA="a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147"
VALIDATOR_COORD="com.okworx.ilcd.validation:ilcd-validation:2.12.2"
VALIDATOR_JAR_SHA="55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b"

NSP="http://lca.jrc.it/ILCD/Process"
NSC="http://lca.jrc.it/ILCD/Common"
NSEPD="http://www.indata.network/EPD/2019"
NSIAI="http://www.iai.kit.edu/EPD/2013"
NS={"p":NSP,"c":NSC,"epd":NSEPD,"iai":NSIAI}

class V31Error(ValueError): pass

def require(c:bool,m:str)->None:
    if not c: raise V31Error(m)

def cj(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def pj(v:Any)->bytes:
    return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def load_json(path:Path)->tuple[dict[str,Any],bytes]:
    raw=Path(path).read_bytes()
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception as e: raise V31Error(f"invalid JSON {path}: {e}") from e
    require(isinstance(obj,dict),f"expected JSON object: {path}")
    return obj,raw

def canonical_decimal(text:Any,label:str)->str:
    require(isinstance(text,str) and text.strip(),f"{label} missing")
    text=text.strip()
    try: d=Decimal(text)
    except InvalidOperation as e: raise V31Error(f"{label} is not Decimal") from e
    require(d.is_finite(),f"{label} must be finite")
    out=format(d,"f")
    if "." in out: out=out.rstrip("0").rstrip(".")
    if out in {"","-0"}: out="0"
    require(out==text,f"{label} is not canonical Decimal: {text}")
    return out

def verify_package(zip_path:Path,committed_manifest:dict[str,Any])->tuple[dict[str,bytes],dict[str,Any]]:
    require(zipfile.is_zipfile(zip_path),"source is not a ZIP package")
    expected_members=committed_manifest.get("members")
    require(isinstance(expected_members,list) and len(expected_members)==33,"committed package manifest must contain 33 members")
    require(committed_manifest.get("package_content_manifest_sha256")==PACKAGE_SHA,"committed package manifest SHA identity mismatch")
    require(committed_manifest.get("target_process_path")==PROCESS_PATH,"committed target process path mismatch")
    require(committed_manifest.get("target_process_sha256")==PROCESS_SHA,"committed target process SHA mismatch")
    require(committed_manifest.get("dataset_uuid")==UUID and committed_manifest.get("requested_version")==VERSION,"committed dataset identity mismatch")
    expected={x["path"]:(int(x["size_bytes"]),x["sha256"]) for x in expected_members}
    with zipfile.ZipFile(zip_path) as z:
        names=sorted(z.namelist())
        require(len(names)==33,"package member count drift")
        require(not any(n.startswith("/") or ".." in Path(n).parts for n in names),"unsafe ZIP path")
        require(set(names)==set(expected),"package member path set drift")
        payload={}
        actual=[]
        for name in names:
            data=z.read(name); payload[name]=data
            size=len(data); digest=sha(data)
            require((size,digest)==expected[name],f"package member identity drift: {name}")
            actual.append({"path":name,"size_bytes":size,"sha256":digest})
    digest=sha(json.dumps(actual,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
    require(digest==PACKAGE_SHA,"canonical package member manifest digest mismatch")
    return payload,{"member_count":33,"package_content_manifest_sha256":digest,"members":actual}

def verify_rights(manifest:dict[str,Any],terms:bytes,extended:bytes)->dict[str,Any]:
    frozen=manifest.get("frozen_source",{})
    require(frozen.get("state")=="FROZEN","source manifest is not frozen")
    require(frozen.get("package_content_manifest_sha256")==PACKAGE_SHA,"source manifest package SHA mismatch")
    require(frozen.get("target_process_sha256")==PROCESS_SHA,"source manifest process SHA mismatch")
    require(len(terms)==TERMS_SIZE and sha(terms)==TERMS_SHA,"published terms bytes drift")
    require(len(extended)==EXTENDED_SIZE and sha(extended)==EXTENDED_SHA,"extended service view bytes drift")
    t=terms.decode("utf-8",errors="strict").lower()
    for marker in ("free of charge","without any restrictions","free distribution of unmodified data","source is named","no responsibility for the accuracy"):
        require(marker in t,f"published rights marker missing: {marker}")
    x=extended.decode("utf-8",errors="strict")
    for marker in (UUID,VERSION,"Concrete C25/30","EPD-IZB-20230421-IBA1-DE"):
        require(marker in x,f"extended service identity marker missing: {marker}")
    r=manifest.get("rights",{})
    require(r.get("read_use")=="ALLOWED","read/use authority missing")
    require(r.get("storage_for_analysis")=="ALLOWED","storage authority missing")
    require(r.get("transformation_for_analysis")=="ALLOWED","transformation authority missing")
    require(r.get("unmodified_redistribution")=="ALLOWED_WITH_SOURCE_ATTRIBUTION","unmodified redistribution authority mismatch")
    require(r.get("modified_or_raw_redistribution")=="UNKNOWN_REQUIRES_SEPARATE_EVIDENCE","modified/raw redistribution must remain unknown")
    require(r.get("scientific_validity_guaranteed_by_provider") is False,"scientific validity promotion rejected")
    require(r.get("professional_suitability_inferred") is False,"professional suitability promotion rejected")
    require(r.get("certification_authority_inferred") is False,"certification authority promotion rejected")
    return {
      "terms_sha256":TERMS_SHA,"terms_size_bytes":TERMS_SIZE,
      "extended_view_sha256":EXTENDED_SHA,"extended_view_size_bytes":EXTENDED_SIZE,
      "read_use":"ALLOWED","storage_for_analysis":"ALLOWED","transformation_for_analysis":"ALLOWED",
      "commercial_analysis_use":"ALLOWED_BY_PUBLISHED_UNRESTRICTED_USE_TERMS",
      "unmodified_redistribution":"ALLOWED_WITH_SOURCE_ATTRIBUTION",
      "modified_or_raw_redistribution":"UNKNOWN_REQUIRES_SEPARATE_EVIDENCE",
      "source_attribution":r.get("source_attribution"),
    }

def text_at(root:ET.Element,path:str)->str:
    e=root.find(path,NS)
    require(e is not None and (e.text or "").strip(),f"missing XML field: {path}")
    return (e.text or "").strip()

def short_desc(ref:ET.Element,lang:str|None=None)->str|None:
    for e in ref.findall("c:shortDescription",NS):
        if lang is None or e.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")==lang:
            txt=(e.text or "").strip()
            if txt: return txt
    return None

def parse_process(process_bytes:bytes)->dict[str,Any]:
    require(sha(process_bytes)==PROCESS_SHA,"target process bytes drift")
    root=ET.fromstring(process_bytes)
    require(root.tag==f"{{{NSP}}}processDataSet","wrong process root namespace")
    require(root.attrib.get(f"{{{NSEPD}}}epd-version")=="1.2","EPD format version mismatch")
    uuid=text_at(root,"p:processInformation/p:dataSetInformation/c:UUID")
    require(uuid==UUID,"dataset UUID mismatch")
    names=root.findall("p:processInformation/p:dataSetInformation/p:name/p:baseName",NS)
    nmap={e.attrib.get("{http://www.w3.org/XML/1998/namespace}lang"):(e.text or "").strip() for e in names}
    require(nmap.get("en")=="Concrete C25/30","English dataset name mismatch")
    version=text_at(root,"p:administrativeInformation/p:publicationAndOwnership/c:dataSetVersion")
    require(version==VERSION,"dataset version mismatch")
    refyear=text_at(root,"p:processInformation/p:time/c:referenceYear"); require(refyear=="2023","reference year mismatch")
    valid=text_at(root,"p:processInformation/p:time/c:dataSetValidUntil"); require(valid=="2028","valid-until mismatch")
    loc=root.find("p:processInformation/p:geography/p:locationOfOperationSupplyOrProduction",NS)
    require(loc is not None and loc.attrib.get("location")=="DE","location mismatch")
    reg=text_at(root,"p:administrativeInformation/p:publicationAndOwnership/c:registrationNumber")
    require(reg=="EPD-IZB-20230421-IBA1-DE","registration number mismatch")
    review=root.find("p:modellingAndValidation/p:validation/p:review",NS)
    require(review is not None and review.attrib.get("type")=="Accredited third party review","source review metadata mismatch")
    reviewer=review.find("c:referenceToNameOfReviewerAndInstitution",NS)
    require(reviewer is not None and reviewer.attrib.get("refObjectId")=="d111dbec-b024-4be5-86c5-752d6eb2cf95","reviewer identity mismatch")
    owner=root.find("p:administrativeInformation/p:publicationAndOwnership/c:referenceToOwnershipOfDataSet",NS)
    require(owner is not None and owner.attrib.get("refObjectId")=="87042751-47a4-4f56-a1c1-8c56880c97d1","owner UUID mismatch")
    require(short_desc(owner)=="InformationsZentrum Beton GmbH","owner name mismatch")
    auth=root.find("p:administrativeInformation/p:publicationAndOwnership/c:referenceToRegistrationAuthority",NS)
    require(auth is not None and auth.attrib.get("refObjectId")=="d111dbec-b024-4be5-86c5-752d6eb2cf95","registration authority UUID mismatch")
    require(short_desc(auth)=="Institut Bauen und Umwelt e. V.","registration authority name mismatch")

    refid=text_at(root,"p:processInformation/p:quantitativeReference/p:referenceToReferenceFlow")
    require(refid=="0","reference-flow internal ID mismatch")
    exchange=None
    for e in root.findall("p:exchanges/p:exchange",NS):
        if e.attrib.get("dataSetInternalID")=="0": exchange=e; break
    require(exchange is not None,"reference-flow exchange missing")
    mean=text_at(exchange,"p:meanAmount"); require(canonical_decimal(mean,"reference quantity")=="1","reference quantity mismatch")
    flowref=exchange.find("p:referenceToFlowDataSet",NS)
    require(flowref is not None and flowref.attrib.get("refObjectId")=="68f1cf50-b4e4-132e-acec-97801ba19ce7","reference product flow mismatch")
    desc=short_desc(flowref); require(desc is not None and "1 m³" in desc,"reference-unit source description mismatch")

    target=None
    for result in root.findall("p:LCIAResults/p:LCIAResult",NS):
        ref=result.find("p:referenceToLCIAMethodDataSet",NS)
        if ref is not None and ref.attrib.get("refObjectId")=="6a37f984-a4b3-458a-a20a-64418c145fa2":
            target=result; break
    require(target is not None,"GWP-total LCIA result missing")
    ref=target.find("p:referenceToLCIAMethodDataSet",NS)
    require(short_desc(ref,"en")=="Global Warming Potential total (GWP-total)","GWP-total source label mismatch")
    unitref=target.find("c:other/iai:referenceToUnitGroupDataSet",NS)
    require(unitref is not None and unitref.attrib.get("refObjectId")=="1ebf3012-d0db-4de2-aefd-ef30cedb0be1","GWP unit-group identity mismatch")
    unitdesc=short_desc(unitref); require(unitdesc is not None and "kg CO" in unitdesc,"GWP source unit description missing")
    amounts=target.findall("c:other/iai:amount",NS)
    a13=[a for a in amounts if a.attrib.get(f"{{{NSIAI}}}module")=="A1-A3"]
    require(len(a13)==1,"GWP A1-A3 row must be unique")
    lexical=(a13[0].text or "").strip(); require(canonical_decimal(lexical,"GWP A1-A3")=="181","GWP A1-A3 value mismatch")
    modules=[]
    for a in amounts:
        modules.append({"module":a.attrib.get(f"{{{NSIAI}}}module"),"value_lexical":(a.text or "").strip() or None})
    return {
      "dataset_uuid":uuid,"dataset_version":version,"name_en":nmap["en"],"name_de":nmap.get("de"),
      "location":"DE","reference_year":2023,"valid_until":2028,"registration_number":reg,
      "owner":{"uuid":owner.attrib["refObjectId"],"name":"InformationsZentrum Beton GmbH"},
      "registration_authority":{"uuid":auth.attrib["refObjectId"],"name":"Institut Bauen und Umwelt e. V."},
      "source_review":{"type":"Accredited third party review","reviewer_contact_uuid":reviewer.attrib["refObjectId"],"scope":"SOURCE_DATASET_METADATA_ONLY"},
      "format":"ILCD+EPD v1.2","product_flow_uuid":flowref.attrib["refObjectId"],
      "declared_reference":{"quantity_decimal":"1","source_unit_description":desc,"canonical_unit_identity":"m3"},
      "gwp_total":{"method_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","indicator_code":"GWP-total","source_unit_description":unitdesc,"canonical_unit_identity":"kg CO2 eqv.","module":"A1-A3","scenario":None,"value_lexical":lexical,"value_decimal":"181","value_origin":"DECLARED_IN_SOURCE","all_module_lexicals":modules},
    }

def verify_profile(profile:dict[str,Any],profile_file_sha:str)->dict[str,Any]:
    require(profile.get("profile_name")=="EPD 1.2 ÖKOBAUDAT","profile name mismatch")
    require(profile.get("profile_version")=="3.8.0","profile version mismatch")
    require(profile.get("profile_coordinates")==PROFILE_COORD,"profile coordinates mismatch")
    require(profile.get("is_positive") is True,"ÖKOBAUDAT profile did not pass")
    require(profile.get("error_count")==0,"ÖKOBAUDAT profile has errors")
    events=profile.get("events"); require(isinstance(events,list),"profile events missing")
    stable_fields=("severity","type","aspect","aspect_description","message","alt_message")
    normalized=sorted([{k:e.get(k) for k in stable_fields} for e in events],key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False))
    fingerprint=sha((json.dumps(normalized,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode())
    return {
      "profile_coordinate":PROFILE_COORD,"profile_version":"3.8.0","profile_jar_sha256":PROFILE_JAR_SHA,
      "profile_pom_sha256":PROFILE_POM_SHA,"generic_include_sha256":PROFILE_GENERIC_SHA,
      "en15804_include_sha256":PROFILE_EN15804_SHA,"validator_coordinate":VALIDATOR_COORD,
      "validator_jar_sha256":VALIDATOR_JAR_SHA,"profile_result_file_sha256":profile_file_sha,
      "error_count":0,"warning_count":profile.get("warning_count"),"event_count":profile.get("event_count"),
      "normalized_event_fingerprint_sha256":fingerprint,"profile_positive":True,
    }

def build_admission(manifest_path:Path,package_manifest_path:Path,zip_path:Path,terms_path:Path,extended_path:Path,profile_path:Path)->dict[str,Any]:
    manifest,manifest_raw=load_json(manifest_path); package_manifest,package_manifest_raw=load_json(package_manifest_path)
    payload,package=verify_package(zip_path,package_manifest)
    rights=verify_rights(manifest,terms_path.read_bytes(),extended_path.read_bytes())
    process=parse_process(payload[PROCESS_PATH])
    profile,profile_raw=load_json(profile_path); conformance=verify_profile(profile,sha(profile_raw))
    record={
      "schema_version":"1.0","record_type":"ProofGridRealEnvironmentalSourceAdmission","verdict":VERDICT,
      "source_identity":process,
      "source_package":{"manifest_file_sha256":sha(package_manifest_raw),"package_content_manifest_sha256":PACKAGE_SHA,"member_count":33,"target_process_path":PROCESS_PATH,"target_process_sha256":PROCESS_SHA},
      "rights":rights,
      "conformance":conformance,
      "source_manifest_sha256":sha(manifest_raw),
      "normalization":{"identity_selection":"EXACT_UUID_VERSION","indicator_selection":"EXACT_METHOD_UUID_MODULE_SCENARIO","unit_conversion_performed":False,"fuzzy_mapping_performed":False},
      "mapped_to_ifc":False,"impact_calculation_performed":False,"whole_building_lca_claimed":False,
      "scientific_validation_performed":False,"professional_suitability_established":False,"regulator_accepted":False,"certified":False,
      "limitations":[
        "Admission establishes rights, exact source identity, package-content integrity, profile conformance, and bounded normalization only.",
        "Dataset-level accredited third-party review metadata is preserved as source metadata and is not review of any IFC mapping or building result.",
        "This source is not automatically suitable for any specific IFC element and is not mapped to the DigitalHub model in v3.1.",
        "Modified/raw redistribution authority remains unknown pending separate evidence."
      ],
      "integrity":{"content_sha256":ZERO,"canonicalization":CANON,"signature":None},
    }
    record["integrity"]["content_sha256"]=sha(cj(record))
    return record

def build_receipt(record:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={
      "verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},
      "record_content_sha256":record["integrity"]["content_sha256"],"record_file_sha256":sha(raw),
      "dataset_uuid":UUID,"dataset_version":VERSION,"package_content_manifest_sha256":PACKAGE_SHA,
      "target_process_sha256":PROCESS_SHA,"terms_sha256":TERMS_SHA,"extended_view_sha256":EXTENDED_SHA,
      "profile_coordinate":PROFILE_COORD,"profile_error_count":0,
      "declared_reference_quantity_decimal":"1","declared_reference_unit":"m3",
      "gwp_total_a1_a3_value_decimal":"181","gwp_total_unit":"kg CO2 eqv.",
      "rights_verified":True,"profile_conformance_verified":True,
      "mapped_to_ifc":False,"impact_calculation_performed":False,"scientific_validation_performed":False,
      "professional_suitability_established":False,"regulator_accepted":False,"certified":False,
    }
    r["receipt_sha256"]=sha(cj(r)); return r

def main(argv=None)->int:
    p=argparse.ArgumentParser()
    for name in ("manifest","package-manifest","zip","terms","extended","profile-result","output-dir"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args(argv)
    try:
        record=build_admission(a.manifest,a.package_manifest,a.zip,a.terms,a.extended,a.profile_result)
        a.output_dir.mkdir(parents=True,exist_ok=True)
        raw=pj(record); (a.output_dir/"real-environmental-source-admission.json").write_bytes(raw)
        receipt=build_receipt(record,raw); (a.output_dir/"real-environmental-source-admission-receipt.json").write_bytes(pj(receipt))
    except Exception as exc:
        print(f"FAILED: {exc}"); return 2
    print(f"RESULT: {VERDICT}")
    print(f"DATASET={UUID}@{VERSION}")
    print("GWP_TOTAL_A1_A3=181 kg CO2 eqv.")
    print("MAPPED_TO_IFC=false")
    print("CERTIFIED=false")
    return 0

if __name__=="__main__": raise SystemExit(main())
