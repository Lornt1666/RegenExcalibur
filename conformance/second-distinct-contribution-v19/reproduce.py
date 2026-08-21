#!/usr/bin/env python3
"""Reproduce the ProofGrid v1.9 second distinct contribution in one clean runner."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

import ifcopenshell

from adapters.ifc.extract import extract_ifc_declared_data
from reference import ifc_extract
from reference import ifc_declaration_product_map as mapper
from reference import ifc_quantity_decimal as qdec
from reference import second_distinct_contribution_v19 as v19

ELEMENT_GLOBAL_ID=v19.SECOND_ELEMENT_GLOBAL_ID
MAPPING_ID=v19.SECOND_MAPPING_ID
SYNTHETIC_SOURCE_URI="synthetic://proofgrid-v19/fixture.ifc"

def pretty(v): return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def build_ifc(path:Path):
    m=ifcopenshell.file(schema="IFC4")
    mass=m.create_entity("IfcSIUnit",UnitType="MASSUNIT",Prefix="KILO",Name="GRAM")
    units=m.create_entity("IfcUnitAssignment",Units=[mass])
    m.create_entity("IfcProject",GlobalId="0iS$wWKLjAuhSPZ5IG0yTx",Name="ProofGrid v1.9 second control",UnitsInContext=units)
    wall=m.create_entity("IfcWall",GlobalId=ELEMENT_GLOBAL_ID,Name="Second Mapped Wall")
    material=m.create_entity("IfcMaterial",Name="RX-MATERIAL-SECOND-CONTROL-NOT-WOOD-PANEL")
    m.create_entity("IfcRelAssociatesMaterial",GlobalId="2CXL7DJx51bvggyIPU2Xi6",RelatedObjects=[wall],RelatingMaterial=material)
    q=m.create_entity("IfcQuantityWeight",Name="Mass",WeightValue=500.0)
    qset=m.create_entity("IfcElementQuantity",GlobalId="3CXL7DJx51bvggyIPU2Xi6",Name="Qto_WallBaseQuantities",Quantities=[q])
    m.create_entity("IfcRelDefinesByProperties",GlobalId="0CXL7DJx51bvggyIPU2Xi6",RelatedObjects=[wall],RelatingPropertyDefinition=qset)
    m.write(str(path))
    text=path.read_text(encoding="utf-8")
    text,count=re.subn(r"(FILE_NAME\('[^']*',)'[^']*'",r"\1'2026-01-01T00:00:00'",text,count=1)
    if count != 1: raise RuntimeError(f"expected one FILE_NAME timestamp replacement, got {count}")
    path.write_text(text,encoding="utf-8",newline="\n")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--v141",type=Path,required=True); p.add_argument("--v14",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--replica",required=True)
    a=p.parse_args(); root=a.output_dir; root.mkdir(parents=True,exist_ok=True)
    closure=a.v141/"v13/a/declaration-product-identity-closure.json"; closure_receipt=a.v141/"v13/a/declaration-product-identity-closure-receipt.json"
    bundle=a.v14/"v13/a/declaration-evidence-bundle.json"; bundle_receipt=a.v14/"v13/a/declaration-evidence-bundle-receipt.json"

    source=root/"fixture.ifc"; build_ifc(source)
    extraction=extract_ifc_declared_data(source)
    # Synthetic-only canonicalization: absolute hosted-runner paths are not evidence authority.
    # The raw IFC bytes remain unchanged and are bound by source_sha256 below.
    extraction["source"]=SYNTHETIC_SOURCE_URI
    ifc_extract.validate_output(extraction)
    extraction_path=root/"ifc-extraction.json"; extraction_path.write_bytes(pretty(extraction))

    closure_record,closure_raw=mapper.load_json(closure); closure_receipt_obj,_=mapper.load_json(closure_receipt)
    declaration=mapper.verify_closure(closure_record,closure_raw,closure_receipt_obj)
    elements=[e for e in extraction["elements"] if e.get("global_id")==ELEMENT_GLOBAL_ID]
    if len(elements)!=1: raise RuntimeError(f"expected one second element, got {len(elements)}")
    element=elements[0]
    if len(element["materials"])!=1 or len(element["quantities"])!=1: raise RuntimeError("expected one material and one quantity")
    material=element["materials"][0]; quantity=element["quantities"][0]; unit=quantity["unit"]
    mapping_artifact={"schema_version":"1.0","artifact_version":"1.5.0","mapping":{"id":MAPPING_ID,"source_ifc":{"sha256":extraction["source_sha256"],"schema":extraction["schema"]},"element":{"step_id":element["step_id"],"global_id":element["global_id"],"ifc_type":element["ifc_type"]},"material":{"association_step_id":material["association_step_id"],"material_step_id":material["material_step_id"],"declared_name":material["name"],"source_type":material["source_type"]},"quantity":{"set_step_id":quantity["set_step_id"],"quantity_step_id":quantity["quantity_step_id"],"name":quantity["name"],"ifc_quantity_type":quantity["ifc_quantity_type"],"value":quantity["value"],"unit":{"unit_type":unit["unit_type"],"name":unit["name"],"prefix":unit["prefix"],"source":unit["source"]}},"declaration":declaration,"review":{"state":"REVIEWED_MAPPING_DECISION","reviewer":"RegenExcalibur v1.9 synthetic conformance harness","role":"synthetic_test_mapping_decision","rationale":"Explicit exact-ID mapping for a second synthetic conformance contribution; not a professional review.","reference":"ProofGrid issue #58"},"limitations":["Synthetic mapping control only; no professional/licensed review is claimed.","Display-name similarity is not mapping authority."]}}
    mapping_artifact_path=root/"mapping-artifact.json"; mapping_artifact_path.write_bytes(pretty(mapping_artifact))
    mapping_record=mapper.map_product(extraction_path,mapping_artifact_path,closure,closure_receipt)
    mapping_path=root/"ifc-declaration-product-mapping.json"; mapping_raw=pretty(mapping_record); mapping_path.write_bytes(mapping_raw)
    mapping_receipt=mapper.build_receipt(mapping_record,mapping_raw); mapping_receipt_path=root/"ifc-declaration-product-mapping-receipt.json"; mapping_receipt_path.write_bytes(pretty(mapping_receipt))

    quantity_record=qdec.extract(mapping_record,mapping_raw,mapping_receipt,source.read_bytes())
    quantity_path=root/"ifc-declared-quantity-exact-decimal.json"; quantity_raw=pretty(quantity_record); quantity_path.write_bytes(quantity_raw)
    quantity_receipt=qdec.build_receipt(quantity_record,quantity_raw); quantity_receipt_path=root/"ifc-declared-quantity-exact-decimal-receipt.json"; quantity_receipt_path.write_bytes(pretty(quantity_receipt))

    calc=v19.calculate(quantity_path,quantity_receipt_path,mapping_path,mapping_receipt_path,closure,closure_receipt,bundle,bundle_receipt)
    calc_path=root/"mapped-declared-result-calculation.json"; calc_raw=pretty(calc); calc_path.write_bytes(calc_raw)
    calc_receipt=v19.calculation_receipt(calc,calc_raw); calc_receipt_path=root/"mapped-declared-result-calculation-receipt.json"; calc_receipt_path.write_bytes(pretty(calc_receipt))

    assert quantity_record["quantity"]["quantity_decimal"]=="500"
    assert calc["calculation"]["scaled_result_decimal"]==v19.EXPECTED_RESULT_DECIMAL
    report={"verdict":"SECOND_DISTINCT_CONTRIBUTION_REPLICA_VERIFIABLE","replica":a.replica,"ifc_source_sha256":sha(source),"element_global_id":ELEMENT_GLOBAL_ID,"quantity_lexical":quantity_record["quantity"]["quantity_lexical"],"quantity_decimal":"500","mapping_record_content_sha256":mapping_record["integrity"]["content_sha256"],"mapping_record_file_sha256":sha(mapping_path),"mapping_receipt_sha256":mapping_receipt["receipt_sha256"],"quantity_record_content_sha256":quantity_record["integrity"]["content_sha256"],"quantity_record_file_sha256":sha(quantity_path),"quantity_receipt_sha256":quantity_receipt["receipt_sha256"],"calculation_record_content_sha256":calc["integrity"]["content_sha256"],"calculation_record_file_sha256":sha(calc_path),"calculation_receipt_sha256":calc_receipt["receipt_sha256"],"calculation_receipt_file_sha256":sha(calc_receipt_path),"scaled_result_decimal":v19.EXPECTED_RESULT_DECIMAL,"scaled_result_unit":"kg CO2 eqv.","source_token_is_authority":True,"parser_numeric_value_is_authority":False,"aggregation_performed":False,"certified":False}
    report["receipt_sha256"]=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    (root/"replica-receipt.json").write_bytes(pretty(report))
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
