#!/usr/bin/env python3
"""ProofGrid v2.2 declared-scope coverage gate.

No environmental arithmetic is performed. The gate binds an exact synthetic
three-slot scope to accepted v2.0 member identities and accepted v2.1 RXEP
partial evidence, proving two covered slots and one unresolved slot.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, SchemaError

ROOT=Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA=ROOT/'schemas'/'declared-scope-coverage-manifest-v22.schema.json'
ENGINE_NAME='RegenExcalibur ProofGrid Declared Scope Coverage Gate'; ENGINE_VERSION='2.2.0'
VERDICT='DECLARED_SCOPE_COVERAGE_PARTIAL_VERIFIABLE'; ZERO='0'*64
CANON='UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false'
EXPECTED_MANIFEST_FILE_SHA256='02a7ebf6ead270a94da092c29eedaf7bc64f103c13ad947aac02fd543c53530a'
EXPECTED_MANIFEST_ID='proofgrid-v22-synthetic-three-slot-declared-scope'
EXPECTED_UNRESOLVED='proofgrid:v22:unresolved-required-slot-1'
V21={'head':'81b5ef6af8ec40b17071086a7af67365e5e92f8f','artifact_id':9471598609,'artifact_zip':'fae329c5960875f6b372f6e610cffce82070930a98ec9ca31010cb7d2cfdd885','record_content':'9e2a2e30d2d4fcf3aa2b9305b2e334f91c282df7e669f42502fe03468a1cf800','record_file':'07fddcbfbfbb83bc29da979d4fdaac219ca008be78b2f0050e717ee4167865bf','receipt':'18561a681189944e99ebbb5d987c9380558ad1f6cc68f742f60c38d459d9444a','receipt_file':'c54485ccace374507753e15ba5bd28fa8e912959d8292efbada76ac9f652612b','comparison':'cae17ea2f59cf342ce79c2443a3d2a430123798f865541cb183bba5670a6698f','comparison_file':'030980aa5bbe0f45f0fb69a6748acefc566a9b64bc6b5ef72b8ed10098080d9e'}
V20={'head':'2fc2c450b1f37cb2c355ff12d09622ad5f094eec','artifact_id':9464376763,'artifact_zip':'9b63ae70c4db86e2b01577bcc433471ad705a3aedcc590cf028fd874d95e677b','record_content':'8b47dfb87f1be4e1979666f85f7da58c41c00e48c92b7cd4a2f3c9fdd62e8ed0','record_file':'3e50fc30562b0611170b78baf1cf8b52a0cd39ba052f1398c7463a700ba9e6d8','receipt':'991de0efd5c71c067391c8e5fa7bbf81fd55febb72a4cfe8cf5a10f09ac238d4','receipt_file':'17ee6da67b9c549f6b53346fa49e4bf8d30d4d459a4f2c17566d286521cb8f2d','members':{'b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc':'1BXL7DJx51bvggyIPU2Xi5','75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950':'1CXL7DJx51bvggyIPU2Xi6'}}

class CoverageError(ValueError): pass
def req(c:bool,m:str)->None:
    if not c: raise CoverageError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def shafile(p:Path)->str: return sha(p.read_bytes())
def load(p:Path)->Any:
    try:return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError as e: raise CoverageError(f'missing required file: {p}') from e
    except json.JSONDecodeError as e: raise CoverageError(f'invalid JSON in {p}: {e}') from e

def zero_integrity(d:dict[str,Any],label:str)->str:
    claimed=d.get('integrity',{}).get('content_sha256'); req(isinstance(claimed,str) and len(claimed)==64,f'{label} missing content hash')
    b=copy.deepcopy(d); b['integrity']['content_sha256']=ZERO; actual=sha(cbytes(b)); req(actual==claimed,f'{label} content digest mismatch'); return actual

def receipt_digest(d:dict[str,Any],field:str,label:str)->str:
    claimed=d.get(field); req(isinstance(claimed,str) and len(claimed)==64,f'{label} missing {field}')
    b=copy.deepcopy(d); b.pop(field,None); actual=sha(cbytes(b)); req(actual==claimed,f'{label} digest mismatch'); return actual

def validate_manifest(path:Path,enforce_pin:bool=True)->dict[str,Any]:
    if enforce_pin:req(shafile(path)==EXPECTED_MANIFEST_FILE_SHA256,'declared-scope manifest file hash mismatch')
    schema=load(MANIFEST_SCHEMA); manifest=load(path)
    try:Draft202012Validator.check_schema(schema)
    except SchemaError as e: raise CoverageError(f'invalid v2.2 manifest schema: {e.message}') from e
    errors=sorted(Draft202012Validator(schema).iter_errors(manifest),key=lambda e:list(e.path))
    if errors: raise CoverageError('declared-scope manifest failed schema validation: '+'; '.join(e.message for e in errors[:5]))
    req(manifest['manifest_id']==EXPECTED_MANIFEST_ID,'wrong declared-scope manifest identity')
    req(manifest['synthetic'] is True and manifest['real_project'] is False,'manifest must remain synthetic/non-project')
    ids=[s['slot_id'] for s in manifest['required_slots']]; req(len(ids)==3 and len(set(ids))==3,'manifest must retain exactly three unique slots')
    return manifest

def verify_v21(rp:Path,pp:Path,cp:Path)->dict[str,Any]:
    req(shafile(rp)==V21['record_file'],'wrong/tampered v2.1 RXEP record file'); req(shafile(pp)==V21['receipt_file'],'wrong/tampered v2.1 receipt file'); req(shafile(cp)==V21['comparison_file'],'wrong/tampered v2.1 comparison file')
    r,p,c=load(rp),load(pp),load(cp)
    req(zero_integrity(r,'v2.1 RXEP record')==V21['record_content'],'v2.1 RXEP content identity mismatch'); req(receipt_digest(p,'receipt_sha256','v2.1 receipt')==V21['receipt'],'v2.1 receipt identity mismatch'); req(receipt_digest(c,'comparison_receipt_sha256','v2.1 comparison')==V21['comparison'],'v2.1 comparison identity mismatch')
    req(r.get('review')=={'state':'CALCULATED','reviewer':None},'v2.1 review promotion'); req(r.get('completeness_status')=='PARTIAL','v2.1 completeness promotion'); req(r.get('whole_building_lca_claimed') is False and r.get('declared_scope_complete_claimed') is False and r.get('certified') is False,'v2.1 claim promotion')
    return r

def verify_v20(rp:Path,pp:Path)->dict[str,dict[str,Any]]:
    req(shafile(rp)==V20['record_file'],'wrong/tampered v2.0 record file'); req(shafile(pp)==V20['receipt_file'],'wrong/tampered v2.0 receipt file')
    r,p=load(rp),load(pp); req(zero_integrity(r,'v2.0 record')==V20['record_content'],'v2.0 content identity mismatch'); req(receipt_digest(p,'receipt_sha256','v2.0 receipt')==V20['receipt'],'v2.0 receipt identity mismatch'); req(r.get('completeness_status')=='PARTIAL','v2.0 completeness promotion')
    members=r.get('members',[]); req(len(members)==2,'accepted v2.0 member count must be two'); idx={}
    for m in members:
        sid=m.get('semantic_identity_sha256'); req(isinstance(sid,str) and sid not in idx,'duplicate/invalid v2.0 member identity'); idx[sid]=m
    req(set(idx)==set(V20['members']),'v2.0 member identity set mismatch')
    for sid,gid in V20['members'].items(): req(idx[sid].get('element_global_id')==gid,f'GlobalId mismatch for {sid}')
    return idx

def coverage(manifest:dict[str,Any],members:dict[str,dict[str,Any]])->dict[str,Any]:
    slots=[]; used=set()
    for slot in manifest['required_slots']:
        b=slot['binding']; status=b['status']; sid=b['semantic_identity_sha256']
        if status=='COVERED':
            req(isinstance(sid,str) and sid in members,f"unknown contribution identity for {slot['slot_id']}"); req(sid not in used,'one contribution cannot cover multiple slots'); m=members[sid]; req(slot['kind']=='IFC_ELEMENT','covered slot must be IFC_ELEMENT'); req(slot['expected_element_global_id']==m['element_global_id'],f"GlobalId mismatch for {slot['slot_id']}"); used.add(sid)
            slots.append({'slot_id':slot['slot_id'],'kind':slot['kind'],'coverage_status':'COVERED','element_global_id':m['element_global_id'],'semantic_identity_sha256':sid,'rxep_record_content_sha256':m['rxep_record_content_sha256']})
        else:
            req(status=='UNRESOLVED' and sid is None,'unresolved slot may not carry contribution identity'); req(slot['slot_id']==EXPECTED_UNRESOLVED,'unexpected unresolved slot'); req(slot['kind']=='SYNTHETIC_REQUIRED_SLOT' and slot['expected_element_global_id'] is None,'unresolved slot must remain synthetic and unmapped')
            slots.append({'slot_id':slot['slot_id'],'kind':slot['kind'],'coverage_status':'UNRESOLVED','element_global_id':None,'semantic_identity_sha256':None,'environmental_value_present':False})
    req(used==set(V20['members']),'not all accepted members represented exactly once'); cov=sum(s['coverage_status']=='COVERED' for s in slots); unr=sum(s['coverage_status']=='UNRESOLVED' for s in slots); req((len(slots),cov,unr)==(3,2,1),'expected exactly 2 covered + 1 unresolved of 3 slots')
    return {'slots':slots,'covered':cov,'unresolved':unr}

def verify_record(r:dict[str,Any])->None:
    req(r.get('verdict')==VERDICT,'wrong v2.2 verdict'); req(r.get('manifest',{}).get('synthetic') is True and r.get('manifest',{}).get('real_project') is False,'record must remain synthetic/non-project'); req((r.get('declared_scope_slot_count'),r.get('covered_slot_count'),r.get('unresolved_slot_count'))==(3,2,1),'coverage counts changed'); req(r.get('coverage_status')=='PARTIAL','coverage completeness promotion rejected'); req(r.get('coverage_percentage_calculated') is False,'coverage percentage not authoritative'); req(r.get('completeness_promotion_permitted') is False,'completeness promotion not permitted'); req(r.get('environmental_arithmetic_performed') is False and r.get('additional_sum_performed') is False,'environmental arithmetic forbidden'); req(r.get('unresolved_slots_are_zero') is False and r.get('missing_contributions_are_zero') is False,'missing/unresolved zero inference forbidden'); req(r.get('whole_building_lca_claimed') is False and r.get('declared_scope_complete_claimed') is False,'scope promotion rejected'); req(r.get('scientific_validation_performed') is False and r.get('professional_review_performed') is False and r.get('certified') is False,'review/certification promotion rejected')
    slots=r.get('slots',[]); req(len(slots)==3,'all three slots required'); u=[s for s in slots if s.get('coverage_status')=='UNRESOLVED']; req(len(u)==1 and u[0].get('slot_id')==EXPECTED_UNRESOLVED,'exact unresolved slot missing'); req(u[0].get('semantic_identity_sha256') is None and u[0].get('environmental_value_present') is False,'unresolved slot acquired value/member'); c=[s for s in slots if s.get('coverage_status')=='COVERED']; req({s.get('semantic_identity_sha256') for s in c}==set(V20['members']) and len(c)==2,'covered identities mismatch/duplicate')
    claimed=r.get('integrity',{}).get('content_sha256'); req(isinstance(claimed,str) and len(claimed)==64,'content hash missing'); b=copy.deepcopy(r); b['integrity']['content_sha256']=ZERO; req(sha(cbytes(b))==claimed,'coverage content hash mismatch')

def build_record(mp:Path,v21r:Path,v21p:Path,v21c:Path,v20r:Path,v20p:Path)->dict[str,Any]:
    manifest=validate_manifest(mp); verify_v21(v21r,v21p,v21c); members=verify_v20(v20r,v20p); cv=coverage(manifest,members)
    r={'schema_version':'1.0','record_type':'ProofGridDeclaredScopeCoverageV22','verdict':VERDICT,'manifest':{'manifest_id':manifest['manifest_id'],'file_sha256':shafile(mp),'synthetic':True,'real_project':False},'parent_v21':{'accepted_head':V21['head'],'record_content_sha256':V21['record_content'],'receipt_sha256':V21['receipt'],'comparison_receipt_sha256':V21['comparison']},'parent_v20':{'accepted_head':V20['head'],'record_content_sha256':V20['record_content'],'receipt_sha256':V20['receipt']},'slots':cv['slots'],'declared_scope_slot_count':3,'covered_slot_count':cv['covered'],'unresolved_slot_count':cv['unresolved'],'coverage_status':'PARTIAL','coverage_percentage_calculated':False,'completeness_promotion_permitted':False,'environmental_arithmetic_performed':False,'additional_sum_performed':False,'unresolved_slots_are_zero':False,'missing_contributions_are_zero':False,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False,'limitations':list(manifest['limitations'])+['Coverage is exact slot membership only; no coverage percentage is authoritative in v2.2.','The synthetic declared scope does not establish the complete scope of any real building or project.','No environmental arithmetic is performed by this gate.'],'integrity':{'content_sha256':ZERO,'canonicalization':CANON}}
    r['integrity']['content_sha256']=sha(cbytes(r)); verify_record(r); return r

def build_receipt(r:dict[str,Any],rb:bytes)->dict[str,Any]:
    p={'verdict':VERDICT,'engine':{'name':ENGINE_NAME,'version':ENGINE_VERSION},'record_content_sha256':r['integrity']['content_sha256'],'record_file_sha256':sha(rb),'manifest_file_sha256':r['manifest']['file_sha256'],'parent_v21_record_content_sha256':V21['record_content'],'parent_v21_receipt_sha256':V21['receipt'],'parent_v20_record_content_sha256':V20['record_content'],'declared_scope_slot_count':3,'covered_slot_count':2,'unresolved_slot_count':1,'coverage_status':'PARTIAL','completeness_promotion_permitted':False,'environmental_arithmetic_performed':False,'additional_sum_performed':False,'unresolved_slots_are_zero':False,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}; p['receipt_sha256']=sha(cbytes(p)); return p

def generate(mp:Path,v21r:Path,v21p:Path,v21c:Path,v20r:Path,v20p:Path,out:Path):
    r=build_record(mp,v21r,v21p,v21c,v20r,v20p); out.mkdir(parents=True,exist_ok=True); rb=pbytes(r); (out/'declared-scope-coverage.json').write_bytes(rb); p=build_receipt(r,rb); (out/'declared-scope-coverage-receipt.json').write_bytes(pbytes(p)); return r,p

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,required=True); ap.add_argument('--v21-record',type=Path,required=True); ap.add_argument('--v21-receipt',type=Path,required=True); ap.add_argument('--v21-comparison',type=Path,required=True); ap.add_argument('--v20-record',type=Path,required=True); ap.add_argument('--v20-receipt',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args()
    try:r,p=generate(a.manifest,a.v21_record,a.v21_receipt,a.v21_comparison,a.v20_record,a.v20_receipt,a.output_dir)
    except CoverageError as e: print(f'FAILED: {e}',file=sys.stderr); return 2
    print(f'RESULT: {VERDICT}'); print(f"SLOTS: {r['covered_slot_count']} covered / {r['unresolved_slot_count']} unresolved / {r['declared_scope_slot_count']} declared"); print('COVERAGE STATUS: PARTIAL'); print('ENVIRONMENTAL ARITHMETIC: FALSE'); print('NOT CERTIFIED'); print(f"Receipt: {p['receipt_sha256']}"); return 0
if __name__=='__main__': raise SystemExit(main())
