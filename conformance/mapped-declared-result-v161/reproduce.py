#!/usr/bin/env python3
"""Independent hosted reproduction harness for accepted ProofGrid v1.6."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.mapped_declared_result_scale import scale, write_outputs

EXPECTED = {
    "record_content_sha256": "1eff779368d48de3a9c637d0a9298788487c67480d6134c18302af1bacf7848e",
    "record_file_sha256": "69921546aa24dd6e0e950964aa3e9bc8bd962f14ab6855f868a5fa8ed639e8d7",
    "calculation_receipt_sha256": "486c4a9e133bf88ec563215649acdf991c4806a31751ddd6895acbac86615af8",
    "calculation_receipt_file_sha256": "a21dbe86fce8eb707fc09b57f5638b8d8d1bcb99ae8712fb16fae2d2f894e69f",
    "scaled_result_decimal": "15559.479677163699",
}


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--v151",type=Path,required=True)
    p.add_argument("--v15",type=Path,required=True)
    p.add_argument("--v141",type=Path,required=True)
    p.add_argument("--v14",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--replica",required=True)
    args=p.parse_args(argv)

    paths={
        "q":args.v151/"out-a/ifc-declared-quantity-exact-decimal.json",
        "qr":args.v151/"out-a/ifc-declared-quantity-exact-decimal-receipt.json",
        "m":args.v15/"out-a/ifc-declaration-product-mapping.json",
        "mr":args.v15/"out-a/ifc-declaration-product-mapping-receipt.json",
        "c":args.v141/"v13/a/declaration-product-identity-closure.json",
        "cr":args.v141/"v13/a/declaration-product-identity-closure-receipt.json",
        "b":args.v14/"v13/a/declaration-evidence-bundle.json",
        "br":args.v14/"v13/a/declaration-evidence-bundle-receipt.json",
    }
    data={k:load(v) for k,v in paths.items()}
    request={
        "schema_version":"1.0",
        "request_version":"1.6.0",
        "bindings":{
            "quantity_record_content_sha256":data["q"]["integrity"]["content_sha256"],
            "quantity_record_file_sha256":file_sha(paths["q"]),
            "quantity_receipt_sha256":data["qr"]["receipt_sha256"],
            "mapping_record_content_sha256":data["m"]["integrity"]["content_sha256"],
            "mapping_record_file_sha256":file_sha(paths["m"]),
            "mapping_receipt_sha256":data["mr"]["receipt_sha256"],
            "closure_record_content_sha256":data["c"]["integrity"]["content_sha256"],
            "closure_record_file_sha256":file_sha(paths["c"]),
            "closure_receipt_sha256":data["cr"]["receipt_sha256"],
            "declaration_bundle_content_sha256":data["b"]["integrity"]["content_sha256"],
            "declaration_bundle_file_sha256":file_sha(paths["b"]),
            "declaration_bundle_receipt_sha256":data["br"]["receipt_sha256"],
        },
        "selection":{
            "indicator_code":"GWP-total",
            "indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2",
            "module":"A1-A3",
            "scenario":None,
            "expected_unit":"kg CO2 eqv.",
        },
    }
    args.output_dir.mkdir(parents=True,exist_ok=True)
    req=args.output_dir/"request.json"
    req.write_text(json.dumps(request,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    result=scale(paths["q"],paths["qr"],paths["m"],paths["mr"],paths["c"],paths["cr"],paths["b"],paths["br"],req)
    outputs=write_outputs(result,args.output_dir)
    if result["integrity"]["content_sha256"] != EXPECTED["record_content_sha256"]: raise SystemExit("accepted v1.6 record content did not reproduce")
    if outputs["record_file_sha256"] != EXPECTED["record_file_sha256"]: raise SystemExit("accepted v1.6 record file did not reproduce")
    if outputs["receipt_sha256"] != EXPECTED["calculation_receipt_sha256"]: raise SystemExit("accepted v1.6 calculation receipt did not reproduce")
    if outputs["receipt_file_sha256"] != EXPECTED["calculation_receipt_file_sha256"]: raise SystemExit("accepted v1.6 calculation receipt file did not reproduce")
    if result["calculation"]["scaled_result_decimal"] != EXPECTED["scaled_result_decimal"]: raise SystemExit("accepted v1.6 Decimal result did not reproduce")
    replica={"verdict":"MAPPED_DECLARED_RESULT_SCALED_REPLICA_VERIFIABLE","replica":args.replica,"accepted_v16_head":"99876aadeef1b17bdf4a8a739df1c830fb80b9d3","request_file_sha256":file_sha(req),"record_content_sha256":result["integrity"]["content_sha256"],"record_file_sha256":outputs["record_file_sha256"],"calculation_receipt_sha256":outputs["receipt_sha256"],"calculation_receipt_file_sha256":outputs["receipt_file_sha256"],"scaled_result_decimal":result["calculation"]["scaled_result_decimal"],"scaled_result_unit":result["calculation"]["scaled_result_unit"],"source_token_is_authority":True,"parser_numeric_value_is_authority":False,"aggregation_performed":False,"unit_conversion_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    replica["receipt_sha256"]=hashlib.sha256(json.dumps(replica,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    (args.output_dir/"replica-receipt.json").write_text(json.dumps(replica,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(replica,indent=2,sort_keys=True)); return 0


if __name__=="__main__":
    raise SystemExit(main())
