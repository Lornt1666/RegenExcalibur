#!/usr/bin/env python3
"""ProofGrid v2.9 exact-Decimal total over the accepted v2.8 three-member PARTIAL set."""
from __future__ import annotations
import argparse, copy, hashlib, json
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'schemas'/'three-member-partial-set-total-v29.schema.json'
ZERO='0'*64
CANON='UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false'
VERDICT='THREE_MEMBER_PARTIAL_SET_EXACT_DECIMAL_TOTAL_VERIFIABLE'
EXPECTED_SET={'content':'9ad3fe620f995d316ac620998fae9bf6fcd75e72151286cc544edf0c2bdad7e4','file':'01b01df63e346148d4d76e8a145a82d80b9b138ea59cc1b647b43af95fd86946','receipt':'6c581cd0a60a051e2efe25924eb6dc1b9bf379fc7a1d7c60d5e9d69d0e082846','receipt_file':'b87433764127ebd53551df81fd98b28fae205ec015fc605f072299dee7fcecba','set_id':'proofgrid-v28-three-distinct-members','scope_id':'proofgrid:v28:three-distinct-elements-partial'}
EXPECTED_MEMBERS={
'b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc':'15559.479677163699',
'75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950':'7779.7398385818495',
'2a67655f18b9cd8d776335e886dc324c9911dd9e1090e8852752235ecb958905':'3889.86991929092475'}
COMPAT={'indicator_code':'GWP-total','indicator_uuid':'6a37f984-a4b3-458a-a20a-64418c145fa2','module':'A1-A3','scenario':None,'unit':'kg CO2 eqv.'}
EXPECTED_TOTAL='27229.08943503647325'

class TotalError(ValueError): pass

def require(c:bool,m:str):
    if not c: raise TotalError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def sha(v:bytes)->str: return hashlib.sha256(v).hexdigest()
def load(p:Path): raw=p.read_bytes(); o=json.loads(raw.decode()); require(isinstance(o,dict),f'expected object: {p}'); return o,raw

def canonical_decimal(v:Any,label:str)->str:
    require(isinstance(v,str) and v,f'{label} must be Decimal string')
    try: n=Decimal(v)
    except InvalidOperation as e: raise TotalError(f'{label} invalid Decimal') from e
    require(n.is_finite(),f'{label} non-finite')
    t='0' if n==0 else format(n,'f').rstrip('0').rstrip('.')
    require(t==v,f'{label} not canonical Decimal'); return v

def verify_parent(s:dict,sraw:bytes,r:dict,rraw:bytes):
    require(s.get('verdict')=='ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE','wrong set verdict')
    h=s.get('integrity',{}).get('content_sha256'); require(h==EXPECTED_SET['content'],'unaccepted set content'); x=copy.deepcopy(s); x['integrity']['content_sha256']=ZERO; require(sha(cbytes(x))==h,'set content digest mismatch'); require(sha(sraw)==EXPECTED_SET['file'],'unaccepted set file')
    rh=r.get('receipt_sha256'); require(rh==EXPECTED_SET['receipt'],'unaccepted set receipt'); y=copy.deepcopy(r); y.pop('receipt_sha256',None); require(sha(cbytes(y))==rh,'set receipt digest mismatch'); require(sha(rraw)==EXPECTED_SET['receipt_file'],'unaccepted set receipt file')
    require(r.get('record_content_sha256')==h and r.get('record_file_sha256')==EXPECTED_SET['file'],'set receipt binding mismatch')
    require(s.get('set_id')==EXPECTED_SET['set_id'] and s.get('scope_id')==EXPECTED_SET['scope_id'],'set ID mismatch'); require(s.get('member_count')==3 and len(s.get('members',[]))==3,'exactly three members required'); require(s.get('completeness_status')=='PARTIAL','source set not PARTIAL'); require(s.get('compatibility')==COMPAT,'compatibility mismatch')
    for k in ('aggregation_performed','sum_performed','missing_contributions_are_zero','missing_modules_are_zero','unit_conversion_performed','scenario_inference_performed','duplicate_members_permitted','scientific_validation_performed','professional_review_performed','certified'): require(s.get(k) is False,f'source set {k} promotion rejected')

def aggregate(s:dict)->dict:
    normalized=[]; ids=[]
    for i,m in enumerate(s['members']):
        sid=m.get('semantic_identity_sha256'); sem=m.get('semantic_identity',{}); require(isinstance(sid,str) and len(sid)==64,f'member[{i}] identity missing'); require(sha(cbytes(sem))==sid,f'member[{i}] identity digest mismatch'); require(sid in EXPECTED_MEMBERS,f'unaccepted member {sid}')
        v=canonical_decimal(sem.get('value_decimal'),f'member[{i}] value'); require(v==EXPECTED_MEMBERS[sid],f'member[{i}] exact value mismatch')
        require({k:sem.get(k) for k in ('indicator_code','indicator_uuid','module','scenario','unit')}==COMPAT,f'member[{i}] compatibility mismatch')
        ids.append(sid); normalized.append({'semantic_identity_sha256':sid,'element_global_id':sem['element_global_id'],'rxep_record_content_sha256':m['rxep']['record_content_sha256'],'calculation_record_content_sha256':m['calculation']['record_content_sha256'],'value_decimal':v,'unit':sem['unit']})
    require(len(set(ids))==3 and set(ids)==set(EXPECTED_MEMBERS),'three distinct accepted identities required'); normalized.sort(key=lambda z:z['semantic_identity_sha256'])
    with localcontext() as ctx: ctx.prec=100; total=sum((Decimal(m['value_decimal']) for m in normalized),Decimal('0'))
    total_text=canonical_decimal(format(total,'f'),'three-member total'); require(total_text==EXPECTED_TOTAL,f'unexpected total {total_text}')
    return {'members':normalized,'order':[m['semantic_identity_sha256'] for m in normalized],'total':total_text}

def build_total(s:dict,sraw:bytes,r:dict,rraw:bytes)->dict:
    verify_parent(s,sraw,r,rraw); a=aggregate(s)
    out={'schema_version':'1.0','record_type':'ProofGridThreeMemberPartialSetExactDecimalTotal','verdict':VERDICT,'source_set':{'record_content_sha256':EXPECTED_SET['content'],'record_file_sha256':EXPECTED_SET['file'],'receipt_sha256':EXPECTED_SET['receipt'],'receipt_file_sha256':EXPECTED_SET['receipt_file'],'set_id':EXPECTED_SET['set_id'],'scope_id':EXPECTED_SET['scope_id']},'compatibility':copy.deepcopy(COMPAT),'completeness_status':'PARTIAL','members':a['members'],'member_count':3,'aggregation':{'method':'canonical_decimal_sum','version':'2.9.0','scope':'ADMITTED_SET_MEMBERS_ONLY','member_order':a['order'],'total_value_decimal':a['total'],'unit':'kg CO2 eqv.'},'aggregation_performed':True,'sum_performed':True,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'missing_contributions_are_zero':False,'missing_modules_are_zero':False,'unit_conversion_performed':False,'scenario_inference_performed':False,'duplicate_members_permitted':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False,'limitations':['Exact Decimal sum of the three admitted members in the accepted PARTIAL set only.','PARTIAL remains explicit; this is not a whole-building or declared-scope-complete LCA.','No missing contribution/module is treated as zero and no unit conversion or scenario inference is performed.'],'integrity':{'content_sha256':ZERO,'canonicalization':CANON,'signature':None}}
    out['integrity']['content_sha256']=sha(cbytes(out)); Draft202012Validator(json.loads(SCHEMA.read_text())).validate(out); return out

def write_outputs(out:dict,d:Path)->dict:
    d.mkdir(parents=True,exist_ok=True); b=pbytes(out); (d/'three-member-partial-set-exact-decimal-total.json').write_bytes(b)
    r={'verdict':VERDICT,'record_content_sha256':out['integrity']['content_sha256'],'record_file_sha256':sha(b),'source_set_content_sha256':EXPECTED_SET['content'],'source_set_receipt_sha256':EXPECTED_SET['receipt'],'member_count':3,'member_semantic_identity_sha256':out['aggregation']['member_order'],'total_value_decimal':EXPECTED_TOTAL,'unit':'kg CO2 eqv.','completeness_status':'PARTIAL','aggregation_performed':True,'sum_performed':True,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'missing_contributions_are_zero':False,'missing_modules_are_zero':False,'unit_conversion_performed':False,'scenario_inference_performed':False,'duplicate_members_permitted':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}; r['receipt_sha256']=sha(cbytes(r)); (d/'three-member-partial-set-exact-decimal-total-receipt.json').write_bytes(pbytes(r)); return r

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--set-record',type=Path,required=True); p.add_argument('--set-receipt',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args(argv)
    try: s,sraw=load(a.set_record); r,rraw=load(a.set_receipt); out=build_total(s,sraw,r,rraw); write_outputs(out,a.output_dir)
    except Exception as e: print(f'FAILED: {e}'); return 2
    print(f'RESULT: {VERDICT}'); print(f'EXACT PARTIAL TOTAL: {EXPECTED_TOTAL} kg CO2 eqv.'); print('COMPLETENESS: PARTIAL'); print('NOT A WHOLE-BUILDING LCA'); return 0
if __name__=='__main__': raise SystemExit(main())
