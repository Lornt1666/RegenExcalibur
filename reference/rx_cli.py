#!/usr/bin/env python3
"""ProofGrid / RX Evidence Fabric v0.3 reference verifier.

v0.3 adds a provenance-controlled LCA/EPD source registry. Material quantities
reference exact source-record IDs; no fuzzy matching or implicit unit conversion
is allowed. Compatible lifecycle boundaries and indicator units are enforced
before deterministic calculation.

The IFC subcommand remains read-only and uses IfcOpenShell for structural parsing.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import html
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ENGINE_NAME = "RegenExcalibur ProofGrid Reference Verifier"
ENGINE_VERSION = "0.3.0"
METHOD_NAME = "registry_resolved_material_gwp"
METHOD_VERSION = "0.3.0"
QUANT = Decimal("0.000001")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "schemas"
RXEP_SCHEMA_ROOT = REPO_ROOT / "specs" / "rxep"
BUILDING_SCHEMA = SCHEMA_ROOT / "building.schema.json"
MATERIALS_SCHEMA = SCHEMA_ROOT / "materials.schema.json"
LCA_SOURCES_SCHEMA = SCHEMA_ROOT / "lca-source-records.schema.json"
EVIDENCE_SCHEMA = RXEP_SCHEMA_ROOT / "evidence-envelope.schema.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class VerificationError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid JSON in {path}: {exc}") from exc


def _error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path)


def validate_json_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise VerificationError(f"invalid schema {schema_path}: {exc.message}") from exc
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{_error_path(error)}: {error.message}" for error in errors[:5])
        if len(errors) > 5:
            preview += f"; +{len(errors) - 5} more"
        raise VerificationError(f"{label} failed schema validation: {preview}")


def as_decimal(value: Any, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise VerificationError(f"{label} must be numeric") from exc
    if not number.is_finite():
        raise VerificationError(f"{label} must be finite")
    return number


def _safe_local_source(project_dir: Path, reference: str) -> Path:
    root = project_dir.resolve()
    candidate = (project_dir / reference).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"source reference escapes project directory: {reference}") from exc
    if not candidate.is_file():
        raise VerificationError(f"missing source content file: {reference}")
    return candidate


def _boundary_signature(record: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(str(module) for module in record["system_boundary"]["modules"]))


def _source_identity(record: dict[str, Any]) -> tuple[str, ...]:
    source = record["source"]
    return (
        str(record["material"]["id"]),
        str(source["publisher"]),
        str(source["document_id"]),
        str(source["version"]),
        str(record["declared_unit"]),
        str(record["reference_quantity"]),
        str(record["indicator"]["name"]),
        "|".join(_boundary_signature(record)),
    )


def validate_lca_registry(registry: list[dict[str, Any]], project_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Validate registry structure, identities, local content hashes, and conflicts."""
    validate_json_schema(registry, LCA_SOURCES_SCHEMA, "lca-sources.json")
    index: dict[str, dict[str, Any]] = {}
    identity_index: dict[tuple[str, ...], dict[str, Any]] = {}
    verified_files: dict[str, str] = {}
    for record in registry:
        record_id = str(record["id"])
        if record_id in index:
            raise VerificationError(f"duplicate LCA source record id: {record_id}")
        source = record["source"]
        reference = str(source["reference"])
        source_path = _safe_local_source(project_dir, reference)
        actual_hash = sha256_file(source_path)
        expected_hash = str(source["source_content_sha256"])
        if actual_hash != expected_hash:
            raise VerificationError(f"source hash mismatch for {record_id}: expected {expected_hash}, got {actual_hash}")
        verified_files[reference] = actual_hash
        identity = _source_identity(record)
        previous = identity_index.get(identity)
        if previous is not None:
            prev_indicator = previous["indicator"]
            indicator = record["indicator"]
            if str(prev_indicator["value"]) != str(indicator["value"]) or str(prev_indicator["unit"]) != str(indicator["unit"]):
                raise VerificationError(
                    "conflicting LCA source records for the same source/document/material/boundary identity: "
                    f"{previous['id']} vs {record_id}"
                )
            raise VerificationError(f"duplicate semantic LCA source records: {previous['id']} vs {record_id}")
        index[record_id] = record
        identity_index[identity] = record
    summary = {
        "records": len(index),
        "record_ids": sorted(index),
        "verified_source_files": [{"path": path, "sha256": digest} for path, digest in sorted(verified_files.items())],
    }
    return index, summary


def resolve_materials(materials: list[dict[str, Any]], source_index: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], Decimal, tuple[str, ...], str]:
    if not materials:
        raise VerificationError("materials.json must contain a non-empty array")
    rows: list[dict[str, Any]] = []
    total = Decimal("0")
    expected_boundary: tuple[str, ...] | None = None
    expected_indicator: str | None = None
    for index, material in enumerate(materials):
        source_record_id = str(material["source_record_id"])
        record = source_index.get(source_record_id)
        if record is None:
            raise VerificationError(f"material[{index}] references missing LCA source record: {source_record_id}")
        material_identity_id = str(material["material_identity_id"])
        if material_identity_id != str(record["material"]["id"]):
            raise VerificationError(
                f"material[{index}] identity {material_identity_id} does not match source record "
                f"{source_record_id} material identity {record['material']['id']}"
            )
        material_unit = str(material["unit"])
        declared_unit = str(record["declared_unit"])
        if material_unit != declared_unit:
            raise VerificationError(
                f"material[{index}] unit {material_unit!r} does not exactly match source record "
                f"{source_record_id} declared unit {declared_unit!r}; implicit unit conversion is prohibited"
            )
        boundary = _boundary_signature(record)
        if expected_boundary is None:
            expected_boundary = boundary
        elif boundary != expected_boundary:
            raise VerificationError(f"incompatible lifecycle/system boundaries in one calculation: {expected_boundary} vs {boundary}")
        indicator_name = str(record["indicator"]["name"])
        if expected_indicator is None:
            expected_indicator = indicator_name
        elif indicator_name != expected_indicator:
            raise VerificationError(f"incompatible indicators in one calculation: {expected_indicator!r} vs {indicator_name!r}")
        indicator_unit = str(record["indicator"]["unit"])
        if indicator_unit != "kgCO2e":
            raise VerificationError(f"unsupported indicator unit {indicator_unit!r} for {source_record_id}; v0.3 calculation requires kgCO2e")
        quantity = as_decimal(material["quantity"], f"material[{index}].quantity")
        reference_quantity = as_decimal(record["reference_quantity"], f"source[{source_record_id}].reference_quantity")
        indicator_value = as_decimal(record["indicator"]["value"], f"source[{source_record_id}].indicator.value")
        if quantity < 0:
            raise VerificationError("material quantity must be non-negative")
        if reference_quantity <= 0:
            raise VerificationError("source reference quantity must be greater than zero")
        subtotal = ((quantity / reference_quantity) * indicator_value).quantize(QUANT, rounding=ROUND_HALF_UP)
        total += subtotal
        rows.append({
            "id": str(material["id"]),
            "material_identity_id": material_identity_id,
            "name": str(material["name"]),
            "quantity": str(quantity),
            "unit": material_unit,
            "source_record_id": source_record_id,
            "source_record_sha256": sha256_bytes(canonical_json_bytes(record)),
            "indicator": {
                "name": indicator_name,
                "value": str(indicator_value),
                "unit": indicator_unit,
                "reference_quantity": str(reference_quantity),
                "declared_unit": declared_unit,
            },
            "system_boundary": {"modules": list(boundary)},
            "subtotal_kgco2e": str(subtotal),
        })
    assert expected_boundary is not None
    assert expected_indicator is not None
    return rows, total.quantize(QUANT, rounding=ROUND_HALF_UP), expected_boundary, expected_indicator


def build_evidence(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project_path = project_dir / "project.json"
    materials_path = project_dir / "materials.json"
    registry_path = project_dir / "lca-sources.json"
    project = load_json(project_path)
    materials = load_json(materials_path)
    registry = load_json(registry_path)
    validate_json_schema(project, BUILDING_SCHEMA, "project.json")
    validate_json_schema(materials, MATERIALS_SCHEMA, "materials.json")
    source_index, registry_summary = validate_lca_registry(registry, project_dir)
    rows, total, boundary, indicator_name = resolve_materials(materials, source_index)
    sources = [
        {"path": "project.json", "sha256": sha256_file(project_path), "kind": "project"},
        {"path": "materials.json", "sha256": sha256_file(materials_path), "kind": "material-quantities"},
        {"path": "lca-sources.json", "sha256": sha256_file(registry_path), "kind": "lca-source-registry"},
    ]
    for item in registry_summary["verified_source_files"]:
        sources.append({"path": item["path"], "sha256": item["sha256"], "kind": "environmental-source-content"})
    all_synthetic = all(bool(record["synthetic"]) for record in registry)
    limitations = [
        "Schema and hash validation establish structural/provenance integrity, not scientific validity or source authority.",
        "No implicit unit conversion is performed; material and source declared units must match exactly.",
        "All source records used in one v0.3 calculation must share one lifecycle/system boundary and indicator.",
        "No professional engineering, architectural, code, LCA, audit, procurement, or regulatory certification is provided.",
    ]
    if all_synthetic:
        limitations.insert(0, "All environmental factors in this fixture are synthetic test data and are prohibited for real project claims.")
    envelope: dict[str, Any] = {
        "id": f"rxep:{project['id']}:embodied-gwp",
        "subject": {"id": str(project["id"]), "type": "building", "name": str(project["name"])},
        "claim": {
            "type": "calculated_material_gwp",
            "statement": "Declared material quantities were resolved by exact material identity and LCA source-record ID, then calculated under one explicit lifecycle boundary and indicator.",
        },
        "measurement": {
            "value": float(total),
            "unit": "kgCO2e",
            "indicator": indicator_name,
            "system_boundary": {"modules": list(boundary)},
            "breakdown": rows,
        },
        "methodology": {
            "name": METHOD_NAME,
            "version": METHOD_VERSION,
            "formula": "sum((quantity / reference_quantity) * indicator_value)",
            "unit_policy": "exact-match-only; no implicit conversion",
            "source_selection_policy": "exact source_record_id; no fuzzy matching",
        },
        "sources": sources,
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": str(project["jurisdiction"]),
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": limitations,
        "integrity": {"content_sha256": "", "signature": None},
    }
    digest_payload = dict(envelope)
    digest_payload["integrity"] = {"content_sha256": "", "signature": None}
    envelope["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(digest_payload))
    validate_json_schema(envelope, EVIDENCE_SCHEMA, "generated evidence envelope")
    used_record_ids = sorted({str(material["source_record_id"]) for material in materials})
    record_digests = [{"id": record_id, "sha256": sha256_bytes(canonical_json_bytes(source_index[record_id]))} for record_id in used_record_ids]
    receipt = {
        "verdict": "VERIFIABLE",
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "project_id": str(project["id"]),
        "schema_validation": {
            "draft": "2020-12",
            "project": str(BUILDING_SCHEMA.relative_to(REPO_ROOT)),
            "materials": str(MATERIALS_SCHEMA.relative_to(REPO_ROOT)),
            "lca_sources": str(LCA_SOURCES_SCHEMA.relative_to(REPO_ROOT)),
            "evidence": str(EVIDENCE_SCHEMA.relative_to(REPO_ROOT)),
        },
        "lca_registry": {
            "path": "lca-sources.json",
            "sha256": sha256_file(registry_path),
            "source_record_ids": used_record_ids,
            "source_record_digests": record_digests,
            "system_boundary": {"modules": list(boundary)},
            "indicator": indicator_name,
            "unit_policy": "exact-match-only",
        },
        "source_hashes": sources,
        "evidence_content_sha256": envelope["integrity"]["content_sha256"],
        "meaning": "Inputs, the environmental source registry, source-content hashes, and generated evidence passed structural/provenance checks; exact source IDs were resolved and a deterministic calculation completed. This is not certification or scientific validation of the underlying source claims.",
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return envelope, receipt


def build_graph(project: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "@context": {"rx": "https://regenexcalibur.example/ns/rx#", "name": "https://schema.org/name"},
        "@graph": [
            {"@id": f"rx:building:{project['id']}", "@type": "rx:Building", "name": project["name"], "rx:jurisdiction": project["jurisdiction"]},
            {"@id": evidence["id"], "@type": "rx:EvidenceEnvelope", "rx:subject": {"@id": f"rx:building:{project['id']}"}, "rx:measurementValue": evidence["measurement"]["value"], "rx:measurementUnit": evidence["measurement"]["unit"], "rx:reviewState": evidence["review"]["state"], "rx:contentSha256": evidence["integrity"]["content_sha256"]},
        ],
    }


def write_outputs(project_dir: Path, output_dir: Path) -> dict[str, Any]:
    evidence, receipt = build_evidence(project_dir)
    project = load_json(project_dir / "project.json")
    graph = build_graph(project, evidence)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "evidence.json"
    graph_path = output_dir / "graph.jsonld"
    receipt_path = output_dir / "receipt.json"
    report_path = output_dir / "report.html"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    total = html.escape(str(evidence["measurement"]["value"]))
    project_name = html.escape(str(project["name"]))
    boundary = html.escape(", ".join(evidence["measurement"]["system_boundary"]["modules"]))
    report = f"""<!doctype html>
<html lang=\"en\"><meta charset=\"utf-8\">
<title>ProofGrid Verification — {project_name}</title>
<body>
<h1>RegenExcalibur ProofGrid v0.3</h1>
<h2>{project_name}</h2>
<p><strong>RESULT: VERIFIABLE — NOT CERTIFIED</strong></p>
<p>Calculated sample material GWP: <strong>{total} kgCO2e</strong></p>
<p>Lifecycle/system boundary: <strong>{boundary}</strong></p>
<p>Review state: {html.escape(evidence["review"]["state"])}</p>
<p>Method: {html.escape(evidence["methodology"]["name"])} v{html.escape(evidence["methodology"]["version"])}</p>
<p>Evidence SHA-256: <code>{html.escape(evidence["integrity"]["content_sha256"])}</code></p>
<h3>Limitations</h3>
<ul>{''.join(f"<li>{html.escape(x)}</li>" for x in evidence["limitations"])}</ul>
</body></html>
"""
    report_path.write_text(report, encoding="utf-8")
    return {"evidence": evidence_path, "graph": graph_path, "receipt": receipt_path, "report": report_path, "total_kgco2e": evidence["measurement"]["value"]}


def inspect_ifc(path: Path, output: Path | None = None) -> dict[str, Any]:
    from adapters.ifc.reader import IFCAdapterError, inspect_ifc as adapter_inspect_ifc
    try:
        summary = adapter_inspect_ifc(path)
    except IFCAdapterError as exc:
        raise VerificationError(str(exc)) from exc
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def validate_registry_command(project_dir: Path, output: Path | None = None) -> dict[str, Any]:
    registry = load_json(project_dir / "lca-sources.json")
    _, summary = validate_lca_registry(registry, project_dir)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rx", description="RegenExcalibur ProofGrid reference verifier")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="verify a ProofGrid project fixture")
    verify.add_argument("project_dir", type=Path)
    verify.add_argument("--output", type=Path, default=None)
    registry = sub.add_parser("lca-registry-validate", help="validate LCA/EPD registry schema, identities, and source-content hashes")
    registry.add_argument("project_dir", type=Path)
    registry.add_argument("--output", type=Path, default=None)
    ifc = sub.add_parser("ifc-inspect", help="read-only IFC structural inspection via IfcOpenShell")
    ifc.add_argument("ifc_file", type=Path)
    ifc.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.command == "verify":
        output = args.output or (args.project_dir / "generated")
        try:
            result = write_outputs(args.project_dir, output)
        except VerificationError as exc:
            print(f"FAILED: {exc}")
            return 2
        print("✓ Draft 2020-12 schema validation")
        print("✓ LCA/EPD source registry provenance")
        print("✓ source-content hash validation")
        print("✓ exact source-record resolution")
        print("✓ exact unit matching")
        print("✓ lifecycle boundary compatibility")
        print("✓ deterministic environmental calculation")
        print("✓ evidence and receipt integrity")
        print()
        print("RESULT: VERIFIABLE")
        print("NOT CERTIFIED")
        print(f"Calculated sample GWP: {result['total_kgco2e']} kgCO2e")
        print(f"Artifacts: {output}")
        return 0
    if args.command == "lca-registry-validate":
        try:
            summary = validate_registry_command(args.project_dir, args.output)
        except VerificationError as exc:
            print(f"FAILED: {exc}")
            return 2
        print("✓ LCA/EPD registry schema")
        print("✓ record identity checks")
        print("✓ source-content hashes")
        print(f"Records: {summary['records']}")
        print("RESULT: SOURCE_REGISTRY_VERIFIABLE")
        print("SOURCE INTEGRITY IS NOT SCIENTIFIC VALIDITY OR CERTIFICATION")
        return 0
    if args.command == "ifc-inspect":
        try:
            summary = inspect_ifc(args.ifc_file, args.output)
        except VerificationError as exc:
            print(f"FAILED: {exc}")
            return 2
        print("✓ IFC parsed with IfcOpenShell")
        print(f"Schema: {summary['schema']}")
        print(f"Projects: {summary['counts']['projects']}")
        print(f"Buildings: {summary['counts']['buildings']}")
        print("RESULT: STRUCTURALLY_INGESTED")
        print("NO COMPLIANCE, LCA, ENGINEERING, OR CERTIFICATION CONCLUSION")
        if args.output:
            print(f"Summary: {args.output}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
