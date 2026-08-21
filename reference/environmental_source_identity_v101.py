#!/usr/bin/env python3
"""ProofGrid v1.0.1 canonical environmental source identity.

This is the v1.0 normalizer with its admission dependency replaced by the
v0.9.1 exact-stack consumer. The canonical metadata semantics remain unchanged;
the trust boundary is stronger for the v1.2 route.
"""
from __future__ import annotations
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from reference import environmental_admission_v091 as hardened  # noqa: E402
from reference import environmental_source_identity as base  # noqa: E402

# Replace the module-level dependency used by every receipt/source check.
base.admission=hardened
base.PROCESS_NS=hardened.PROCESS_NS
base.EPD_2019_NS=hardened.EPD_2019_NS
base.ENGINE_VERSION="1.0.1"

CanonicalizationError=base.CanonicalizationError
canonical_json_bytes=base.canonical_json_bytes
sha256_bytes=base.sha256_bytes
sha256_file=base.sha256_file
load_json=base.load_json
validate_schema=base.validate_schema
verify_receipt_chain=base.verify_receipt_chain
extract_process_identity=base.extract_process_identity
source_identity=base.source_identity
build_record=base.build_record
build_receipt=base.build_receipt
normalize=base.normalize


def main(argv=None):
    return base.main(argv)


if __name__=="__main__":
    raise SystemExit(main())
