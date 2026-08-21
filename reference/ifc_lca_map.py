#!/usr/bin/env python3
"""ProofGrid v0.5 explicit IFC -> environmental source mapping verifier.

The verifier validates a human/reviewer-authored mapping artifact against the
v0.4 IFC declared-data extraction and the v0.3 provenance-controlled source
registry. It performs no fuzzy material matching, no geometry-derived quantity
takeoff, and no general unit conversion.

The only v0.5 unit identity bridge is IFC MASSUNIT KILO+GRAM -> ``kg``. The
numeric quantity is not changed by that identity bridge.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import rx_cli  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Explicit IFC Environmental Mapper"
ENGINE_VERSION = "0.5.0"
METHOD_VERSION = "0.5.0"
QUANT = Decimal("0.000001")
MAPPING_SCHEMA = ROOT / "schemas" / "ifc-lca-mapping.schema.json"
EXTRACTION_SCHEMA = ROOT / "schemas" / "ifc-extraction.schema.json"


class MappingError(ValueError):
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
        raise MappingError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MappingError(f"invalid JSON in {path}: {exc}") from exc


def _error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path)


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise MappingError(f"invalid schema {schema_path}: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{_error_path(error)}: {error.message}" for error in errors[:5])
        if len(errors) > 5:
            preview += f"; +{len(errors) - 5} more"
        raise MappingError(f"{label} failed schema validation: {preview}")


def as_decimal(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MappingError(f"{label} must be numeric") from exc
    if not result.is_finite():
        raise MappingError(f"{label} must be finite")
    return result


def boundary_signature(record: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(str(module) for module in record["system_boundary"]["modules"]))


def explicit_unit_identity(unit: dict[str, Any]) -> str:
    """Return the only unit identity bridge authorized in v0.5."""
    if (
        unit.get("unit_type") == "MASSUNIT"
        and unit.get("name") == "GRAM"
        and unit.get("prefix") == "KILO"
        and unit.get("source") in {"project_unit_context", "explicit_quantity_unit"}
    ):
        return "kg"
    raise MappingError(
        "unsupported IFC unit identity for v0.5 mapping; only MASSUNIT KILO+GRAM -> kg is authorized, with no numerical conversion"
    )


def _exact_unit_match(mapped: dict[str, Any], extracted: dict[str, Any] | None) -> None:
    if extracted is None:
        raise MappingError("referenced IFC quantity has no declared unit context")
    fields = ("unit_type", "name", "prefix", "source")
    for field in fields:
        if mapped.get(field) != extracted.get(field):
            raise MappingError(
                f"mapping quantity unit mismatch for {field}: expected extracted {extracted.get(field)!r}, got {mapped.get(field)!r}"
            )


def _mapping_identity(mapping: dict[str, Any]) -> tuple[Any, ...]:
    return (
        mapping["source_ifc"]["sha256"],
        mapping["element"]["global_id"],
        mapping["element"]["step_id"],
        mapping["material"]["association_step_id"],
        mapping["material"]["material_step_id"],
        mapping["quantity"]["set_step_id"],
        mapping["quantity"]["quantity_step_id"],
    )


def _find_element(extraction: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    wanted = mapping["element"]
    matches = [
        element
        for element in extraction["elements"]
        if element.get("global_id") == wanted["global_id"]
        and element.get("step_id") == wanted["step_id"]
        and element.get("ifc_type") == wanted["ifc_type"]
    ]
    if len(matches) != 1:
        raise MappingError(f"mapping element identity resolved to {len(matches)} extracted elements; expected exactly 1")
    return matches[0]


def _find_material(element: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    wanted = mapping["material"]
    if not wanted["declared_name"].strip():
        raise MappingError("mapping material name is blank/ambiguous")
    matches = [
        material
        for material in element["materials"]
        if material.get("association_step_id") == wanted["association_step_id"]
        and material.get("material_step_id") == wanted["material_step_id"]
        and material.get("name") == wanted["declared_name"]
        and material.get("source_type") == wanted["source_type"]
    ]
    if len(matches) != 1:
        raise MappingError(f"mapping material identity resolved to {len(matches)} extracted materials; expected exactly 1")
    if not matches[0].get("name"):
        raise MappingError("extracted IFC material name is missing/ambiguous and cannot be mapped")
    return matches[0]


def _find_quantity(element: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    wanted = mapping["quantity"]
    matches = [
        quantity
        for quantity in element["quantities"]
        if quantity.get("set_step_id") == wanted["set_step_id"]
        and quantity.get("quantity_step_id") == wanted["quantity_step_id"]
        and quantity.get("name") == wanted["name"]
        and quantity.get("ifc_quantity_type") == wanted["ifc_quantity_type"]
    ]
    if len(matches) != 1:
        raise MappingError(f"mapping quantity identity resolved to {len(matches)} extracted quantities; expected exactly 1")
    extracted = matches[0]
    if extracted.get("value_source") != "declared_ifc_element_quantity":
        raise MappingError("referenced IFC quantity is not a declared IfcElementQuantity value")
    if as_decimal(extracted["value"], "extracted quantity value") != as_decimal(wanted["value"], "mapping quantity value"):
        raise MappingError(
            f"mapping quantity value mismatch: extracted {extracted['value']!r}, mapping {wanted['value']!r}"
        )
    _exact_unit_match(wanted["unit"], extracted.get("unit"))
    return extracted


def map_explicit_ifc_environmental(
    extraction_path: Path,
    mapping_path: Path,
    registry_path: Path,
) -> dict[str, Any]:
    extraction_path = Path(extraction_path)
    mapping_path = Path(mapping_path)
    registry_path = Path(registry_path)
    extraction = load_json(extraction_path)
    mapping_artifact = load_json(mapping_path)
    registry = load_json(registry_path)

    validate_schema(extraction, EXTRACTION_SCHEMA, "IFC extraction")
    validate_schema(mapping_artifact, MAPPING_SCHEMA, "IFC environmental mapping artifact")

    try:
        source_index, registry_summary = rx_cli.validate_lca_registry(registry, registry_path.parent)
    except rx_cli.VerificationError as exc:
        raise MappingError(f"environmental source registry failed provenance validation: {exc}") from exc

    mapping_ids: set[str] = set()
    identity_targets: dict[tuple[Any, ...], tuple[str, str]] = {}
    results: list[dict[str, Any]] = []
    total = Decimal("0")
    expected_boundary: tuple[str, ...] | None = None
    expected_indicator: str | None = None

    for index, mapping in enumerate(mapping_artifact["mappings"]):
        mapping_id = str(mapping["id"])
        if mapping_id in mapping_ids:
            raise MappingError(f"duplicate mapping id: {mapping_id}")
        mapping_ids.add(mapping_id)

        identity = _mapping_identity(mapping)
        target_identity = (
            str(mapping["target"]["material_identity_id"]),
            str(mapping["target"]["source_record_id"]),
        )
        previous_target = identity_targets.get(identity)
        if previous_target is not None:
            if previous_target == target_identity:
                raise MappingError(f"duplicate mapping identity for {mapping_id}")
            raise MappingError(
                f"conflicting mappings for one IFC material/quantity identity: {previous_target} vs {target_identity}"
            )
        identity_targets[identity] = target_identity

        if mapping["review"]["state"] != "REVIEWED":
            raise MappingError(f"mapping {mapping_id} is not REVIEWED")

        if mapping["source_ifc"]["sha256"] != extraction["source_sha256"]:
            raise MappingError(f"mapping {mapping_id} source IFC SHA-256 does not match extraction")
        if mapping["source_ifc"]["schema"] != extraction["schema"]:
            raise MappingError(f"mapping {mapping_id} IFC schema does not match extraction")

        element = _find_element(extraction, mapping)
        material = _find_material(element, mapping)
        quantity = _find_quantity(element, mapping)
        unit_identity = explicit_unit_identity(quantity["unit"])

        source_record_id = str(mapping["target"]["source_record_id"])
        source_record = source_index.get(source_record_id)
        if source_record is None:
            raise MappingError(f"mapping {mapping_id} references missing environmental source record {source_record_id}")
        material_identity_id = str(mapping["target"]["material_identity_id"])
        if material_identity_id != str(source_record["material"]["id"]):
            raise MappingError(
                f"mapping {mapping_id} target material identity {material_identity_id!r} does not match source record material {source_record['material']['id']!r}"
            )
        declared_unit = str(source_record["declared_unit"])
        if declared_unit != unit_identity:
            raise MappingError(
                f"mapping {mapping_id} IFC unit identity {unit_identity!r} does not match environmental declared unit {declared_unit!r}; general unit conversion is prohibited"
            )

        boundary = boundary_signature(source_record)
        indicator_name = str(source_record["indicator"]["name"])
        if expected_boundary is None:
            expected_boundary = boundary
        elif boundary != expected_boundary:
            raise MappingError(f"incompatible lifecycle/system boundaries: {expected_boundary} vs {boundary}")
        if expected_indicator is None:
            expected_indicator = indicator_name
        elif indicator_name != expected_indicator:
            raise MappingError(f"incompatible environmental indicators: {expected_indicator!r} vs {indicator_name!r}")
        if str(source_record["indicator"]["unit"]) != "kgCO2e":
            raise MappingError(f"unsupported environmental indicator unit for {source_record_id}")

        quantity_value = as_decimal(quantity["value"], f"mapping[{index}].quantity")
        reference_quantity = as_decimal(source_record["reference_quantity"], f"source[{source_record_id}].reference_quantity")
        indicator_value = as_decimal(source_record["indicator"]["value"], f"source[{source_record_id}].indicator.value")
        if quantity_value < 0:
            raise MappingError("mapped quantity must be non-negative")
        if reference_quantity <= 0:
            raise MappingError("environmental source reference quantity must be greater than zero")
        subtotal = ((quantity_value / reference_quantity) * indicator_value).quantize(QUANT, rounding=ROUND_HALF_UP)
        total += subtotal

        results.append(
            {
                "mapping_id": mapping_id,
                "review": mapping["review"],
                "element": {
                    "global_id": element["global_id"],
                    "step_id": element["step_id"],
                    "ifc_type": element["ifc_type"],
                },
                "material": material,
                "quantity": {
                    "set_step_id": quantity["set_step_id"],
                    "quantity_step_id": quantity["quantity_step_id"],
                    "name": quantity["name"],
                    "ifc_quantity_type": quantity["ifc_quantity_type"],
                    "value": quantity["value"],
                    "unit": quantity["unit"],
                    "unit_identity": unit_identity,
                    "numerical_conversion_applied": False,
                    "value_source": quantity["value_source"],
                },
                "target": {
                    "material_identity_id": material_identity_id,
                    "source_record_id": source_record_id,
                    "source_record_sha256": sha256_bytes(canonical_json_bytes(source_record)),
                    "declared_unit": declared_unit,
                    "reference_quantity": float(reference_quantity),
                    "indicator": {
                        "name": indicator_name,
                        "value": float(indicator_value),
                        "unit": str(source_record["indicator"]["unit"]),
                    },
                    "system_boundary": {"modules": list(boundary)},
                },
                "subtotal_kgco2e": float(subtotal),
            }
        )

    assert expected_boundary is not None
    assert expected_indicator is not None
    receipt: dict[str, Any] = {
        "verdict": "EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE",
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION, "method_version": METHOD_VERSION},
        "mapping_artifact": {
            "artifact_version": mapping_artifact["artifact_version"],
            "file_sha256": sha256_file(mapping_path),
            "content_sha256": sha256_bytes(canonical_json_bytes(mapping_artifact)),
        },
        "ifc_extraction": {
            "file_sha256": sha256_file(extraction_path),
            "source_ifc_sha256": extraction["source_sha256"],
            "schema": extraction["schema"],
            "adapter": extraction["adapter"],
            "adapter_version": extraction["adapter_version"],
        },
        "environmental_registry": {
            "file_sha256": sha256_file(registry_path),
            "records": registry_summary["records"],
            "verified_source_files": registry_summary["verified_source_files"],
        },
        "indicator": expected_indicator,
        "system_boundary": {"modules": list(expected_boundary)},
        "unit_policy": "IFC MASSUNIT KILO+GRAM is recognized only as the identity kg; numerical quantity is unchanged; no general conversion is performed",
        "results": results,
        "total_kgco2e": float(total.quantize(QUANT, rounding=ROUND_HALF_UP)),
        "limitations": [
            "Every environmental target is supplied by an explicit REVIEWED mapping artifact; material names are not fuzzy-matched to source records.",
            "Only declared IfcElementQuantity values are accepted; geometry-derived quantities are outside this gate.",
            "Only the explicit IFC MASSUNIT KILO+GRAM -> kg unit identity is recognized in v0.5 and no numerical conversion is performed.",
            "Source-registry provenance integrity does not establish scientific suitability of a source record for a real project.",
            "This receipt is not an LCA, code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion.",
        ],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and calculate explicit IFC-to-environmental mapping records")
    parser.add_argument("--extraction", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = map_explicit_ifc_environmental(args.extraction, args.mapping, args.registry)
    except MappingError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print("✓ mapping artifact Draft 2020-12 validation")
    print("✓ exact IFC source/element/material/quantity identity validation")
    print("✓ explicit reviewed mapping state")
    print("✓ environmental source-registry provenance")
    print("✓ exact v0.5 kg unit identity; no numerical conversion")
    print("✓ lifecycle/indicator compatibility")
    print("✓ mapping/extraction/source-record provenance receipt")
    print(f"Mapped records: {len(receipt['results'])}")
    print(f"Calculated mapped GWP: {receipt['total_kgco2e']} kgCO2e")
    print("RESULT: EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE")
    print("NOT CERTIFIED")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
