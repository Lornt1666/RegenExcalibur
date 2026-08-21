#!/usr/bin/env python3
"""ProofGrid v0.4 IFC declared-quantity/material extraction CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "schemas" / "ifc-extraction.schema.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.ifc.extract import IFCExtractionError, extract_ifc_declared_data


class IFCConformanceError(ValueError):
    pass


def _error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path)


def validate_output(output: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise IFCConformanceError(f"invalid extraction schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(output), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{_error_path(error)}: {error.message}" for error in errors[:5])
        raise IFCConformanceError(f"IFC extraction failed schema validation: {preview}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rx-ifc-extract",
        description="Extract declared IFC quantities/material associations without LCA mapping.",
    )
    parser.add_argument("ifc_file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = extract_ifc_declared_data(args.ifc_file)
        validate_output(result)
    except (IFCExtractionError, IFCConformanceError) as exc:
        print(f"FAILED: {exc}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    quantity_count = sum(len(element["quantities"]) for element in result["elements"])
    material_count = sum(len(element["materials"]) for element in result["elements"])
    print("✓ real IFC parsed with IfcOpenShell")
    print("✓ source SHA-256 retained")
    print("✓ project unit context retained")
    print("✓ project/building/storey/space hierarchy retained")
    print("✓ declared IfcElementQuantity values extracted")
    print("✓ IFC material associations extracted")
    print("✓ Draft 2020-12 extraction schema")
    print(f"Elements: {len(result['elements'])}")
    print(f"Declared quantities: {quantity_count}")
    print(f"Material associations: {material_count}")
    print("RESULT: DECLARED_IFC_DATA_EXTRACTED")
    print("NO ENVIRONMENTAL FACTOR LINKAGE OR PROFESSIONAL CONCLUSION")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
