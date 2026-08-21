#!/usr/bin/env python3
"""ProofGrid v1.2.1 hardening wrapper for frozen RXEP v0.2 exact-decimal binding.

RXEP v0.2 is intentionally preserved byte-for-byte: its envelope schema pins
the core extraction methodology version to 1.1.0 and binder software version to
1.2.0. Those values remain truthful because v1.1.1 reuses the historical
extraction algorithm bytes and adds only a stronger parent trust boundary.

This wrapper therefore does not rewrite RXEP v0.2 protocol fields. Instead it:
1. requires the parent extraction receipt engine to be exactly 1.1.1;
2. delegates to the frozen v1.2.0 RXEP v0.2 binder/schema;
3. emits a separate v1.2.1 hardening receipt binding the hardened parent receipt
   to the exact RXEP v0.2 bundle and binding receipt.

No receipt emitted here is scientific validation, professional review,
regulatory approval, source-rights expansion, or certification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declared_environmental_indicators_v111 as declared_hardened  # noqa: E402
from reference import rxep_declared_indicator_binding as base  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Hardened RXEP Parent Binder"
ENGINE_VERSION = "1.2.1"
PARENT_EXTRACTION_VERSION = "1.1.1"
PROTOCOL_BINDER_VERSION = "1.2.0"
PROTOCOL_METHODOLOGY_VERSION = "1.1.0"
PROTOCOL_VERSION = base.PROTOCOL_VERSION
VERDICT = base.VERDICT
HARDENED_VERDICT = "RXEP_DECLARED_INDICATOR_HARDENED_PARENT_BOUND_VERIFIABLE"
REVIEW_STATE = base.REVIEW_STATE
BindingError = base.BindingError

canonical_json_bytes = base.canonical_json_bytes
sha256_bytes = base.sha256_bytes
load_json_bytes = base.load_json_bytes

_original_verify_receipt_integrity = base.verify_receipt_integrity

# Parent record/Decimal validation uses the hardened v1.1.1 compatibility layer,
# while frozen RXEP v0.2 protocol output remains versioned 1.2.0 / methodology 1.1.0.
base.declared = declared_hardened


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


# All inherited parent-material paths now require the hardened extraction receipt.
base.verify_receipt_integrity = verify_receipt_integrity


def build_hardening_receipt(
    extraction_receipt: dict[str, Any],
    bundle: dict[str, Any],
    protocol_receipt: dict[str, Any],
) -> dict[str, Any]:
    require(protocol_receipt.get("engine", {}).get("version") == PROTOCOL_BINDER_VERSION, "frozen RXEP v0.2 binder version changed")
    require(bundle.get("protocol_version") == PROTOCOL_VERSION, "unexpected RXEP protocol version")
    require(bundle.get("review_state") == "CLAIMED", "RXEP v0.2 review state must remain CLAIMED")
    require(bundle.get("signed") is False and bundle.get("certified") is False, "RXEP v0.2 bundle must remain unsigned and non-certified")
    require(
        all(env.get("methodology", {}).get("version") == PROTOCOL_METHODOLOGY_VERSION for env in bundle.get("envelopes", [])),
        "frozen RXEP v0.2 core methodology version changed",
    )
    require(
        all(env.get("software", {}).get("version") == PROTOCOL_BINDER_VERSION for env in bundle.get("envelopes", [])),
        "frozen RXEP v0.2 envelope binder version changed",
    )

    receipt: dict[str, Any] = {
        "verdict": HARDENED_VERDICT,
        "certified": False,
        "signed": False,
        "review_state": "CLAIMED",
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "parent_extraction": {
            "engine_version": extraction_receipt["engine"]["version"],
            "receipt_sha256": extraction_receipt["receipt_sha256"],
            "record_content_sha256": extraction_receipt["record_content_sha256"],
            "record_file_sha256": extraction_receipt["record_file_sha256"],
        },
        "rxep_v02": {
            "protocol_version": PROTOCOL_VERSION,
            "binder_version": protocol_receipt["engine"]["version"],
            "core_extraction_methodology_version": PROTOCOL_METHODOLOGY_VERSION,
            "bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "binding_receipt_sha256": protocol_receipt["receipt_sha256"],
            "envelope_count": bundle["envelope_count"],
        },
        "evidence_dimensions": {
            "hardened_parent_version": "VERIFIED_1_1_1",
            "rxep_v02_protocol_preserved": True,
            "source_declared_values_only": True,
            "scientific_validity": "NOT_EVALUATED",
            "professional_review": "NOT_EVALUATED",
            "certification": "NOT_EVALUATED",
        },
        "limitations": [
            "The RXEP v0.2 bundle is intentionally not rewritten: methodology 1.1.0 denotes the unchanged extraction algorithm and binder 1.2.0 denotes the frozen protocol binder.",
            "This v1.2.1 receipt separately proves that the frozen RXEP v0.2 evidence was produced from a hardened v1.1.1 extraction receipt.",
            "The evidence remains a CLAIMED statement of document content only; no scientific validity, professional review, regulatory applicability, source-rights expansion, or certification is established.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def bind(
    extraction_record_path: Path,
    *,
    extraction_receipt_path: Path,
    output_dir: Path,
    requested_review_state: str = REVIEW_STATE,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    extraction_receipt, _ = load_json_bytes(extraction_receipt_path)
    verify_receipt_integrity(extraction_receipt)
    bundle, protocol_receipt = base.bind(
        extraction_record_path,
        extraction_receipt_path=extraction_receipt_path,
        output_dir=output_dir,
        requested_review_state=requested_review_state,
    )
    hardening_receipt = build_hardening_receipt(extraction_receipt, bundle, protocol_receipt)
    path = output_dir.resolve() / "v121-hardening-receipt.json"
    path.write_bytes((json.dumps(hardening_receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return bundle, protocol_receipt, hardening_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.2.1 hardened parent wrapper for RXEP v0.2 exact-decimal binding")
    parser.add_argument("--extraction-record", type=Path, required=True)
    parser.add_argument("--extraction-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--review-state", default=REVIEW_STATE)
    args = parser.parse_args(argv)
    try:
        bundle, protocol_receipt, hardening_receipt = bind(
            args.extraction_record,
            extraction_receipt_path=args.extraction_receipt,
            output_dir=args.output_dir,
            requested_review_state=args.review_state,
        )
    except (BindingError, declared_hardened.ExtractionError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {hardening_receipt['verdict']}")
    print(f"RXEP PROTOCOL: v{bundle['protocol_version']} (preserved)")
    print(f"RXEP BINDER: {protocol_receipt['engine']['version']} (preserved)")
    print(f"HARDENING ENGINE: {ENGINE_VERSION}")
    print(f"PARENT EXTRACTION: {PARENT_EXTRACTION_VERSION}")
    print(f"ENVELOPES: {bundle['envelope_count']}")
    print("REVIEW STATE: CLAIMED")
    print("SIGNED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
