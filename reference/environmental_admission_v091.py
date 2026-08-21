#!/usr/bin/env python3
"""ProofGrid v0.9.1 exact-stack environmental admission hardening.

This module composes the accepted v0.9 preflight/version-routing logic with a
strict consumer policy for ILCD+EPD v1.2 conformance receipts. A self-consistent
receipt is insufficient: it must also carry the exact validator/profile
fingerprint that was accepted by the v0.8 authority-safe profile gate.

v0.9 remains a historical evidence receipt. v0.9.1 is the stricter downstream
consumer contract used by subsequent ProofGrid gates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission as base  # noqa: E402
from reference import source_import  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Declaration Admission"
ENGINE_VERSION = "0.9.1"
VERDICT = "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE"

# Re-export the stable v0.9 protocol/detection surfaces for downstream modules.
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
preflight = base.preflight

V12_OFFICIAL_VALIDATOR = {
    "coordinate": "com.okworx.ilcd.validation:ilcd-validation:2.12.2",
    "jar_sha256": "55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b",
    "pom_sha256": "16430562fe6ebb6da3e4afea4a8c6cce98d822d61f59eb33e0b5dc98a4eb1fc1",
}
V12_OFFICIAL_PROFILE = {
    "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
    "jar_sha256": "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
    "pom_sha256": "0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a",
    "generic_include_sha256": "31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25",
    "en15804_include_sha256": "a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147",
}


def validate_v12_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    """Reject any v1.2 receipt that does not pin the complete accepted stack."""
    verify_canonical_receipt(conformance, "v1.2 conformance")
    if conformance.get("claim_token") != V12_CLAIM:
        raise AdmissionError(f"wrong v1.2 conformance claim token: {conformance.get('claim_token')}")
    if conformance.get("compatibility_claim") is not True:
        raise AdmissionError("v1.2 conformance receipt does not assert bounded compatibility")
    if conformance.get("certified") is not False:
        raise AdmissionError("v1.2 conformance receipt must remain certified=false")
    if conformance.get("authority_inference_allowed") is not False:
        raise AdmissionError("v1.2 conformance receipt permits an authority inference")

    validator = conformance.get("official_validator")
    if validator != V12_OFFICIAL_VALIDATOR:
        raise AdmissionError("v1.2 conformance receipt does not match the exact accepted official validator stack")
    profile = conformance.get("official_profile")
    if profile != V12_OFFICIAL_PROFILE:
        raise AdmissionError("v1.2 conformance receipt does not match the exact accepted ÖKOBAUDAT profile stack")

    positive = conformance.get("positive_control", {})
    if positive.get("error_count") != 0 or positive.get("is_positive") is not True:
        raise AdmissionError("v1.2 official-profile conformance is not positive with zero errors")
    expected_manifest = preflight_receipt["source"].get("package_manifest_sha256")
    if not expected_manifest or conformance.get("package_manifest_sha256") != expected_manifest:
        raise AdmissionError("v1.2 conformance receipt is not bound to the admitted package manifest")

    return {
        "receipt_sha256": conformance["receipt_sha256"],
        "claim_token": V12_CLAIM,
        "official_validator": validator,
        "official_profile": profile,
        "profile_validation_performed": True,
        "profile_positive": True,
        "error_count": 0,
        "warning_count": positive.get("warning_count"),
    }


def validate_v13_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    return base.validate_v13_conformance(preflight_receipt, conformance)


def finalize(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    """Finalize admission only after the route-specific hardened consumer passes."""
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
            "For the v1.2 route, v0.9.1 additionally requires the complete accepted validator/profile fingerprint; a self-consistent but forged stack receipt is rejected.",
            "Admission does not expand third-party rights and does not authorize redistribution unless the independent rights manifest says so.",
            "Admission does not establish scientific validity, real-product representativeness, professional LCA suitability, programme-operator approval, BBSR plausibility approval, code/engineering/architectural approval, procurement/regulatory approval, or certification.",
            "AUTHORIZED, FORMAT_CONFORMANT, PROFILE_COMPATIBLE, SCIENTIFICALLY_VALID, PROFESSIONALLY_REVIEWED, and CERTIFIED remain independent evidence states.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v0.9.1 exact-stack environmental declaration admission")
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
