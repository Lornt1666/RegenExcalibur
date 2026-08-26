#!/usr/bin/env python3
"""ProofGrid v3.2 model-wide literal concrete strength-class scan.

Scans exact source strings across all IfcProduct objects for literal EN-style
concrete class tokens Cxx/yy. It does not infer classes from material names,
object families, geometry, structural role, or language-specific shorthand.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any
import ifcopenshell
import ifcopenshell.util.element
from reference.real_model_source_suitability_probe_v32 import entity_attributes, scalar, direct_material_associations, classification_associations

SOURCE_SHA256="19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb"
SOURCE_BYTES=9022255
VERDICT="REAL_IFC_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_VERIFIABLE"
PATTERN=re.compile(r"(?<![A-Z0-9])C\s*(\d{2})\s*/\s*(\d{2})(?![0-9])",re.I)
ZERO="0"*64
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
class ScanError(ValueError): pass
def require(c,m):
    if not c: raise ScanError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def collect(value:Any,path:str=""):
    out=[]
    if isinstance(value,str):
        for m in PATTERN.finditer(value): out.append({"path":path or "$","value":value,"normalized_class":f"C{m.group(1)}/{m.group(2)}"})
    elif isinstance(value,dict):
        for k in sorted(value): out.extend(collect(value[k],f"{path}.{k}" if path else str(k)))
    elif isinstance(value,list):
        for i,x in enumerate(value): out.extend(collect(x,f"{path}[{i}]"))
    return out
def psets(element):
    try: return scalar(ifcopenshell.util.element.get_psets(element,psets_only=False,qtos_only=False,should_inherit=True,verbose=True))
    except TypeError: return scalar(ifcopenshell.util.element.get_psets(element,should_inherit=True))
def type_context(element):
    try: typ=ifcopenshell.util.element.get_type(element)
    except Exception: typ=None
    if typ is None: return None
    return {"step_id":int(typ.id()),"ifc_type":str(typ.is_a()),"attributes":entity_attributes(typ),"property_sets":psets(typ),"material_associations":direct_material_associations(typ),"classification_associations":classification_associations(typ)}
def build(path:Path):
    raw=path.read_bytes(); require(len(raw)==SOURCE_BYTES,"source byte-size mismatch"); require(sha(raw)==SOURCE_SHA256,"source SHA mismatch")
    model=ifcopenshell.open(str(path)); products=sorted(model.by_type("IfcProduct"),key=lambda e:int(e.id())); rows=[]; scanned_strings=0
    for e in products:
        ctx={"element":{"step_id":int(e.id()),"global_id":getattr(e,"GlobalId",None),"ifc_type":str(e.is_a()),"attributes":entity_attributes(e),"property_sets":psets(e),"material_associations":direct_material_associations(e),"classification_associations":classification_associations(e)},"type":type_context(e)}
        matches=collect(ctx); scanned_strings += len([x for x in _all_strings(ctx)])
        if matches:
            rows.append({"step_id":int(e.id()),"global_id":getattr(e,"GlobalId",None),"ifc_type":str(e.is_a()),"name":getattr(e,"Name",None),"matches":matches})
    classes=sorted({m["normalized_class"] for r in rows for m in r["matches"]})
    record={"schema_version":"1.0","record_type":"ProofGridRealIFCLiteralConcreteStrengthClassScan","verdict":VERDICT,"source":{"sha256":SOURCE_SHA256,"file_bytes":SOURCE_BYTES},"enumerated_ifc_product_count":len(products),"matched_product_count":len(rows),"literal_strength_classes":classes,"target_classes":{"C25/30_present":any(x=="C25/30" for x in classes),"C30/37_present":any(x=="C30/37" for x in classes)},"matched_products":rows,"method":{"literal_regex":"C\\s*dd\\s*/\\s*dd","inference_from_stb_or_material_names":False,"fuzzy_matching":False},"authority_boundaries":{"mapping_performed":False,"impact_calculation_performed":False,"scientific_suitability_decided":False,"certified":False}}
    record["integrity"]={"content_sha256":sha(cbytes(record)),"canonicalization":CANON,"signature":None}; return record
def _all_strings(value:Any):
    if isinstance(value,str): yield value
    elif isinstance(value,dict):
        for k in sorted(value): yield from _all_strings(value[k])
    elif isinstance(value,list):
        for x in value: yield from _all_strings(x)
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--ifc",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    try: r=build(a.ifc); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(pbytes(r))
    except Exception as exc: print(f"FAILED: {exc}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print('MATCHED_PRODUCTS='+str(r['matched_product_count'])); print('CLASSES='+','.join(r['literal_strength_classes'])); return 0
if __name__=='__main__': raise SystemExit(main())
