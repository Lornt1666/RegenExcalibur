#!/usr/bin/env python3
"""ProofGrid v0.9.1 hardened environmental admission.

This module preserves v0.9.0 receipts as historical evidence while adding a
strict consumer that will not accept a v1.2 compatibility receipt unless the
entire accepted validator/profile stack fingerprint is present and exact.

No receipt emitted here is certification, scientific validation, professional
LCA review, provider authorization, programme-operator approval, or BBSR
plausibility approval.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission as v09  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Declaration Admission Hardened"
ENGINE_VERSION = "0.9.1"
VERDICT = "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE"

EXPECTED_VALIDATOR = {
    "coordinate": "com.okworx.ilcd.validation:ilcd-validation:2.12.2",
    "jar_sha256": "55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b",
    "pom_sha256": "16430562fe6ebb6da3e4afea4a8c6cce98d822d61f59eb33e0b5dc98a4eb1fc1",
}
EXPECTED_PROFILE = {
    "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
    "jar_sha256": "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
    "pom_sha256": "0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a",
    "generic_include_sha256": "31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25",
    "en15804_include_sha256": "a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147",
}
STACK_FINGERPRINT = {"validator": EXPECTED_VALIDATOR, "profile": EXPECTED_PROFILE}
STACK_FINGERPRINT_SHA256 = v09.sha256_bytes(v09.canonical_json_bytes(STACK_FINGERPRINT))


class HardenedAdmissionError(v09.AdmissionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HardenedAdmissionError(message)


def verify_v12_stack(conformance: dict[str, Any]) -> dict[str, Any]:
    v09.verify_canonical_receipt(conformance, "v1.2 conformance")
    validator = conformance.get("official_validator")
    profile = conformance.get("official_profile")
    require(validator == EXPECTED_VALIDATOR, "v1.2 conformance validator fingerprint mismatch or missing")
    require(profile == EXPECTED_PROFILE, "v1.2 conformance profile fingerprint mismatch or missing")
    supplied = conformance.get("official_stack_fingerprint_sha256")
    require(supplied == STACK_FINGERPRINT_SHA256, "v1.2 official stack fingerprint digest mismatch or missing")
    return {
        "validator": copy.deepcopy(EXPECTED_VALIDATOR),
        "profile": copy.deepcopy(EXPECTED_PROFILE),
        "fingerprint_sha256": STACK_FINGERPRINT_SHA256,
    }


def finalize(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    route = preflight_receipt.get("routing", {}).get("route")
    stack = None
    if route == v09.V12_ROUTE:
        stack = verify_v12_stack(conformance)

    base = v09.finalize(preflight_receipt, conformance)
    receipt = copy.deepcopy(base)
    receipt["engine"] = {"name": ENGINE_NAME, "version": ENGINE_VERSION}
    receipt["parent_engine"] = {"name": v09.ENGINE_NAME, "version": v09.ENGINE_VERSION}
    if stack is not None:
        receipt["conformance"]["official_stack"] = stack
        receipt["evidence_dimensions"]["validator_profile_stack_identity"] = "VERIFIED_EXACT"
    else:
        receipt["evidence_dimensions"]["validator_profile_stack_identity"] = "NOT_APPLICABLE_TO_V13_ROUTE"
    receipt["limitations"] = list(receipt["limitations"]) + [
        "v0.9.1 additionally verifies exact v1.2 validator/profile artifact identities before admission; it does not make those artifacts scientific or regulatory authority."
    ]
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = v09.sha256_bytes(v09.canonical_json_bytes(receipt))
    return receipt


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v0.9.1 hardened environmental admission")
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--conformance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = finalize(v09.load_json(args.preflight), v09.load_json(args.conformance))
        write_receipt(args.output, receipt)
    except v09.AdmissionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {receipt['verdict']}")
    print(f"ENGINE VERSION: {ENGINE_VERSION}")
    print(f"NORMALIZATION PERMITTED: {receipt['normalization_permitted']}")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
