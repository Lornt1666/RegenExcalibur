#!/usr/bin/env python3
"""ProofGrid v0.6 authorization-aware environmental source importer.

The importer binds an explicit rights/terms manifest to exact local source bytes,
a versioned parser profile, a normalized ProofGrid environmental source record,
and a machine-readable import receipt.

Public visibility alone is not treated as authorization. The initial parser accepts
only a RegenExcalibur synthetic XML carrier used for software conformance testing;
it does not claim ILCD+EPD compliance or provider-specific production support.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import rx_cli  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Authorized Source Importer"
ENGINE_VERSION = "0.6.0"
PARSER_NAME = "rx-synthetic-epd-carrier"
PARSER_VERSION = "0.6.0"
PARSER_PROFILE = "rx-synthetic-epd-carrier-1.0"
FORMAT_NAME = "RX-SYNTHETIC-EPD-CARRIER"
FORMAT_VERSION = "1.0"
XML_NAMESPACE = "urn:regenexcalibur:synthetic-epd-carrier:1.0"
MANIFEST_SCHEMA = ROOT / "schemas" / "source-import-manifest.schema.json"


class SourceImportError(ValueError):
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
        raise SourceImportError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceImportError(f"invalid JSON in {path}: {exc}") from exc


def _error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path)


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SourceImportError(f"invalid schema {schema_path}: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{_error_path(error)}: {error.message}" for error in errors[:5])
        if len(errors) > 5:
            preview += f"; +{len(errors) - 5} more"
        raise SourceImportError(f"{label} failed schema validation: {preview}")


def safe_package_file(package_dir: Path, relative: str) -> Path:
    root = package_dir.resolve()
    candidate = (package_dir / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SourceImportError(f"import reference escapes package directory: {relative}") from exc
    if not candidate.is_file():
        raise SourceImportError(f"import package file not found: {relative}")
    return candidate


def parse_iso_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SourceImportError(f"{label} must be an ISO date YYYY-MM-DD") from exc


def rights_decision(manifest: dict[str, Any], *, as_of: date, export_source: bool) -> dict[str, Any]:
    acquisition = manifest["acquisition"]
    rights = manifest["authorization"]
    status = rights["status"]

    if status in {"UNKNOWN", "PUBLIC_ACCESS_ONLY"}:
        raise SourceImportError(
            f"authorization status {status} does not authorize source import; public/basic visibility is not sufficient"
        )

    if status == "TEST_ONLY":
        if acquisition["synthetic"] is not True:
            raise SourceImportError("TEST_ONLY authorization is valid only for an explicitly synthetic source")
        if acquisition["method"] != "TEST_FIXTURE" or acquisition["intended_use"] != "INTERNAL_TEST":
            raise SourceImportError("TEST_ONLY authorization requires TEST_FIXTURE acquisition and INTERNAL_TEST use")

    if status == "EXPLICITLY_AUTHORIZED":
        approval = rights.get("approval_reference")
        if not isinstance(approval, str) or not approval.strip():
            raise SourceImportError("EXPLICITLY_AUTHORIZED import requires a non-empty approval_reference")

    valid_until = rights.get("valid_until")
    if valid_until is not None and as_of > parse_iso_date(valid_until, "authorization.valid_until"):
        raise SourceImportError(f"source authorization expired on {valid_until}; evaluated as of {as_of.isoformat()}")

    if rights["storage"] != "ALLOWED":
        raise SourceImportError("v0.6 local import requires explicit source storage permission")
    if rights["transformation"] != "ALLOWED":
        raise SourceImportError("v0.6 normalized import requires explicit transformation permission")
    if acquisition["intended_use"] == "COMMERCIAL_TOOL" and rights["commercial_use"] != "ALLOWED":
        raise SourceImportError("COMMERCIAL_TOOL use requires explicit commercial_use = ALLOWED")
    if export_source and rights["redistribution"] != "ALLOWED":
        raise SourceImportError("raw source export requested without explicit redistribution permission")

    return {
        "decision": "AUTHORIZED_FOR_DECLARED_IMPORT_ONLY",
        "evaluated_as_of": as_of.isoformat(),
        "status": status,
        "intended_use": acquisition["intended_use"],
        "commercial_use": rights["commercial_use"],
        "storage": rights["storage"],
        "transformation": rights["transformation"],
        "redistribution": rights["redistribution"],
        "raw_source_export_requested": export_source,
    }


def as_decimal(value: str, label: str) -> Decimal:
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise SourceImportError(f"{label} must be numeric") from exc
    if not number.is_finite():
        raise SourceImportError(f"{label} must be finite")
    return number


def _required_element(root: ET.Element, local_name: str) -> ET.Element:
    element = root.find(f"{{{XML_NAMESPACE}}}{local_name}")
    if element is None:
        raise SourceImportError(f"synthetic declaration missing required element: {local_name}")
    return element


def _required_attribute(element: ET.Element, name: str) -> str:
    if name not in element.attrib:
        raise SourceImportError(f"synthetic declaration element {element.tag} missing attribute {name}")
    return element.attrib[name]


def parse_synthetic_carrier(source_path: Path, manifest: dict[str, Any], redistribution_status: str) -> tuple[dict[str, Any], dict[str, Any]]:
    source = manifest["source"]
    parser = manifest["parser"]
    declared_format = source["declared_format"]
    if source["media_type"] != "application/xml":
        raise SourceImportError("v0.6 synthetic parser requires media_type application/xml")
    if declared_format != {"name": FORMAT_NAME, "version": FORMAT_VERSION}:
        raise SourceImportError(f"unsupported declared source format: {declared_format}")
    if parser != {"name": PARSER_NAME, "version": PARSER_VERSION, "profile": PARSER_PROFILE}:
        raise SourceImportError(f"unsupported parser/profile declaration: {parser}")

    raw = source_path.read_bytes()
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise SourceImportError("DTD/entity declarations are not accepted by the v0.6 synthetic XML parser")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SourceImportError(f"unable to parse synthetic environmental declaration XML: {exc}") from exc

    if root.tag != f"{{{XML_NAMESPACE}}}environmentalDeclaration":
        raise SourceImportError(f"unexpected synthetic declaration root element: {root.tag}")
    if root.attrib.get("format") != FORMAT_NAME or root.attrib.get("version") != FORMAT_VERSION:
        raise SourceImportError("synthetic declaration root format/version does not match supported parser profile")

    identity = _required_element(root, "identity")
    publisher = _required_element(root, "publisher")
    material = _required_element(root, "material")
    declared_unit = _required_element(root, "declaredUnit")
    indicator = _required_element(root, "indicator")
    boundary = _required_element(root, "systemBoundary")
    source_metadata = _required_element(root, "sourceMetadata")
    limitations_element = _required_element(root, "limitations")

    publisher_text = (publisher.text or "").strip()
    if publisher_text != manifest["provider"]["name"]:
        raise SourceImportError("source publisher does not exactly match import manifest provider name")

    modules = [
        (item.text or "").strip()
        for item in boundary.findall(f"{{{XML_NAMESPACE}}}module")
        if (item.text or "").strip()
    ]
    limitations = [
        (item.text or "").strip()
        for item in limitations_element.findall(f"{{{XML_NAMESPACE}}}item")
        if (item.text or "").strip()
    ]

    reference_quantity = as_decimal(_required_attribute(declared_unit, "referenceQuantity"), "declaredUnit.referenceQuantity")
    indicator_value = as_decimal(_required_attribute(indicator, "value"), "indicator.value")

    record: dict[str, Any] = {
        "id": manifest["normalized_record_id"],
        "material": {
            "id": _required_attribute(material, "id"),
            "name": _required_attribute(material, "name"),
        },
        "declared_unit": _required_attribute(declared_unit, "unit"),
        "reference_quantity": float(reference_quantity),
        "indicator": {
            "name": _required_attribute(indicator, "name"),
            "value": float(indicator_value),
            "unit": _required_attribute(indicator, "unit"),
        },
        "system_boundary": {"modules": modules},
        "source": {
            "publisher": publisher_text,
            "document_id": _required_attribute(identity, "documentId"),
            "version": _required_attribute(identity, "documentVersion"),
            "publication_date": _required_attribute(source_metadata, "publicationDate"),
            "geography": _required_attribute(source_metadata, "geography"),
            "verification": {
                "state": "UNVERIFIED",
                "evidence_reference": None,
            },
            "reference": manifest["source"]["path"],
            "source_uri": manifest["provider"]["source_locator"],
            "source_content_sha256": manifest["source"]["sha256"],
            "redistribution_status": redistribution_status,
        },
        "synthetic": bool(manifest["acquisition"]["synthetic"]),
        "limitations": limitations,
        "data_quality_flags": [
            "SYNTHETIC_TEST_DATA",
            "RIGHTS_MANIFEST_REQUIRED",
            "FORMAT_NOT_CLAIMED_ILCD_EPD_COMPLIANT",
        ],
    }
    parsed_identity = {
        "dataset_uuid": _required_attribute(identity, "datasetUuid"),
        "document_id": record["source"]["document_id"],
        "document_version": record["source"]["version"],
    }
    return record, parsed_identity


def import_package(
    package_dir: Path,
    *,
    output_dir: Path,
    as_of: date,
    export_source: bool = False,
) -> dict[str, Any]:
    package_dir = Path(package_dir)
    output_dir = Path(output_dir)
    manifest_path = package_dir / "import-manifest.json"
    manifest = load_json(manifest_path)
    validate_schema(manifest, MANIFEST_SCHEMA, "source import manifest")

    decision = rights_decision(manifest, as_of=as_of, export_source=export_source)
    terms_path = safe_package_file(package_dir, manifest["authorization"]["terms_snapshot"]["path"])
    terms_actual = sha256_file(terms_path)
    terms_expected = manifest["authorization"]["terms_snapshot"]["sha256"]
    if terms_actual != terms_expected:
        raise SourceImportError(f"terms snapshot hash mismatch: expected {terms_expected}, got {terms_actual}")

    source_path = safe_package_file(package_dir, manifest["source"]["path"])
    source_actual = sha256_file(source_path)
    source_expected = manifest["source"]["sha256"]
    if source_actual != source_expected:
        raise SourceImportError(f"source-content hash mismatch: expected {source_expected}, got {source_actual}")

    rights = manifest["authorization"]
    if manifest["acquisition"]["synthetic"] and rights["redistribution"] == "ALLOWED":
        redistribution_status = "SYNTHETIC_OPEN"
    elif rights["redistribution"] == "ALLOWED":
        redistribution_status = "REDISTRIBUTABLE"
    else:
        redistribution_status = "RESTRICTED"

    record, parsed_identity = parse_synthetic_carrier(source_path, manifest, redistribution_status)
    if record["id"] != manifest["normalized_record_id"]:
        raise SourceImportError("normalized record ID does not match import manifest")

    try:
        source_index, registry_summary = rx_cli.validate_lca_registry([record], package_dir)
    except rx_cli.VerificationError as exc:
        raise SourceImportError(f"normalized ProofGrid source record failed schema/provenance validation: {exc}") from exc
    normalized = source_index[record["id"]]

    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir / "normalized-registry.json"
    registry_bytes = (json.dumps([normalized], indent=2, sort_keys=True) + "\n").encode("utf-8")
    registry_path.write_bytes(registry_bytes)

    raw_export: dict[str, Any] = {
        "requested": export_source,
        "exported": False,
        "path": None,
        "sha256": None,
    }
    if export_source:
        raw_dir = output_dir / "raw-source"
        raw_dir.mkdir(parents=True, exist_ok=True)
        exported = raw_dir / source_path.name
        shutil.copyfile(source_path, exported)
        raw_export = {
            "requested": True,
            "exported": True,
            "path": exported.relative_to(output_dir).as_posix(),
            "sha256": sha256_file(exported),
        }

    receipt: dict[str, Any] = {
        "verdict": "AUTHORIZED_SOURCE_IMPORT_VERIFIABLE",
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "import_id": manifest["import_id"],
        "rights": decision,
        "manifest": {
            "version": manifest["manifest_version"],
            "file_sha256": sha256_file(manifest_path),
            "content_sha256": sha256_bytes(canonical_json_bytes(manifest)),
        },
        "terms": {
            "reference": rights["terms_reference"],
            "path": manifest["authorization"]["terms_snapshot"]["path"],
            "sha256": terms_actual,
            "approval_reference": rights.get("approval_reference"),
            "valid_until": rights.get("valid_until"),
        },
        "source": {
            "provider": manifest["provider"],
            "path": manifest["source"]["path"],
            "sha256": source_actual,
            "media_type": manifest["source"]["media_type"],
            "declared_format": manifest["source"]["declared_format"],
            "redistribution_status": redistribution_status,
            "raw_export": raw_export,
        },
        "parser": manifest["parser"],
        "parsed_identity": parsed_identity,
        "normalized_record": {
            "id": normalized["id"],
            "canonical_sha256": sha256_bytes(canonical_json_bytes(normalized)),
            "registry_file": registry_path.name,
            "registry_file_sha256": sha256_bytes(registry_bytes),
            "registry_records": registry_summary["records"],
            "verified_source_files": registry_summary["verified_source_files"],
        },
        "limitations": [
            "The initial v0.6 parser accepts only a RegenExcalibur synthetic XML carrier and does not claim ILCD+EPD or programme-operator profile conformance.",
            "Authorization evidence proves only the declared import/use permission state represented by the manifest and referenced terms snapshot; it does not expand third-party rights.",
            "Source/schema/provenance integrity does not establish scientific validity, product representativeness, or professional LCA suitability.",
            "No real provider API access, authentication bypass, scraping, or provider-data redistribution is performed by this synthetic conformance gate.",
            "This receipt is not an LCA, code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    receipt_path = output_dir / "import-receipt.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v0.6 authorization-aware environmental source importer")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--as-of", type=str, default=None, help="ISO policy-evaluation date; defaults to current UTC date")
    parser.add_argument("--export-source", action="store_true", help="Export raw source bytes only when redistribution is explicitly allowed")
    args = parser.parse_args(argv)
    try:
        as_of = parse_iso_date(args.as_of, "--as-of") if args.as_of else datetime.now(timezone.utc).date()
        receipt = import_package(
            args.package_dir,
            output_dir=args.output_dir,
            as_of=as_of,
            export_source=args.export_source,
        )
    except SourceImportError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print("✓ import manifest Draft 2020-12 validation")
    print("✓ fail-closed authorization/use policy")
    print("✓ terms snapshot SHA-256")
    print("✓ source-content SHA-256")
    print("✓ versioned synthetic parser profile")
    print("✓ normalized ProofGrid source-record schema/provenance")
    print("✓ raw-source redistribution policy")
    print(f"Normalized record: {receipt['normalized_record']['id']}")
    print("RESULT: AUTHORIZED_SOURCE_IMPORT_VERIFIABLE")
    print("NOT CERTIFIED")
    print(f"Receipt: {args.output_dir / 'import-receipt.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
