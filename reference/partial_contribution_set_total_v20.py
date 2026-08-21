#!/usr/bin/env python3
"""ProofGrid v2.0 exact-Decimal total over the accepted two-member PARTIAL set.

This is the first multi-contribution arithmetic gate. It is intentionally hard-
pinned to the accepted v1.9 two-member contribution set and sums only the two
canonical Decimal member values after proving set/receipt integrity, compatibility,
uniqueness, and PARTIAL completeness. It does not infer missing values or claim a
complete building LCA.
"""
from __future__ import annotations

import argparse, copy, hashlib, json, sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

ENGINE_NAME="RegenExcalibur ProofGrid Partial Contribution Set Exact Decimal Total"
ENGINE_VERSION="2.0.0"
VERDICT="PARTIAL_CONTRIBUTION_SET_EXACT_DECIMAL_TOTAL_VERIFIABLE"
EXPECTED_SET={
  "content":"f2d790e499da25204877817b8d396a335be9dbc60e118fb4bf2f61009c289a8b",
  "file":"427150971842dbd1dd4d1deb87c762abb366bb3c9d56986453bec70d6ad6357b",
  "receipt":"1f1d0b7ffae6caebf3c43201f277bc3997c28112095e9e99fb8208bc77e2fa9e",
  "receipt_file":"8ab034122a244c9a8974b44ae8d84e3170c81b5d92c6d74b660059c950e3a797",
  "set_id":"proofgrid-v19-two-distinct-members",
  "scope_id":"proofgrid:v19:two-distinct-elements-partial",
}
EXPECTED_MEMBERS={
  "b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc":"15559.479677163699",
  "75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950":"7779.7398385818495",
}
EXPECTED_TOTAL="23339.2195157455485"
EXPECTED_COMPATIBILITY={"indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","unit":"kg CO2 eqv.","module":"A1-A3","scenario":None}
ZERO_DIGEST="0"*64
CANONICALIZATION="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
SCHEMA=ROOT/"schemas"/"partial-contribution-set-total-v20.schema.json"

class PartialSetTotalError(ValueError): pass

def require(c:bool,m:str)->None:
    if not c: raise PartialSetTotalError(m)

def canonical_json_bytes(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')

def pretty_json_bytes(v:Any)->bytes:
    return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf-8')

def sha256_bytes(v:bytes)->str: return hashlib.sha256(v).hexdigest()

def load_json(path:Path)->tuple[dict[str,Any],bytes]:
    try: raw=Path(path).read_bytes()
    except FileNotFoundError as e: raise PartialSetTotalError(f'missing required file: {path}') from e
    try: v=json.loads(raw.decode('utf-8'))
    except Exception as e: raise PartialSetTotalError(f'invalid UTF-8 JSON in {path}: {e}') from e
    require(isinstance(v,dict),f'expected JSON object: {path}')
    return v,raw

def canonical_decimal(value:Any,label:str)->str:
    require(isinstance(value,str) and value,f'{label} must be a non-empty Decimal string')
    try: n=Decimal(value)
    except InvalidOperation as e: raise PartialSetTotalError(f'{label} is not Decimal-compatible') from e
    require(n.is_finite(),f'{label} must be finite')
    rendered='0' if n==0 else format(n,'f')
    if '.' in rendered: rendered=rendered.rstrip('0').rstrip('.')
    require(rendered==value,f'{label} is not canonical Decimal')
    return value

def validate_schema(v:dict[str,Any])->None:
    schema=json.loads(SCHEMA.read_text(encoding='utf-8'))
    try: Draft202012Validator.check_schema(schema)
    except SchemaError as e: raise PartialSetTotalError(f'invalid v2.0 schema: {e.message}') from e
    errors=sorted(Draft202012Validator(schema).iter_errors(v),key=lambda e:list(e.path))
    if errors: raise PartialSetTotalError('v2.0 result failed schema validation: '+'; '.join(f'{list(e.path)}: {e.message}' for e in errors[:6]))

def verify_parent(record:dict[str,Any],raw:bytes,receipt:dict[str,Any],receipt_raw:bytes)->None:
    require(record.get('verdict')=='ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE','wrong contribution-set verdict')
    integrity=record.get('integrity'); require(isinstance(integrity,dict),'set missing integrity')
    claimed=integrity.get('content_sha256'); require(claimed==EXPECTED_SET['content'],'unaccepted set content identity')
    shadow=copy.deepcopy(record); shadow['integrity']['content_sha256']=ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow))==claimed,'set content digest mismatch')
    require(sha256_bytes(raw)==EXPECTED_SET['file'],'unaccepted set file identity')
    claimed_receipt=receipt.get('receipt_sha256'); require(claimed_receipt==EXPECTED_SET['receipt'],'unaccepted set receipt identity')
    rshadow=copy.deepcopy(receipt); rshadow.pop('receipt_sha256',None)
    require(sha256_bytes(canonical_json_bytes(rshadow))==claimed_receipt,'set receipt digest mismatch')
    require(sha256_bytes(receipt_raw)==EXPECTED_SET['receipt_file'],'unaccepted set receipt file identity')
    require(receipt.get('record_content_sha256')==claimed,'set receipt/content mismatch')
    require(receipt.get('record_file_sha256')==EXPECTED_SET['file'],'set receipt/file mismatch')
    require(record.get('set_id')==EXPECTED_SET['set_id'] and record.get('scope_id')==EXPECTED_SET['scope_id'],'set identity mismatch')
    require(record.get('completeness_status')=='PARTIAL','v2.0 requires PARTIAL source set')
    require(record.get('member_count')==2 and len(record.get('members',[]))==2,'v2.0 requires exactly two members')
    require(record.get('compatibility')==EXPECTED_COMPATIBILITY,'set compatibility mismatch')
    for key in ('aggregation_performed','sum_performed','missing_contributions_are_zero','missing_modules_are_zero','unit_conversion_performed','scenario_inference_performed','duplicate_members_permitted','scientific_validation_performed','professional_review_performed','certified'):
        require(record.get(key) is False,f'source set {key} promotion rejected')
        if key in receipt: require(receipt.get(key) is False,f'source set receipt {key} promotion rejected')

def aggregate_verified_set(record:dict[str,Any])->dict[str,Any]:
    members=record.get('members',[]); require(len(members)==2,'exactly two members required')
    ids=[]; normalized=[]
    for idx,member in enumerate(members):
        sid=member.get('semantic_identity_sha256'); semantic=member.get('semantic_identity',{})
        require(isinstance(sid,str) and len(sid)==64,f'member[{idx}] semantic identity missing')
        require(sha256_bytes(canonical_json_bytes(semantic))==sid,f'member[{idx}] semantic identity digest mismatch')
        require(sid in EXPECTED_MEMBERS,f'unaccepted member semantic identity: {sid}')
        value=canonical_decimal(semantic.get('value_decimal'),f'member[{idx}] value_decimal')
        require(value==EXPECTED_MEMBERS[sid],f'member[{idx}] exact Decimal mismatch')
        require(semantic.get('indicator_code')==EXPECTED_COMPATIBILITY['indicator_code'],'mixed indicator code')
        require(semantic.get('indicator_uuid')==EXPECTED_COMPATIBILITY['indicator_uuid'],'mixed indicator UUID')
        require(semantic.get('unit')==EXPECTED_COMPATIBILITY['unit'],'mixed environmental unit')
        require(semantic.get('module')==EXPECTED_COMPATIBILITY['module'],'mixed module')
        require(semantic.get('scenario') is None,'scenario inference/mismatch rejected')
        ids.append(sid)
        normalized.append({"semantic_identity_sha256":sid,"element_global_id":semantic['element_global_id'],"rxep_record_content_sha256":member['rxep']['record_content_sha256'],"calculation_record_content_sha256":member['calculation']['record_content_sha256'],"value_decimal":value,"unit":semantic['unit']})
    require(len(set(ids))==2,'duplicate semantic identities rejected')
    require(set(ids)==set(EXPECTED_MEMBERS),'accepted two-member identity set mismatch')
    normalized.sort(key=lambda m:m['semantic_identity_sha256'])
    with localcontext() as ctx:
        ctx.prec=100
        total=sum((Decimal(m['value_decimal']) for m in normalized),Decimal('0'))
    total_text=canonical_decimal(format(total,'f'),'partial-set total')
    require(total_text==EXPECTED_TOTAL,f'unexpected exact partial-set total: {total_text}')
    return {"members":normalized,"member_order":[m['semantic_identity_sha256'] for m in normalized],"total_value_decimal":total_text}

def build_total(record:dict[str,Any],raw:bytes,receipt:dict[str,Any],receipt_raw:bytes)->dict[str,Any]:
    verify_parent(record,raw,receipt,receipt_raw)
    agg=aggregate_verified_set(record)
    out={
      "schema_version":"1.0","record_type":"ProofGridPartialContributionSetExactDecimalTotal","verdict":VERDICT,
      "source_set":{"record_content_sha256":EXPECTED_SET['content'],"record_file_sha256":EXPECTED_SET['file'],"receipt_sha256":EXPECTED_SET['receipt'],"receipt_file_sha256":EXPECTED_SET['receipt_file'],"set_id":EXPECTED_SET['set_id'],"scope_id":EXPECTED_SET['scope_id']},
      "compatibility":copy.deepcopy(EXPECTED_COMPATIBILITY),"completeness_status":"PARTIAL","members":agg['members'],"member_count":2,
      "aggregation":{"method":"canonical_decimal_sum","version":"2.0.0","scope":"ADMITTED_SET_MEMBERS_ONLY","member_order":agg['member_order'],"total_value_decimal":agg['total_value_decimal'],"unit":"kg CO2 eqv."},
      "aggregation_performed":True,"sum_performed":True,"whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,
      "missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
      "limitations":["This is an exact Decimal sum of the two admitted members in the accepted PARTIAL contribution set only.","PARTIAL completeness is preserved; this total is not a complete building LCA or declared-scope-complete result.","No missing contribution/module is treated as zero and no unit conversion or scenario inference is performed.","Aggregation integrity does not establish scientific validity, professional review, regulatory approval, or certification."],
      "integrity":{"content_sha256":ZERO_DIGEST,"canonicalization":CANONICALIZATION,"signature":None}
    }
    out['integrity']['content_sha256']=sha256_bytes(canonical_json_bytes(out)); validate_schema(out); return out

def build_receipt(record:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={"verdict":VERDICT,"engine":{"name":ENGINE_NAME,"version":ENGINE_VERSION},"source_set_content_sha256":EXPECTED_SET['content'],"source_set_receipt_sha256":EXPECTED_SET['receipt'],"record_content_sha256":record['integrity']['content_sha256'],"record_file_sha256":sha256_bytes(raw),"member_count":2,"member_semantic_identity_sha256":record['aggregation']['member_order'],"total_value_decimal":EXPECTED_TOTAL,"unit":"kg CO2 eqv.","completeness_status":"PARTIAL","aggregation_performed":True,"sum_performed":True,"whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,"missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    r['receipt_sha256']=sha256_bytes(canonical_json_bytes(r)); return r

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument('--set-record',type=Path,required=True); p.add_argument('--set-receipt',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args(argv)
    try:
        record,raw=load_json(a.set_record); receipt,receipt_raw=load_json(a.set_receipt); total=build_total(record,raw,receipt,receipt_raw)
        a.output_dir.mkdir(parents=True,exist_ok=True); total_raw=pretty_json_bytes(total); (a.output_dir/'partial-contribution-set-exact-decimal-total.json').write_bytes(total_raw)
        out_receipt=build_receipt(total,total_raw); (a.output_dir/'partial-contribution-set-exact-decimal-total-receipt.json').write_bytes(pretty_json_bytes(out_receipt))
    except Exception as e:
        print(f'FAILED: {e}',file=sys.stderr); return 2
    print(f'RESULT: {VERDICT}'); print(f"EXACT PARTIAL TOTAL: {EXPECTED_TOTAL} kg CO2 eqv."); print('COMPLETENESS: PARTIAL'); print('NOT A WHOLE-BUILDING LCA'); print('NOT CERTIFIED'); return 0
if __name__=='__main__': raise SystemExit(main())
