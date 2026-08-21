#!/usr/bin/env python3
"""ProofGrid v1.0.1 canonical source identity bound to hardened v0.9.1 admission.

The v1.0 artifact audit found that the historical v0.9 admission consumer did
not independently enforce the full v1.2 validator/profile fingerprint. This
wrapper deliberately reuses the already-tested v1.0 metadata canonicalizer but
rebinds its admission dependency to v0.9.1 before any receipt-chain validation.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission_v091 as hardened_admission  # noqa: E402
from reference import environmental_source_identity as base  # noqa: E402

# Patch only the dependency/version globals used by the v1.0 implementation.
# All parsing, schema, identity extraction and deterministic serialization code
# remains the previously tested v1.0 implementation.
base.admission = hardened_admission
base.ENGINE_VERSION = "1.0.1"

CanonicalizationError = base.CanonicalizationError
ENGINE_NAME = base.ENGINE_NAME
ENGINE_VERSION = base.ENGINE_VERSION
VERDICT = base.VERDICT
SCHEMA_PATH = base.SCHEMA_PATH
COMMON_NS = base.COMMON_NS
PROCESS_NS = base.PROCESS_NS
EPD_2019_NS = base.EPD_2019_NS
XML_NS = base.XML_NS
CANONICALIZATION = base.CANONICALIZATION
ZERO_DIGEST = base.ZERO_DIGEST

canonical_json_bytes = base.canonical_json_bytes
sha256_bytes = base.sha256_bytes
sha256_file = base.sha256_file
load_json = base.load_json
validate_schema = base.validate_schema
require = base.require
verify_receipt_chain = base.verify_receipt_chain
extract_process_identity = base.extract_process_identity
source_identity = base.source_identity
build_record = base.build_record
build_receipt = base.build_receipt
normalize = base.normalize


def main(argv: list[str] | None = None) -> int:
    # base.main reads the module-global admission and ENGINE_VERSION values that
    # were rebound above, so the CLI is hardened as well as the Python API.
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
