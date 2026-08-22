#!/usr/bin/env python3
"""ProofGrid v2.8: admit the accepted third RXEP/calculation pair into the accepted v1.9 PARTIAL set.

No summation or aggregate recomputation occurs. The historical v1.8 set record
format/verdict is preserved; v2.8 acceptance is expressed by its receipt.
"""
from __future__ import annotations

import argparse, copy, hashlib, json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SET_SCHEMA=ROOT/'schemas'/'environmental-contribution-set.schema.json'
RXEP_SCHEMA=ROOT/'specs'/'rxep'/'evidence-envelope.schema.json'
ZERO='0'*64
CANON='UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false'
SET_VERDICT='ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE'
VERDICT='THREE_MEMBER_ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE'

V19={
 'content':'f2d790e499da25204877817b8d396a335be9dbc60e118fb4bf2f61009c289a8b',
 'file':'427150971842dbd1dd4d1deb87c762abb366bb3c9d56986453bec70d6ad6357b',
 'receipt':'1f1d0b7ffae6caebf3c43201f277bc3997c28112095e9e99fb8208bc77e2fa9e',
 'receipt_file':'8ab034122a244c9a8974b44ae8d84e3170c81b5d92c6d74b660059c950e3a797',
 'members':[
  'b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc',
  '75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950']}
V27={'content':'fe679a64a013c709814ce089b068b9d2cd7284dc513eb2f49a3f071757da5f3b','file':'43797abd10cdb571441e063f19617234b9ab4241e1929010feccc01ed8ae1861','receipt':'adb6df405792a994654c3868b9d24403f2faa42b795e4863767e0bb23c010515','receipt_file':'da8d8bbad354fca328f1ab284367a0b428e12e6ce3be35916dd64b0a269b2b13'}
V26={'content':'125b070fa9935b667cc23beb0c07a955be9b27d9c4d1412f94307c41306fbe56','file':'6f26a7dea2bfaf424c390a39fe00ac0e572af26602cd455f6d77ccad180d9106','receipt':'be67971767fb7210622b60cc4280bec1d00085a1108884e2fa185017bdec946e','receipt_file':'8429c4b054710f6f9969c4145dc1b4bd8cbe16478d00a644e2c7419edb494128'}
COMPAT={'indicator_code':'GWP-total','indicator_uuid':'6a37f984-a4b3-458a-a20a-64418c145fa2','module':'A1-A3','scenario':None,'unit':'kg CO2 eqv.'}
THIRD_IDENTITY={
 'ifc_source_sha256':'ae74ee2db97b6257dc6983ccdf8eacaff7b0998212ce569ad844f6c4600ea31d',
 'element_global_id':'1DXL7DJx51bvggyIPU2Xi7',
 'product_flow_uuid':'a7432abd-0881-4977-a817-f8aaf627fb91','product_flow_version':'00.00.001',
 'quantity_record_content_sha256':'0a9c1e7e8efc6be240315cf04e87904c468b1bb1406f0b1494cb3c0905f37b12',
 'mapping_record_content_sha256':'483aaf34ea733d798c748b90ae3de7d2bd82e6f00573576432bdcfd0dc9290fb',
 'closure_record_content_sha256':'cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd',
 'declaration_bundle_content_sha256':'8e71852027be10c4120f6185e0ae90127da9c72bf1e64f5c50b08442ed2c0aa0',
 'indicator_code':'GWP-total','indicator_uuid':'6a37f984-a4b3-458a-a20a-64418c145fa2','module':'A1-A3','scenario':None,
 'value_decimal':'3889.86991929092475','unit':'kg CO2 eqv.'}
THIRD_IDENTITY_SHA='2a67655f18b9cd8d776335e886dc324c9911dd9e1090e8852752235ecb958905'

class SetAdmissionError(ValueError): pass

def require(c:bool,m:str)->None:
    if not c: raise SetAdmissionError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def load(p:Path):
    raw=p.read_bytes(); v=json.loads(raw.decode()); require(isinstance(v,dict),f'expected object: {p}'); return v,raw

def self_hash(o:dict,label:str)->str:
    i=o.get('integrity'); require(isinstance(i,dict),f'{label} missing integrity'); h=i.get('content_sha256'); require(isinstance(h,str),f'{label} missing hash')
    x=copy.deepcopy(o); x['integrity']['content_sha256']=ZERO; require(sha(cbytes(x))==h,f'{label} content hash mismatch'); return h

def receipt_hash(o:dict,label:str,key:str='receipt_sha256')->str:
    h=o.get(key); require(isinstance(h,str),f'{label} missing digest'); x=copy.deepcopy(o); x.pop(key,None); require(sha(cbytes(x))==h,f'{label} digest mismatch'); return h

def verify_v19(s:dict,sraw:bytes,r:dict,rraw:bytes)->None:
    require(s.get('verdict')==SET_VERDICT,'wrong v1.9 set verdict'); require(self_hash(s,'v1.9 set')==V19['content'],'unaccepted v1.9 set content'); require(sha(sraw)==V19['file'],'unaccepted v1.9 set file')
    require(receipt_hash(r,'v1.9 receipt')==V19['receipt'],'unaccepted v1.9 receipt'); require(sha(rraw)==V19['receipt_file'],'unaccepted v1.9 receipt file')
    require(s.get('member_count')==2 and s.get('completeness_status')=='PARTIAL','v1.9 set state mismatch'); require(s.get('aggregation_performed') is False and s.get('sum_performed') is False,'v1.9 set already aggregated')
    ids=[m['semantic_identity_sha256'] for m in s['members']]; require(ids==V19['members'],'v1.9 semantic members mismatch'); require(s.get('compatibility')==COMPAT,'v1.9 compatibility mismatch')

def verify_third(rx:dict,rxraw:bytes,rr:dict,rrraw:bytes,calc:dict,craw:bytes,cr:dict,crraw:bytes)->dict:
    require(self_hash(rx,'v2.7 RXEP')==V27['content'],'unaccepted v2.7 RXEP content'); require(sha(rxraw)==V27['file'],'unaccepted v2.7 RXEP file'); require(receipt_hash(rr,'v2.7 receipt')==V27['receipt'],'unaccepted v2.7 receipt'); require(sha(rrraw)==V27['receipt_file'],'unaccepted v2.7 receipt file')
    Draft202012Validator(json.loads(RXEP_SCHEMA.read_text())).validate(rx)
    require(rx.get('review')=={'state':'CALCULATED','reviewer':None},'third RXEP review mismatch'); m=rx.get('measurement',{}); require(m.get('value_decimal')==THIRD_IDENTITY['value_decimal'] and m.get('decimal_value_is_authority') is True and m.get('numeric_value_is_authority') is False,'third RXEP Decimal authority mismatch')
    require(rx.get('contribution_set_admission_performed') is False and rx.get('aggregate_recomputed') is False,'third RXEP already set/aggregate promoted')
    require(calc.get('verdict')=='THIRD_MAPPED_DECLARED_RESULT_EXACT_DECIMAL_VERIFIABLE','wrong v2.6 verdict'); require(self_hash(calc,'v2.6 calculation')==V26['content'],'unaccepted v2.6 content'); require(sha(craw)==V26['file'],'unaccepted v2.6 file'); require(receipt_hash(cr,'v2.6 receipt')==V26['receipt'],'unaccepted v2.6 receipt'); require(sha(crraw)==V26['receipt_file'],'unaccepted v2.6 receipt file')
    i=calc['inputs']; sel=calc['selection']; c=calc['calculation']
    identity={'ifc_source_sha256':i['ifc_source_sha256'],'element_global_id':i['element_global_id'],'product_flow_uuid':i['product_flow_uuid'],'product_flow_version':i['product_flow_version'],'quantity_record_content_sha256':i['v24_readiness_content_sha256'],'mapping_record_content_sha256':i['v25_mapping_content_sha256'],'closure_record_content_sha256':i['closure_content_sha256'],'declaration_bundle_content_sha256':i['declaration_bundle_content_sha256'],'indicator_code':sel['indicator_code'],'indicator_uuid':sel['indicator_uuid'],'module':sel['module'],'scenario':sel['scenario'],'value_decimal':c['scaled_result_decimal'],'unit':c['scaled_result_unit']}
    require(identity==THIRD_IDENTITY,'third semantic identity fields mismatch'); require(sha(cbytes(identity))==THIRD_IDENTITY_SHA,'third semantic identity hash mismatch')
    require(rx['subject']['id']==identity['element_global_id'],'third RXEP element mismatch'); require({k:m.get(k) for k in ('indicator_code','indicator_uuid','module','scenario','unit','value_decimal')}=={k:identity[k] for k in ('indicator_code','indicator_uuid','module','scenario','unit','value_decimal')},'third RXEP/calculation compatibility mismatch')
    return identity

def build_set(v19s:dict,v19r:dict,rx:dict,rr:dict,calc:dict,cr:dict)->dict:
    identities={m['semantic_identity_sha256'] for m in v19s['members']}; require(THIRD_IDENTITY_SHA not in identities,'third semantic identity collision')
    third={'member_id':'third-remediated-contribution','rxep':{'record_content_sha256':V27['content'],'record_file_sha256':V27['file'],'receipt_sha256':V27['receipt'],'receipt_file_sha256':V27['receipt_file'],'review_state':'CALCULATED'},'calculation':{'record_content_sha256':V26['content'],'record_file_sha256':V26['file'],'receipt_sha256':V26['receipt'],'receipt_file_sha256':V26['receipt_file']},'semantic_identity':copy.deepcopy(THIRD_IDENTITY),'semantic_identity_sha256':THIRD_IDENTITY_SHA}
    members=copy.deepcopy(v19s['members'])+[third]; members.sort(key=lambda x:x['member_id']); keys=[m['semantic_identity_sha256'] for m in members]; require(len(keys)==3 and len(set(keys))==3,'three distinct semantic members not proven')
    admission_manifest={'base_set_content_sha256':V19['content'],'third_rxep_content_sha256':V27['content'],'third_calculation_content_sha256':V26['content'],'third_semantic_identity_sha256':THIRD_IDENTITY_SHA}
    out={'schema_version':'1.0','record_type':'ProofGridEnvironmentalContributionSet','verdict':SET_VERDICT,'set_id':'proofgrid-v28-three-distinct-members','scope_id':'proofgrid:v28:three-distinct-elements-partial','completeness_status':'PARTIAL','compatibility':copy.deepcopy(COMPAT),'members':members,'member_count':3,'request_file_sha256':sha(cbytes(admission_manifest)),'aggregation_performed':False,'sum_performed':False,'missing_contributions_are_zero':False,'missing_modules_are_zero':False,'unit_conversion_performed':False,'scenario_inference_performed':False,'duplicate_members_permitted':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False,'limitations':['This record admits exactly three distinct calculated contributions; it performs no summation or aggregation.','PARTIAL is explicit and does not imply whole-building or declared-scope completeness.','Missing contributions/modules are not treated as zero.','Membership integrity does not establish scientific validity, professional review, regulatory approval, or certification.'],'integrity':{'content_sha256':ZERO,'canonicalization':CANON,'signature':None}}
    out['integrity']['content_sha256']=sha(cbytes(out)); Draft202012Validator(json.loads(SET_SCHEMA.read_text())).validate(out); return out

def write_outputs(out:dict,dir:Path)->dict:
    dir.mkdir(parents=True,exist_ok=True); rb=pbytes(out); (dir/'three-member-environmental-contribution-set.json').write_bytes(rb)
    ids=[m['semantic_identity_sha256'] for m in out['members']]
    receipt={'verdict':VERDICT,'record_content_sha256':out['integrity']['content_sha256'],'record_file_sha256':sha(rb),'member_count':3,'member_semantic_identity_sha256':ids,'third_semantic_identity_sha256':THIRD_IDENTITY_SHA,'completeness_status':'PARTIAL','aggregation_performed':False,'sum_performed':False,'whole_building_lca_claimed':False,'missing_contributions_are_zero':False,'missing_modules_are_zero':False,'duplicate_members_permitted':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}
    receipt['receipt_sha256']=sha(cbytes(receipt)); (dir/'three-member-environmental-contribution-set-receipt.json').write_bytes(pbytes(receipt)); return receipt

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--base-set',type=Path,required=True); p.add_argument('--base-receipt',type=Path,required=True); p.add_argument('--third-rxep',type=Path,required=True); p.add_argument('--third-rxep-receipt',type=Path,required=True); p.add_argument('--third-calculation',type=Path,required=True); p.add_argument('--third-calculation-receipt',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args(argv)
    try:
        s,sraw=load(a.base_set); sr,srraw=load(a.base_receipt); rx,rxraw=load(a.third_rxep); rr,rrraw=load(a.third_rxep_receipt); c,craw=load(a.third_calculation); cr,crraw=load(a.third_calculation_receipt)
        verify_v19(s,sraw,sr,srraw); verify_third(rx,rxraw,rr,rrraw,c,craw,cr,crraw); out=build_set(s,sr,rx,rr,c,cr); write_outputs(out,a.output_dir)
    except Exception as e: print(f'FAILED: {e}'); return 2
    print(f'RESULT: {VERDICT}'); print('MEMBERS: 3'); print('COMPLETENESS: PARTIAL'); print('SUM PERFORMED: false'); return 0
if __name__=='__main__': raise SystemExit(main())
