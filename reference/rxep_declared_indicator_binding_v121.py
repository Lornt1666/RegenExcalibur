#!/usr/bin/env python3
"""ProofGrid v1.2.1 hardened RXEP v0.2 exact-decimal binder.

This wrapper reuses the proven v1.2 binder/schema logic while requiring the
superseding v1.1.1 declared-indicator extraction receipt. Historical v1.1.0
parent receipts are rejected even if otherwise internally consistent.

Every envelope remains a CLAIMED, unsigned, non-calculated statement about what
the exact admitted source declares. No scientific/professional/regulatory or
certification state is added.
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declared_environmental_indicators_v111 as declared_hardened  # noqa: E402
from reference import rxep_declared_indicator_binding as base  # noqa: E402

ENGINE_NAME = base.ENGINE_NAME
ENGINE_VERSION = "1.2.1"
PARENT_EXTRACTION_VERSION = "1.1.1"
PROTOCOL_VERSION = base.PROTOCOL_VERSION
VERDICT = base.VERDICT
REVIEW_STATE = base.REVIEW_STATE
CANONICALIZATION = base.CANONICALIZATION
ZERO_DIGEST = base.ZERO_DIGEST
BindingError = base.BindingError

canonical_json_bytes = base.canonical_json_bytes
sha256_bytes = base.sha256_bytes
sha256_file = base.sha256_file
load_json_bytes = base.load_json_bytes
validate_envelope = base.validate_envelope
validate_bundle = base.validate_bundle

_original_verify_receipt_integrity = base.verify_receipt_integrity
_original_build_envelope = base.build_envelope

# Rebind Decimal/schema semantics to the hardened v1.1.1 extraction layer.
base.declared = declared_hardened
base.ENGINE_VERSION = ENGINE_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BindingError(message)


def verify_receipt_integrity(receipt: dict[str, Any]) -> None:
    _original_verify_receipt_integrity(receipt)
    engine = receipt.get("engine")
    require(isinstance(engine, dict), "parent extraction receipt engine identity missing")
    require(
        engine.get("version") == PARENT_EXTRACTION_VERSION,
        f"v1.2.1 requires hardened parent extraction engine {PARENT_EXTRACTION_VERSION}; got {engine.get('version')!r}",
    )


def build_envelope(record: dict[str, Any], receipt: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    envelope = _original_build_envelope(record, receipt, row)
    envelope = copy.deepcopy(envelope)
    envelope["methodology"]["version"] = PARENT_EXTRACTION_VERSION
    envelope["software"] = {"name": ENGINE_NAME, "version": ENGINE_VERSION}
    envelope["integrity"]["content_sha256"] = ZERO_DIGEST
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(envelope))
    validate_envelope(envelope)
    return envelope


# Make all inherited parent/bundle/CLI paths use the hardened checks.
base.verify_receipt_integrity = verify_receipt_integrity
base.build_envelope = build_envelope


def bind(
    extraction_record_path: Path,
    *,
    extraction_receipt_path: Path,
    output_dir: Path,
    requested_review_state: str = REVIEW_STATE,
):
    return base.bind(
        extraction_record_path,
        extraction_receipt_path=extraction_receipt_path,
        output_dir=output_dir,
        requested_review_state=requested_review_state,
    )


def main(argv: list[str] | None = None) -> int:
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
