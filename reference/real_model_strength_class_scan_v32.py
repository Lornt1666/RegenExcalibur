#!/usr/bin/env python3
"""ProofGrid v3.2 model-wide literal concrete strength-class source scan.

Scans the entire exact native IFC STEP text for literal EN-style concrete class
tokens Cxx/yy. This scanner intentionally does not invoke an IFC helper/parser:
the accepted v3.0 inventory already proves the model identity and 1,026-product
inventory. This gate asks only whether the exact native source bytes literally
contain a strength-class token. If absent, ProofGrid cannot infer one from STB,
Ortbeton, geometry, structural role, or common construction practice.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

SOURCE_SHA256="19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb"
SOURCE_BYTES=9022255
ACCEPTED_V30_IFC_PRODUCT_COUNT=1026
ACCEPTED_V30_INVENTORY_IDENTITY_SET_SHA256="e7f1271f7a601caea4a52e246dcd70f0c3e29f0b6788e2111b4f5929b89b77d8"
VERDICT="REAL_IFC_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_VERIFIABLE"
PATTERN=re.compile(r"(?<![A-Z0-9])C\s*(\d{2})\s*/\s*(\d{2})(?![0-9])",re.I)
CANON="UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
class ScanError(ValueError): pass
def require(c,m):
    if not c: raise ScanError(m)
def cbytes(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def pbytes(v:Any)->bytes: return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def build(path:Path):
    raw=path.read_bytes(); require(len(raw)==SOURCE_BYTES,"source byte-size mismatch"); require(sha(raw)==SOURCE_SHA256,"source SHA mismatch")
    text=raw.decode("utf-8")
    occurrences=[]
    for line_no,line in enumerate(text.splitlines(),start=1):
        for match in PATTERN.finditer(line):
            step_match=re.match(r"\s*#(\d+)\s*=",line)
            occurrences.append({
                "line_number":line_no,
                "step_id":int(step_match.group(1)) if step_match else None,
                "normalized_class":f"C{match.group(1)}/{match.group(2)}",
                "matched_lexical":match.group(0),
                "source_line_sha256":sha(line.encode("utf-8")),
                "source_line":line,
            })
    occurrences.sort(key=lambda x:(x["line_number"],x["normalized_class"],x["matched_lexical"]))
    classes=sorted({o["normalized_class"] for o in occurrences})
    record={
      "schema_version":"1.0",
      "record_type":"ProofGridRealIFCLiteralConcreteStrengthClassSourceScan",
      "verdict":VERDICT,
      "source":{"sha256":SOURCE_SHA256,"file_bytes":SOURCE_BYTES,"accepted_v30_ifc_product_count":ACCEPTED_V30_IFC_PRODUCT_COUNT,"accepted_v30_inventory_identity_set_sha256":ACCEPTED_V30_INVENTORY_IDENTITY_SET_SHA256},
      "source_occurrence_count":len(occurrences),
      "literal_strength_classes":classes,
      "target_classes":{"C25/30_present":"C25/30" in classes,"C30/37_present":"C30/37" in classes},
      "occurrences":occurrences,
      "method":{"scope":"ENTIRE_NATIVE_IFC_UTF8_SOURCE_TEXT","literal_regex":"C\\s*dd\\s*/\\s*dd","ifc_parser_invoked_by_this_scan":False,"helper_api_inference_used":False,"inference_from_stb_or_material_names":False,"fuzzy_matching":False},
      "authority_boundaries":{"mapping_performed":False,"impact_calculation_performed":False,"scientific_suitability_decided":False,"certified":False},
    }
    record["integrity"]={"content_sha256":sha(cbytes(record)),"canonicalization":CANON,"signature":None}; return record
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--ifc",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(argv)
    try: r=build(a.ifc); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(pbytes(r))
    except Exception as exc: print(f"FAILED: {exc}",file=sys.stderr); return 2
    print(f"RESULT: {VERDICT}"); print('SOURCE_OCCURRENCES='+str(r['source_occurrence_count'])); print('CLASSES='+','.join(r['literal_strength_classes'])); print('C25_30_PRESENT='+str(r['target_classes']['C25/30_present']).lower()); print('C30_37_PRESENT='+str(r['target_classes']['C30/37_present']).lower()); return 0
if __name__=='__main__': raise SystemExit(main())
