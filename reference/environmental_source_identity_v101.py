#!/usr/bin/env python3
"""ProofGrid v1.0.1 canonical environmental source identity.

v1.0.1 preserves the historical v1.0 normalizer and applies the v0.9.1
exact-stack admission consumer only for the duration of a v1.0.1 operation.
The original module is restored immediately afterward so importing this module
cannot alter historical v1.0 behavior or unrelated test suites.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from reference import environmental_admission_v091 as hardened  # noqa: E402
from reference import environmental_source_identity as base  # noqa: E402

CanonicalizationError=base.CanonicalizationError
canonical_json_bytes=base.canonical_json_bytes
sha256_bytes=base.sha256_bytes
sha256_file=base.sha256_file
load_json=base.load_json
validate_schema=base.validate_schema


@contextmanager
def _hardened_context():
    old_admission=base.admission
    old_process_ns=base.PROCESS_NS
    old_epd_ns=base.EPD_2019_NS
    try:
        base.admission=hardened
        base.PROCESS_NS=hardened.PROCESS_NS
        base.EPD_2019_NS=hardened.EPD_2019_NS
        yield
    finally:
        base.admission=old_admission
        base.PROCESS_NS=old_process_ns
        base.EPD_2019_NS=old_epd_ns


def verify_receipt_chain(preflight_receipt,conformance_receipt,admission_receipt):
    with _hardened_context():
        return base.verify_receipt_chain(preflight_receipt,conformance_receipt,admission_receipt)


def extract_process_identity(raw:bytes,*,label:str,expected_version:str):
    with _hardened_context():
        return base.extract_process_identity(raw,label=label,expected_version=expected_version)


def source_identity(source_path:Path,*,media_type:str,expected_version:str):
    with _hardened_context():
        return base.source_identity(source_path,media_type=media_type,expected_version=expected_version)


def build_record(source_path:Path,preflight_receipt,conformance_receipt,admission_receipt):
    with _hardened_context():
        return base.build_record(source_path,preflight_receipt,conformance_receipt,admission_receipt)


def build_receipt(record,record_file_bytes:bytes):
    receipt=base.build_receipt(record,record_file_bytes)
    receipt["engine"]["version"]="1.0.1"
    receipt.pop("receipt_sha256",None)
    receipt["receipt_sha256"]=sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def normalize(source_path:Path,*,preflight_path:Path,conformance_path:Path,admission_path:Path,output_dir:Path):
    preflight=load_json(preflight_path)
    conformance=load_json(conformance_path)
    admission_receipt=load_json(admission_path)
    record=build_record(source_path,preflight,conformance,admission_receipt)
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    record_path=output_dir/"canonical-source-identity.json"
    record_bytes=(json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt=build_receipt(record,record_bytes)
    (output_dir/"canonicalization-receipt.json").write_bytes((json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8"))
    return record,receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description="ProofGrid v1.0.1 exact-stack admission-bound environmental source identity normalizer")
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--preflight",type=Path,required=True)
    parser.add_argument("--conformance",type=Path,required=True)
    parser.add_argument("--admission",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        record,receipt=normalize(args.source,preflight_path=args.preflight,conformance_path=args.conformance,admission_path=args.admission,output_dir=args.output_dir)
    except (CanonicalizationError,hardened.AdmissionError) as exc:
        print(f"FAILED: {exc}",file=sys.stderr)
        return 2
    print(f"RESULT: {receipt['verdict']}")
    print(f"SOURCE IDENTITY: {record['identity']['process_dataset_uuid']}")
    print(f"FORMAT: ILCD+EPD v{record['source']['format_version']}")
    print("IMPACT VALUES NORMALIZED: false")
    print("SCIENTIFIC VALIDATION: false")
    print("PROFESSIONAL REVIEW: false")
    print("NOT CERTIFIED")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
