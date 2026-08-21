#!/usr/bin/env python3
"""ProofGrid v1.5 explicit IFC material -> declaration product mapping.

Consumes one exact IFC extraction, one explicit reviewed mapping artifact, and
one accepted v1.4.1 declaration product-identity closure. Mapping authority is
carried by exact identifiers and the explicit artifact, never by name similarity.
No environmental multiplication or unit conversion is performed.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, SchemaError

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from reference import declaration_evidence_bundle as v14
from reference import declaration_product_identity_closure as v141
from reference import ifc_lca_map as ifcmap

ENGINE_NAME="RegenExcalibur ProofGrid IFC Declaration Product Mapper"
ENGINE_VERSION="1.5.0"
VERDICT="IFC_DECLARATION_PRODUCT_MAPPING_VERIFIABLE"
METHOD="EXPLICIT_REVIEWED_ARTIFACT"
ZERO_DIGEST="0"*64
CANONICALIZATION=v14.CANONICALIZATION
IFC_SCHEMA=ROOT/'schemas'/'ifc-extraction.schema.json'
MAPPING_SCHEMA=ROOT/'schemas'/'ifc-declaration-product-mapping.schema.json'
RESULT_SCHEMA=ROOT/'schemas'/'ifc-declaration-product-mapping-result.schema.json'

class ProductMappingError(ValueError): pass

def require(c:bool,m:str)->None:
    if not c: raise ProductMappingError(m)

def canonical_json_bytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha256_bytes(v:bytes)->str: return hashlib.sha256(v).hexdigest()

def load_json(path:Path)->tuple[dict[str,Any],bytes]:
    try: raw=path.read_bytes()
    except FileNotFoundError as e: raise ProductMappingError(f'missing required file: {path}') from e
    try: v=json.loads(raw.decode('utf-8'))
    except Exception as e: raise ProductMappingError(f'invalid UTF-8 JSON in {path}: {e}') from e
    require(isinstance(v,dict),f'expected JSON object: {path}')
    return v,raw

def validate_schema(v:Any,path:Path,label:str)->None:
    schema=json.loads(path.read_text(encoding='utf-8'))
    try: Draft202012Validator.check_schema(schema)
    except SchemaError as e: raise ProductMappingError(f'invalid {label} schema: {e.message}') from e
    errors=sorted(Draft202012Validator(schema).iter_errors(v),key=lambda e:list(e.path))
    if errors: raise ProductMappingError(f"{label} failed schema validation: "+'; '.join(f'{list(e.path)}: {e.message}' for e in errors[:6]))

def verify_closure(record:dict[str,Any],raw:bytes,receipt:dict[str,Any])->dict[str,Any]:
    require(record.get('verdict')==v141.VERDICT,'v1.4.1 closure verdict mismatch')
    content=v14.verify_record_integrity(record,label='v1.4.1 declaration product closure')
    v14.verify_receipt(receipt,label='v1.4.1 closure receipt',verdict=v141.VERDICT)
    require(receipt.get('record_content_sha256')==content,'v1.4.1 receipt/content mismatch')
    require(receipt.get('record_file_sha256')==sha256_bytes(raw),'v1.4.1 receipt/file mismatch')
    require(receipt.get('source_identity')==record.get('source_identity'),'v1.4.1 source identity receipt mismatch')
    require(receipt.get('product_flow')==record.get('product_flow'),'v1.4.1 product-flow receipt mismatch')
    require(receipt.get('declared_reference_basis')==record.get('declared_reference_basis'),'v1.4.1 basis receipt mismatch')
    for k in ('calculated','environmental_values_transformed','building_quantity_multiplication_performed','aggregation_performed','unit_conversion_performed','scientific_validation_performed','professional_review_performed','certified'):
        require(record.get(k) is False,f'v1.4.1 {k} promotion rejected')
        require(receipt.get(k) is False,f'v1.4.1 receipt {k} promotion rejected')
    v141.validate_internal_identity(record)
    product=record['product_flow']; basis=record['declared_reference_basis']; source=record['source_identity']
    require(basis['unit']=='kg',f"initial v1.5 unit gate requires declaration reference unit kg, got {basis['unit']!r}")
    return {
      'closure_content_sha256':content,
      'closure_receipt_sha256':receipt['receipt_sha256'],
      'source_sha256':source['source_sha256'],
      'process_xml_sha256':source['process_xml_sha256'],
      'process_dataset_uuid':source['process_dataset_uuid'],
      'format_version':source['format_version'],
      'product_flow_uuid':product['uuid'],
      'product_flow_version':product['version'],
      'product_flow_sha256':product['sha256'],
      'reference_quantity_decimal':basis['quantity_decimal'],
      'reference_unit':basis['unit'],
    }

def map_product(extraction_path:Path,mapping_path:Path,closure_path:Path,closure_receipt_path:Path)->dict[str,Any]:
    extraction,extraction_raw=load_json(extraction_path); mapping_artifact,mapping_raw=load_json(mapping_path)
    closure_record,closure_raw=load_json(closure_path); closure_receipt,_=load_json(closure_receipt_path)
    validate_schema(extraction,IFC_SCHEMA,'IFC extraction'); validate_schema(mapping_artifact,MAPPING_SCHEMA,'explicit mapping artifact')
    declaration=verify_closure(closure_record,closure_raw,closure_receipt)
    mapping=mapping_artifact['mapping']
    require(mapping['review']['state']=='REVIEWED_MAPPING_DECISION','mapping decision is not REVIEWED_MAPPING_DECISION')
    require(mapping['source_ifc']['sha256']==extraction['source_sha256'],'mapping IFC source SHA mismatch')
    require(mapping['source_ifc']['schema']==extraction['schema'],'mapping IFC schema mismatch')
    require(mapping['declaration']==declaration,'mapping declaration target does not exactly match accepted v1.4.1 closure')
    try:
        element=ifcmap._find_element(extraction,mapping); material=ifcmap._find_material(element,mapping); quantity=ifcmap._find_quantity(element,mapping)
        unit_identity=ifcmap.explicit_unit_identity(quantity['unit'])
    except ifcmap.MappingError as e: raise ProductMappingError(str(e)) from e
    require(unit_identity==declaration['reference_unit'],'IFC quantity unit is not identical to declaration product/reference unit')
    require(mapping['quantity']['value']==quantity['value'],'mapping quantity changed after extraction')
    record={
      'schema_version':'1.0','record_type':'ProofGridIFCDeclarationProductMapping','verdict':VERDICT,'mapping_id':mapping['id'],
      'ifc':{
        'extraction_file_sha256':sha256_bytes(extraction_raw),'source_sha256':extraction['source_sha256'],'schema':extraction['schema'],
        'element':{'step_id':element['step_id'],'global_id':element['global_id'],'ifc_type':element['ifc_type'],'name':element.get('name')},
        'material':{'association_step_id':material['association_step_id'],'material_step_id':material['material_step_id'],'declared_name':material['name'],'source_type':material['source_type']},
        'quantity':{'set_step_id':quantity['set_step_id'],'quantity_step_id':quantity['quantity_step_id'],'name':quantity['name'],'ifc_quantity_type':quantity['ifc_quantity_type'],'value':quantity['value'],'unit_identity':unit_identity,'unit':quantity['unit'],'value_source':quantity['value_source'],'numerical_conversion_applied':False},
      },
      'declaration':declaration,'review':copy.deepcopy(mapping['review']),
      'mapping_artifact':{'file_sha256':sha256_bytes(mapping_raw),'artifact_version':mapping_artifact['artifact_version']},
      'mapping_method':METHOD,'fuzzy_matching_performed':False,'automatic_name_mapping_performed':False,
      'environmental_calculation_performed':False,'building_quantity_multiplication_performed':False,'unit_conversion_performed':False,
      'scientific_validation_performed':False,'professional_review_performed':False,'certified':False,
      'limitations':list(mapping['limitations'])+[
        'Mapping authority comes from the explicit reviewed artifact and exact identifiers, not display-name similarity.',
        'The IFC quantity is preserved as evidence only; no environmental result is multiplied by it.',
        'kg-to-kg is accepted only as an identity unit relationship; no numerical conversion is performed.',
        'Workflow review state does not imply professional licensure, scientific validity, engineering approval, programme-operator authority, regulatory approval, or certification.'
      ],
      'integrity':{'content_sha256':ZERO_DIGEST,'canonicalization':CANONICALIZATION,'signature':None},
    }
    record['integrity']['content_sha256']=sha256_bytes(canonical_json_bytes(record)); validate_schema(record,RESULT_SCHEMA,'mapping result'); return record

def build_receipt(record:dict[str,Any],raw:bytes)->dict[str,Any]:
    r={'verdict':VERDICT,'certified':False,'engine':{'name':ENGINE_NAME,'version':ENGINE_VERSION},'mapping_id':record['mapping_id'],'record_content_sha256':record['integrity']['content_sha256'],'record_file_sha256':sha256_bytes(raw),'ifc_source_sha256':record['ifc']['source_sha256'],'closure_content_sha256':record['declaration']['closure_content_sha256'],'closure_receipt_sha256':record['declaration']['closure_receipt_sha256'],'product_flow_uuid':record['declaration']['product_flow_uuid'],'product_flow_version':record['declaration']['product_flow_version'],'reference_unit':record['declaration']['reference_unit'],'mapping_method':METHOD,'fuzzy_matching_performed':False,'automatic_name_mapping_performed':False,'environmental_calculation_performed':False,'building_quantity_multiplication_performed':False,'unit_conversion_performed':False,'scientific_validation_performed':False,'professional_review_performed':False,'limitations':list(record['limitations'])}
    r['receipt_sha256']=sha256_bytes(canonical_json_bytes(r)); return r

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(); p.add_argument('--ifc-extraction',type=Path,required=True); p.add_argument('--mapping',type=Path,required=True); p.add_argument('--closure',type=Path,required=True); p.add_argument('--closure-receipt',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args(argv)
    try:
        record=map_product(a.ifc_extraction,a.mapping,a.closure,a.closure_receipt); a.output_dir.mkdir(parents=True,exist_ok=True)
        raw=(json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode(); (a.output_dir/'ifc-declaration-product-mapping.json').write_bytes(raw)
        receipt=build_receipt(record,raw); (a.output_dir/'ifc-declaration-product-mapping-receipt.json').write_bytes((json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode())
    except Exception as e: print(f'FAILED: {e}',file=sys.stderr); return 2
    print(f'RESULT: {VERDICT}'); print(f"PRODUCT FLOW: {record['declaration']['product_flow_uuid']} @ {record['declaration']['product_flow_version']}"); print(f"IFC QUANTITY: {record['ifc']['quantity']['value']} {record['ifc']['quantity']['unit_identity']}"); print('BUILDING QUANTITY MULTIPLICATION PERFORMED: false'); print('NOT CERTIFIED'); return 0
if __name__=='__main__': raise SystemExit(main())
