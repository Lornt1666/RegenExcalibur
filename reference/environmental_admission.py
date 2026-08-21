#!/usr/bin/env python3
"""ProofGrid v0.9 evidence-gated environmental declaration admission pipeline.

The state machine deliberately separates source authority, source integrity,
format detection/version routing, format/profile conformance, and downstream
normalization permission. A parseable document is never sufficient for
admission.

v1.2 route:
    authority -> integrity -> deterministic v1.2 detection -> exact bounded
    v0.8 ÖKOBAUDAT 3.8.0 receipt -> admission

v1.3 route:
    authority -> integrity -> deterministic v1.3 detection -> exact bounded
    v0.7 XSD/master-data receipt (profile not performed) -> admission

No state produced here is a certification, scientific validation, professional
LCA review, programme-operator approval, BBSR plausibility approval, code
approval, engineering/architectural approval, or provider-rights expansion.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import source_import  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Environmental Declaration Admission"
ENGINE_VERSION = "0.9.0"
ROUTER_NAME = "proofgrid-ilcd-epd-admission-router"
ROUTER_VERSION = "0.9.0"
ROUTER_PROFILE = "auto-v1.2-v1.3"
FORMAT_NAME = "ILCD+EPD"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
PROCESS_NS = "http://lca.jrc.it/ILCD/Process"

V12_ROUTE = "OEKOBAUDAT_V12_PROFILE_3_8_0"
V13_ROUTE = "INDATA_V13_XSD_MASTERDATA_ONLY"
V12_CLAIM = "OEKOBAUDAT_V12_PROFILE_380_SYNTHETIC_AUTHORITY_SAFE_COMPATIBLE"
V13_VERDICT = "ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT"

MAX_ZIP_FILES = 2000
MAX_ZIP_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 512 * 1024 * 1024


class AdmissionError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AdmissionError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AdmissionError(f"invalid JSON in {path}: {exc}") from exc


def verify_canonical_receipt(receipt: dict[str, Any], label: str) -> str:
    claimed = receipt.get("receipt_sha256")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise AdmissionError(f"{label} is missing a canonical receipt_sha256")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    actual = sha256_bytes(canonical_json_bytes(body))
    if actual != claimed:
        raise AdmissionError(f"{label} receipt digest mismatch: expected {claimed}, got {actual}")
    return actual


def safe_zip_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise AdmissionError(f"unsafe ZIP member path: {name}")
    return path


def safe_xml_root(raw: bytes, label: str) -> ET.Element:
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise AdmissionError(f"DTD/entity declarations are not accepted in {label}")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdmissionError(f"invalid XML in {label}: {exc}") from exc


def process_version(raw: bytes, label: str) -> str:
    root = safe_xml_root(raw, label)
    if root.tag != f"{{{PROCESS_NS}}}processDataSet":
        raise AdmissionError(f"{label} is not an ILCD processDataSet")
    version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
    if not version:
        raise AdmissionError(f"{label} lacks deterministic epd-version metadata")
    return version


def zip_content_manifest(zf: zipfile.ZipFile) -> tuple[str, list[dict[str, Any]], list[str]]:
    infos = [info for info in zf.infolist() if not info.is_dir()]
    if not infos:
        raise AdmissionError("ZIP source is empty")
    if len(infos) > MAX_ZIP_FILES:
        raise AdmissionError(f"ZIP source exceeds file-count limit {MAX_ZIP_FILES}")
    total = 0
    rows: list[dict[str, Any]] = []
    process_versions: list[str] = []
    seen: set[str] = set()
    for info in infos:
        path = safe_zip_name(info.filename)
        name = path.as_posix()
        if name in seen:
            raise AdmissionError(f"duplicate ZIP member path: {name}")
        seen.add(name)
        if info.file_size > MAX_ZIP_MEMBER_BYTES:
            raise AdmissionError(f"ZIP member exceeds size limit: {name}")
        total += info.file_size
        if total > MAX_ZIP_TOTAL_BYTES:
            raise AdmissionError("ZIP source exceeds total uncompressed-size limit")
        raw = zf.read(info)
        digest = sha256_bytes(raw)
        rows.append({"path": name, "sha256": digest, "size": len(raw)})
        if name.startswith("ILCD/processes/") and name.lower().endswith(".xml"):
            process_versions.append(process_version(raw, name))
    if not process_versions:
        raise AdmissionError("ZIP source contains no ILCD/processes/*.xml process dataset")
    unique_versions = sorted(set(process_versions))
    if len(unique_versions) != 1:
        raise AdmissionError(f"ambiguous ILCD+EPD versions in ZIP source: {unique_versions}")

    # v0.8 package manifests are SHA-256 over deterministic sha256sum-style
    # lines for the ILCD tree. Reproduce that identity exactly for receipt binding.
    ilcd_rows = [row for row in sorted(rows, key=lambda row: row["path"]) if row["path"].startswith("ILCD/")]
    if not ilcd_rows:
        raise AdmissionError("ZIP source contains no ILCD tree")
    text = "".join(f"{row['sha256']}  {row['path']}\n" for row in ilcd_rows).encode("utf-8")
    return sha256_bytes(text), rows, unique_versions


def detect_source(source_path: Path, media_type: str) -> dict[str, Any]:
    raw_sha = sha256_file(source_path)
    if media_type in {"application/zip", "application/x-zip-compressed"} or zipfile.is_zipfile(source_path):
        try:
            with zipfile.ZipFile(source_path, "r") as zf:
                manifest_sha, rows, versions = zip_content_manifest(zf)
        except zipfile.BadZipFile as exc:
            raise AdmissionError(f"invalid ZIP source: {source_path}") from exc
        return {
            "container": "ZIP",
            "source_sha256": raw_sha,
            "package_manifest_sha256": manifest_sha,
            "file_count": len(rows),
            "detected_version": versions[0],
            "detection_basis": "epd2:epd-version on every ILCD/processes/*.xml processDataSet",
        }

    if media_type in {"application/xml", "text/xml"} or source_path.suffix.lower() == ".xml":
        raw = source_path.read_bytes()
        version = process_version(raw, source_path.name)
        return {
            "container": "XML",
            "source_sha256": raw_sha,
            "package_manifest_sha256": None,
            "file_count": 1,
            "detected_version": version,
            "detection_basis": "epd2:epd-version on ILCD Process/processDataSet root",
        }
    raise AdmissionError(f"unsupported source media type/container: {media_type}")


def route_for(version: str) -> dict[str, Any]:
    if version == "1.2":
        return {
            "route": V12_ROUTE,
            "required_evidence": "exact official ÖKOBAUDAT profile 3.8.0 compatibility receipt",
            "profile_validation_applicable": True,
            "profile_validation_required": True,
        }
    if version == "1.3":
        return {
            "route": V13_ROUTE,
            "required_evidence": "authoritative InData v1.3 XSD/master-data conformance receipt",
            "profile_validation_applicable": False,
            "profile_validation_required": False,
        }
    raise AdmissionError(f"unsupported ILCD+EPD version: {version}")


def preflight(package_dir: Path, *, as_of: date) -> dict[str, Any]:
    package_dir = Path(package_dir).resolve()
    manifest_path = package_dir / "import-manifest.json"
    manifest = load_json(manifest_path)
    try:
        source_import.validate_schema(manifest, source_import.MANIFEST_SCHEMA, "source import manifest")
    except source_import.SourceImportError as exc:
        raise AdmissionError(str(exc)) from exc

    parser = manifest["parser"]
    expected_parser = {"name": ROUTER_NAME, "version": ROUTER_VERSION, "profile": ROUTER_PROFILE}
    if parser != expected_parser:
        raise AdmissionError(f"unsupported admission router declaration: {parser}")

    try:
        rights = source_import.rights_decision(manifest, as_of=as_of, export_source=False)
        terms_path = source_import.safe_package_file(package_dir, manifest["authorization"]["terms_snapshot"]["path"])
        source_path = source_import.safe_package_file(package_dir, manifest["source"]["path"])
    except source_import.SourceImportError as exc:
        raise AdmissionError(str(exc)) from exc

    terms_actual = sha256_file(terms_path)
    terms_expected = manifest["authorization"]["terms_snapshot"]["sha256"]
    if terms_actual != terms_expected:
        raise AdmissionError(f"terms snapshot hash mismatch: expected {terms_expected}, got {terms_actual}")
    source_actual = sha256_file(source_path)
    source_expected = manifest["source"]["sha256"]
    if source_actual != source_expected:
        raise AdmissionError(f"source-content hash mismatch: expected {source_expected}, got {source_actual}")

    detected = detect_source(source_path, manifest["source"]["media_type"])
    if detected["source_sha256"] != source_actual:
        raise AdmissionError("internal source-integrity binding mismatch")

    declared = manifest["source"]["declared_format"]
    if declared.get("name") != FORMAT_NAME:
        raise AdmissionError(f"unsupported declared source format name: {declared.get('name')}")
    if declared.get("version") != detected["detected_version"]:
        raise AdmissionError(
            f"declared/detected version mismatch: declared {declared.get('version')}, detected {detected['detected_version']}"
        )
    route = route_for(detected["detected_version"])

    receipt: dict[str, Any] = {
        "verdict": "ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE",
        "state": "AWAITING_CONFORMANCE",
        "certified": False,
        "normalization_permitted": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "import_id": manifest["import_id"],
        "rights": rights,
        "manifest": {
            "version": manifest["manifest_version"],
            "file_sha256": sha256_file(manifest_path),
            "content_sha256": sha256_bytes(canonical_json_bytes(manifest)),
        },
        "terms": {
            "reference": manifest["authorization"]["terms_reference"],
            "sha256": terms_actual,
            "approval_reference": manifest["authorization"].get("approval_reference"),
            "valid_until": manifest["authorization"].get("valid_until"),
        },
        "source": {
            "path": manifest["source"]["path"],
            "media_type": manifest["source"]["media_type"],
            "declared_format": declared,
            **detected,
        },
        "routing": route,
        "evidence_dimensions": {
            "source_authority": "VERIFIED_FOR_DECLARED_TEST_IMPORT",
            "source_integrity": "VERIFIED",
            "format_version": "DETECTED_AND_MATCHED_TO_DECLARATION",
            "conformance": "PENDING",
            "scientific_validity": "NOT_EVALUATED",
            "professional_review": "NOT_EVALUATED",
            "certification": "NOT_EVALUATED",
        },
        "limitations": [
            "Preflight proves only declared source authority/integrity and deterministic version routing; it is not admission or normalization permission.",
            "No format/profile conformance result is accepted until a separately integrity-checked receipt is bound to these exact source bytes/content identity.",
            "Source authority does not establish scientific validity, product representativeness, professional LCA suitability, code/engineering/architectural approval, procurement/regulatory approval, or certification.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def validate_v12_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    verify_canonical_receipt(conformance, "v1.2 conformance")
    if conformance.get("claim_token") != V12_CLAIM:
        raise AdmissionError(f"wrong v1.2 conformance claim token: {conformance.get('claim_token')}")
    if conformance.get("compatibility_claim") is not True:
        raise AdmissionError("v1.2 conformance receipt does not assert bounded compatibility")
    if conformance.get("certified") is not False:
        raise AdmissionError("v1.2 conformance receipt must remain certified=false")
    if conformance.get("authority_inference_allowed") is not False:
        raise AdmissionError("v1.2 conformance receipt permits an authority inference")
    positive = conformance.get("positive_control", {})
    if positive.get("error_count") != 0 or positive.get("is_positive") is not True:
        raise AdmissionError("v1.2 official-profile conformance is not positive with zero errors")
    expected_manifest = preflight_receipt["source"].get("package_manifest_sha256")
    if not expected_manifest or conformance.get("package_manifest_sha256") != expected_manifest:
        raise AdmissionError("v1.2 conformance receipt is not bound to the admitted package manifest")
    return {
        "receipt_sha256": conformance["receipt_sha256"],
        "claim_token": V12_CLAIM,
        "official_profile": conformance.get("official_profile"),
        "profile_validation_performed": True,
        "profile_positive": True,
        "error_count": 0,
        "warning_count": positive.get("warning_count"),
    }


def validate_v13_conformance(preflight_receipt: dict[str, Any], conformance: dict[str, Any]) -> dict[str, Any]:
    verify_canonical_receipt(conformance, "v1.3 conformance")
    if conformance.get("verdict") != V13_VERDICT:
        raise AdmissionError(f"wrong v1.3 conformance verdict: {conformance.get('verdict')}")
    if conformance.get("certified") is not False:
        raise AdmissionError("v1.3 conformance receipt must remain certified=false")
    fmt = conformance.get("format_conformance", {})
    if fmt.get("xsd_validation") is not True or fmt.get("master_data_identity_validation") is not True:
        raise AdmissionError("v1.3 XSD/master-data conformance is incomplete")
    if fmt.get("profile_validation_performed") is not False:
        raise AdmissionError("v1.3 route must not silently perform/relabel the v1.2 profile")
    synthetic = conformance.get("synthetic_fixture", {})
    if synthetic.get("sha256") != preflight_receipt["source"]["source_sha256"]:
        raise AdmissionError("v1.3 conformance receipt is not bound to the admitted XML source bytes")
    identity = synthetic.get("identity", {})
    if identity.get("epd_version") != "1.3":
        raise AdmissionError("v1.3 conformance synthetic identity does not declare epd-version 1.3")
    return {
        "receipt_sha256": conformance["receipt_sha256"],
        "verdict": V13_VERDICT,
        "profile_validation_performed": False,
        "profile_status": fmt.get("profile_status"),
        "xsd_validation": True,
        "master_data_identity_validation": True,
    }


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
        "verdict": "ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE",
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
    parser = argparse.ArgumentParser(description="ProofGrid v0.9 environmental declaration admission")
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
