#!/usr/bin/env python3
"""ProofGrid v0.9.1 hardened environmental-declaration admission consumer.

v0.9.1 preserves the v0.9 authority/integrity/version-routing semantics while
closing a receipt-consumption gap discovered during the v1.0 artifact audit:
a self-consistent v1.2 conformance receipt is not accepted unless it carries
and exactly matches the independently researched official validator/profile
fingerprint.

This module intentionally wraps rather than rewrites v0.9 so historical v0.9
receipts remain auditable as historical evidence. New downstream consumers
should use this module.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission as base  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Declaration Admission"
ENGINE_VERSION = "0.9.1"
VERDICT = "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE"

# Re-export stable v0.9 routing/parser constants and helpers used downstream.
ROUTER_NAME = base.ROUTER_NAME
ROUTER_VERSION = base.ROUTER_VERSION
ROUTER_PROFILE = base.ROUTER_PROFILE
FORMAT_NAME = base.FORMAT_NAME
EPD_2019_NS = base.EPD_2019_NS
PROCESS_NS = base.PROCESS_NS
V12_ROUTE = base.V12_ROUTE
V13_ROUTE = base.V13_ROUTE
V12_CLAIM = base.V12_CLAIM
V13_VERDICT = base.V13_VERDICT
AdmissionError = base.AdmissionError
canonical_json_bytes = base.canonical_json_bytes
sha256_bytes = base.sha256_bytes
sha256_file = base.sha256_file
load_json = base.load_json
verify_canonical_receipt = base.verify_canonical_receipt
safe_zip_name = base.safe_zip_name
safe_xml_root = base.safe_xml_root
process_version = base.process_version
zip_content_manifest = base.zip_content_manifest
detect_source = base.detect_source
route_for = base.route_for
write_receipt = base.write_receipt
source_import = base.source_import

EXPECTED_V12_STACK: dict[str, Any] = {
    "validator": {
        "coordinate": "com.okworx.ilcd.validation:ilcd-validation:2.12.2",
        "jar_sha256": "55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b",
        "pom_sha256": "16430562fe6ebb6da3e4afea4a8c6cce98d822d61f59eb33e0b5dc98a4eb1fc1",
    },
    "profile": {
        "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
        "jar_sha256": "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
        "pom_sha256": "0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a",
    },
    "included_profiles": {
        "EPD-1.2-Generic.jar": "31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25",
        "EPD-1.2-EN15804.jar": "a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147",
    },
}
EXPECTED_V12_STACK_SHA256 = sha256_bytes(canonical_json_bytes(EXPECTED_V12_STACK))
EXPECTED_LEGACY_PROFILE = {
    "coordinate": EXPECTED_V12_STACK["profile"]["coordinate"],
    "jar_sha256": EXPECTED_V12_STACK["profile"]["jar_sha256"],
}


def _require_exact_stack(conformance: dict[str, Any]) -> dict[str, Any]:
    actual = conformance.get("official_stack")
    if actual != EXPECTED_V12_STACK:
        if not isinstance(actual, dict):
            raise AdmissionError("v1.2 conformance receipt is missing official_stack exact fingerprint")
        for section, expected_section in EXPECTED_V12_STACK.items():
            actual_section = actual.get(section)
            if actual_section != expected_section:
                raise AdmissionError(f"v1.2 official stack mismatch in {section}: expected exact pinned fingerprint")
        raise AdmissionError("v1.2 official stack contains unexpected fields or values")

    if conformance.get("official_stack_sha256") != EXPECTED_V12_STACK_SHA256:
        raise AdmissionError("v1.2 official_stack_sha256 does not match the pinned stack fingerprint")

    # Keep the v0.9 compatibility field but require it to agree with the stronger
    # stack object so two conflicting profile identities cannot coexist.
    if conformance.get("official_profile") != EXPECTED_LEGACY_PROFILE:
        raise AdmissionError("v1.2 official_profile does not match the pinned official_stack profile")
    return copy.deepcopy(actual)


def preflight(package_dir: Path, *, as_of) -> dict[str, Any]:
    receipt = base.preflight(package_dir, as_of=as_of)
    receipt["engine"] = {"name": ENGINE_NAME, "version": ENGINE_VERSION}
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def validate_v12_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    # Preserve every original v0.9 bounded check first.
    binding = base.validate_v12_conformance(preflight_receipt, conformance)
    stack = _require_exact_stack(conformance)
    binding["official_stack"] = stack
    binding["official_stack_sha256"] = EXPECTED_V12_STACK_SHA256
    binding["official_profile"] = copy.deepcopy(EXPECTED_LEGACY_PROFILE)
    return binding


def validate_v13_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    return base.validate_v13_conformance(preflight_receipt, conformance)


def finalize(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    verify_canonical_receipt(preflight_receipt, "admission preflight")
    if preflight_receipt.get("verdict") != "ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE":
        raise AdmissionError("wrong admission preflight verdict")
    if preflight_receipt.get("state") != "AWAITING_CONFORMANCE":
        raise AdmissionError("preflight is not awaiting conformance")
    if preflight_receipt.get("normalization_permitted") is not False:
        raise AdmissionError("preflight illegally permits normalization before conformance")
    if preflight_receipt.get("certified") is not False:
        raise AdmissionError("preflight must remain certified=false")
    if preflight_receipt.get("rights", {}).get("transformation") != "ALLOWED":
        raise AdmissionError("normalization cannot be admitted without explicit transformation permission")

    route = preflight_receipt["routing"]["route"]
    if route == V12_ROUTE:
        conformance_binding = validate_v12_conformance(preflight_receipt, conformance)
    elif route == V13_ROUTE:
        conformance_binding = validate_v13_conformance(preflight_receipt, conformance)
    else:
        raise AdmissionError(f"unsupported preflight route: {route}")

    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "state": "ADMITTED_FOR_NORMALIZATION",
        "admitted": True,
        "normalization_permitted": True,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "preflight_receipt_sha256": preflight_receipt["receipt_sha256"],
        "source": {
            "sha256": preflight_receipt["source"]["source_sha256"],
            "package_manifest_sha256": preflight_receipt["source"].get("package_manifest_sha256"),
            "detected_version": preflight_receipt["source"]["detected_version"],
            "container": preflight_receipt["source"]["container"],
        },
        "rights": {
            "decision": preflight_receipt["rights"]["decision"],
            "status": preflight_receipt["rights"]["status"],
            "transformation": preflight_receipt["rights"]["transformation"],
            "redistribution": preflight_receipt["rights"]["redistribution"],
        },
        "routing": preflight_receipt["routing"],
        "conformance": conformance_binding,
        "evidence_dimensions": {
            "source_authority": "VERIFIED_FOR_DECLARED_IMPORT",
            "source_integrity": "VERIFIED",
            "format_version": "VERIFIED",
            "format_or_profile_conformance": "VERIFIED_FOR_SELECTED_ROUTE",
            "normalization_permission": "GRANTED_FOR_THIS_EXACT_SOURCE_IDENTITY",
            "scientific_validity": "NOT_EVALUATED",
            "professional_review": "NOT_EVALUATED",
            "certification": "NOT_EVALUATED",
        },
        "limitations": [
            "Admission means only that source authority/integrity, deterministic version routing, and the applicable ProofGrid format/profile gate succeeded for this exact source identity.",
            "For the v1.2 route, the consumed conformance receipt must carry the exact pinned validator/profile JAR/POM/include fingerprint researched by ProofGrid v0.8.",
            "Admission does not expand third-party rights and does not authorize redistribution unless the independent rights manifest says so.",
            "Admission does not establish scientific validity, real-product representativeness, professional LCA suitability, programme-operator approval, BBSR plausibility approval, code/engineering/architectural approval, procurement/regulatory approval, or certification.",
            "AUTHORIZED, FORMAT_CONFORMANT, PROFILE_COMPATIBLE, SCIENTIFICALLY_VALID, PROFESSIONALLY_REVIEWED, and CERTIFIED remain independent evidence states.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v0.9.1 hardened environmental declaration admission")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("package_dir", type=Path)
    p_pre.add_argument("--output", type=Path, required=True)
    p_pre.add_argument("--as-of", type=str, default=None)

    p_fin = sub.add_parser("finalize")
    p_fin.add_argument("--preflight", type=Path, required=True)
    p_fin.add_argument("--conformance", type=Path, required=True)
    p_fin.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            as_of = source_import.parse_iso_date(args.as_of, "--as-of") if args.as_of else datetime.now(timezone.utc).date()
            receipt = preflight(args.package_dir, as_of=as_of)
        else:
            receipt = finalize(load_json(args.preflight), load_json(args.conformance))
        write_receipt(args.output, receipt)
    except (AdmissionError, source_import.SourceImportError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {receipt['verdict']}")
    print(f"STATE: {receipt['state']}")
    print(f"NORMALIZATION PERMITTED: {receipt['normalization_permitted']}")
    print("NOT CERTIFIED")
    print(f"Receipt: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
