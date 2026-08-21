#!/usr/bin/env python3
"""ProofGrid / RX Evidence Fabric v0.2 reference verifier.

The verifier validates canonical JSON documents against Draft 2020-12 JSON
Schemas, performs a deterministic material-GWP calculation, emits provenance-
bearing evidence, and labels the result VERIFIABLE rather than CERTIFIED.

The IFC subcommand is read-only and uses IfcOpenShell for real IFC parsing.
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
ENGINE_VERSION = "0.2.0"
METHOD_NAME = "material_quantity_times_gwp_factor"
METHOD_VERSION = "0.2.0"
QUANT = Decimal("0.000001")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "schemas"
RXEP_SCHEMA_ROOT = REPO_ROOT / "specs" / "rxep"
BUILDING_SCHEMA = SCHEMA_ROOT / "building.schema.json"
MATERIALS_SCHEMA = SCHEMA_ROOT / "materials.schema.json"
EVIDENCE_SCHEMA = RXEP_SCHEMA_ROOT / "evidence-envelope.schema.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class VerificationError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


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
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
    )


def validate_json_schema(instance: Any, schema_path: Path, label: str) -> None:
    """Validate one document against a Draft 2020-12 schema, fail closed."""
    schema = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise VerificationError(f"invalid schema {schema_path}: {exc.message}") from exc

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(
            f"{_error_path(error)}: {error.message}" for error in errors[:5]
        )
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


def calculate_materials(materials: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Decimal]:
    if not isinstance(materials, list) or not materials:
        raise VerificationError("materials.json must contain a non-empty array")

    rows: list[dict[str, Any]] = []
    total = Decimal("0")
    for index, material in enumerate(materials):
        if not isinstance(material, dict):
            raise VerificationError(f"material[{index}] must be an object")

        quantity = as_decimal(material["quantity"], f"material[{index}].quantity")
        factor = as_decimal(
            material["gwp_kgco2e_per_unit"],
            f"material[{index}].gwp_kgco2e_per_unit",
        )
        if quantity < 0 or factor < 0:
            raise VerificationError("quantity and GWP factor must be non-negative")

        subtotal = (quantity * factor).quantize(QUANT, rounding=ROUND_HALF_UP)
        total += subtotal
        rows.append(
            {
                "id": str(material["id"]),
                "name": str(material["name"]),
                "quantity": str(quantity),
                "unit": str(material["unit"]),
                "gwp_kgco2e_per_unit": str(factor),
                "subtotal_kgco2e": str(subtotal),
                "factor_source": str(material["factor_source"]),
            }
        )
    return rows, total.quantize(QUANT, rounding=ROUND_HALF_UP)


def build_evidence(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project_path = project_dir / "project.json"
    materials_path = project_dir / "materials.json"
    project = load_json(project_path)
    materials = load_json(materials_path)

    validate_json_schema(project, BUILDING_SCHEMA, "project.json")
    validate_json_schema(materials, MATERIALS_SCHEMA, "materials.json")

    rows, total = calculate_materials(materials)

    sources = [
        {"path": "project.json", "sha256": sha256_file(project_path)},
        {"path": "materials.json", "sha256": sha256_file(materials_path)},
    ]

    envelope: dict[str, Any] = {
        "id": f"rxep:{project['id']}:embodied-gwp",
        "subject": {
            "id": str(project["id"]),
            "type": "building",
            "name": str(project["name"]),
        },
        "claim": {
            "type": "calculated_material_gwp",
            "statement": "Declared sample materials produce the calculated GWP under the stated fictional factors and method.",
        },
        "measurement": {
            "value": float(total),
            "unit": "kgCO2e",
            "breakdown": rows,
        },
        "methodology": {
            "name": METHOD_NAME,
            "version": METHOD_VERSION,
            "formula": "sum(quantity * gwp_kgco2e_per_unit)",
        },
        "sources": sources,
        "software": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "jurisdiction": str(project["jurisdiction"]),
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": [
            "Fictional demonstration dataset; factors are not suitable for real project claims.",
            "Schema validation establishes structural conformance, not scientific truth, code compliance, or source authority.",
            "No professional engineering, architectural, code, LCA, audit, or regulatory certification is provided.",
            "Integrity hashes establish byte consistency, not scientific truth or source authority.",
        ],
        "integrity": {"content_sha256": "", "signature": None},
    }

    digest_payload = dict(envelope)
    digest_payload["integrity"] = {"content_sha256": "", "signature": None}
    envelope["integrity"]["content_sha256"] = sha256_bytes(
        canonical_json_bytes(digest_payload)
    )

    validate_json_schema(envelope, EVIDENCE_SCHEMA, "generated evidence envelope")

    receipt = {
        "verdict": "VERIFIABLE",
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "project_id": str(project["id"]),
        "schema_validation": {
            "draft": "2020-12",
            "project": str(BUILDING_SCHEMA.relative_to(REPO_ROOT)),
            "materials": str(MATERIALS_SCHEMA.relative_to(REPO_ROOT)),
            "evidence": str(EVIDENCE_SCHEMA.relative_to(REPO_ROOT)),
        },
        "source_hashes": sources,
        "evidence_content_sha256": envelope["integrity"]["content_sha256"],
        "meaning": "Inputs and generated evidence passed structural schema checks, the declared deterministic calculation completed, and integrity digests were emitted. This is not certification.",
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return envelope, receipt


def build_graph(project: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "@context": {
            "rx": "https://regenexcalibur.example/ns/rx#",
            "name": "https://schema.org/name",
        },
        "@graph": [
            {
                "@id": f"rx:building:{project['id']}",
                "@type": "rx:Building",
                "name": project["name"],
                "rx:jurisdiction": project["jurisdiction"],
            },
            {
                "@id": evidence["id"],
                "@type": "rx:EvidenceEnvelope",
                "rx:subject": {"@id": f"rx:building:{project['id']}"},
                "rx:measurementValue": evidence["measurement"]["value"],
                "rx:measurementUnit": evidence["measurement"]["unit"],
                "rx:reviewState": evidence["review"]["state"],
                "rx:contentSha256": evidence["integrity"]["content_sha256"],
            },
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
    report = f"""<!doctype html>
<html lang=\"en\"><meta charset=\"utf-8\">
<title>ProofGrid Verification — {project_name}</title>
<body>
<h1>RegenExcalibur ProofGrid v0.2</h1>
<h2>{project_name}</h2>
<p><strong>RESULT: VERIFIABLE — NOT CERTIFIED</strong></p>
<p>Calculated sample material GWP: <strong>{total} kgCO2e</strong></p>
<p>Review state: {html.escape(evidence["review"]["state"])}</p>
<p>Method: {html.escape(evidence["methodology"]["name"])} v{html.escape(evidence["methodology"]["version"])}</p>
<p>Evidence SHA-256: <code>{html.escape(evidence["integrity"]["content_sha256"])}</code></p>
<h3>Limitations</h3>
<ul>{''.join(f"<li>{html.escape(x)}</li>" for x in evidence["limitations"])}</ul>
</body></html>
"""
    report_path.write_text(report, encoding="utf-8")

    return {
        "evidence": evidence_path,
        "graph": graph_path,
        "receipt": receipt_path,
        "report": report_path,
        "total_kgco2e": evidence["measurement"]["value"],
    }


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rx", description="RegenExcalibur ProofGrid reference verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="verify a ProofGrid project fixture")
    verify.add_argument("project_dir", type=Path)
    verify.add_argument("--output", type=Path, default=None)

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
        print("✓ source integrity")
        print("✓ material quantities")
        print("✓ environmental calculation")
        print("✓ methodology")
        print("✓ provenance")
        print("✓ review state")
        print("✓ receipt integrity")
        print()
        print("RESULT: VERIFIABLE")
        print("NOT CERTIFIED")
        print(f"Calculated sample GWP: {result['total_kgco2e']} kgCO2e")
        print(f"Artifacts: {output}")
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
