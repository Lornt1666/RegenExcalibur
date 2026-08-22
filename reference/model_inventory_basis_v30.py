#!/usr/bin/env python3
"""ProofGrid v3.0 policy-closed IFC model inventory basis.

Synthetic IFC fixtures may exercise mechanics but are structurally ineligible for
v3.0 acceptance. A real acceptance-eligible run requires an exact source
authorization manifest bound to the IFC SHA-256.
"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
POLICY_SCHEMA_PATH = ROOT / "conformance" / "real-ifc-v30" / "inventory-policy.json"
ADMISSION_SCHEMA = ROOT / "schemas" / "model-admission-v30.schema.json"
BASIS_SCHEMA = ROOT / "schemas" / "model-inventory-basis-v30.schema.json"
AUTH_SCHEMA = ROOT / "schemas" / "real-ifc-authorization-v30.schema.json"

CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

_QUANTITY_TYPES: tuple[tuple[str, str, str | None], ...] = (
    ("IfcQuantityLength", "LengthValue", "LENGTHUNIT"),
    ("IfcQuantityArea", "AreaValue", "AREAUNIT"),
    ("IfcQuantityVolume", "VolumeValue", "VOLUMEUNIT"),
    ("IfcQuantityWeight", "WeightValue", "MASSUNIT"),
    ("IfcQuantityCount", "CountValue", None),
    ("IfcQuantityTime", "TimeValue", "TIMEUNIT"),
)

_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$")
_TYPED_NUMERIC_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*\(\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s*\)$"
)


class ModelInventoryError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ModelInventoryError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise ModelInventoryError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelInventoryError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def validate_schema(value: dict[str, Any], schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ModelInventoryError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path)
    )
    if errors:
        preview = "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors[:8]
        )
        raise ModelInventoryError(f"{label} failed schema validation: {preview}")


def _self_hash(record: dict[str, Any]) -> str:
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    return sha256_bytes(canonical_json_bytes(shadow))


def _string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _entity_id(entity: Any) -> int | None:
    if entity is None or not hasattr(entity, "id"):
        return None
    try:
        value = int(entity.id())
    except Exception:
        return None
    return value if value > 0 else None


def _canonical_decimal_from_lexical(token: str) -> str:
    text = token.strip()
    numeric = text
    if not _NUMERIC_RE.fullmatch(numeric):
        match = _TYPED_NUMERIC_RE.fullmatch(numeric)
        require(match is not None, f"unsupported IFC numeric lexical token: {token}")
        numeric = match.group(1)
    try:
        value = Decimal(numeric)
    except InvalidOperation as exc:
        raise ModelInventoryError(f"invalid Decimal token: {token}") from exc
    require(value.is_finite(), f"non-finite Decimal token: {token}")
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _scan_step_records(raw: bytes, max_records: int) -> dict[int, str]:
    text = raw.decode("latin-1")
    records: dict[int, str] = {}
    for match in re.finditer(r"(?m)^[ \t]*#(\d+)[ \t]*=", text):
        step_id = int(match.group(1))
        require(step_id not in records, f"duplicate STEP record id: {step_id}")
        i = match.end()
        in_string = False
        end = None
        while i < len(text):
            ch = text[i]
            if ch == "'":
                if in_string and i + 1 < len(text) and text[i + 1] == "'":
                    i += 2
                    continue
                in_string = not in_string
            elif ch == ";" and not in_string:
                end = i + 1
                break
            i += 1
        require(end is not None, f"unterminated STEP record: #{step_id}")
        records[step_id] = text[match.start() : end].strip()
        require(
            len(records) <= max_records,
            f"STEP record budget exceeded: {len(records)} > {max_records}",
        )
    require(records, "no STEP entity records found")
    return records


def _split_step_arguments(record: str) -> list[str]:
    left = record.find("(")
    right = record.rfind(")")
    require(left >= 0 and right > left, "STEP record has no argument list")
    body = record[left + 1 : right]
    args: list[str] = []
    start = 0
    depth = 0
    in_string = False
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "'":
            if in_string and i + 1 < len(body) and body[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
        elif not in_string:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                require(depth >= 0, "unbalanced STEP argument parentheses")
            elif ch == "," and depth == 0:
                args.append(body[start:i].strip())
                start = i + 1
        i += 1
    require(not in_string and depth == 0, "unterminated STEP argument structure")
    args.append(body[start:].strip())
    return args


def _quantity_lexical(records: dict[int, str], quantity: Any) -> tuple[str, str]:
    step_id = int(quantity.id())
    require(step_id in records, f"quantity STEP record missing: #{step_id}")
    args = _split_step_arguments(records[step_id])
    require(len(args) >= 4, f"quantity STEP record too short: #{step_id}")
    lexical = args[3]
    canonical = _canonical_decimal_from_lexical(lexical)
    return lexical, canonical


def _unit_summary(unit: Any, source: str) -> dict[str, Any]:
    return {
        "step_id": _entity_id(unit),
        "ifc_type": str(unit.is_a()),
        "unit_type": _string(getattr(unit, "UnitType", None)),
        "name": _string(getattr(unit, "Name", None)),
        "prefix": _string(getattr(unit, "Prefix", None)),
        "source": source,
    }


def _project_unit_map(model: Any) -> dict[str, dict[str, Any]]:
    projects = list(model.by_type("IfcProject"))
    require(len(projects) == 1, f"v3.0 requires exactly one IfcProject; found {len(projects)}")
    units_context = getattr(projects[0], "UnitsInContext", None)
    if units_context is None:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for unit in list(getattr(units_context, "Units", None) or ()):
        unit_type = _string(getattr(unit, "UnitType", None))
        if not unit_type:
            continue
        require(unit_type not in result, f"duplicate project unit type: {unit_type}")
        result[unit_type] = _unit_summary(unit, "project_unit_context")
    return result


def _quantity_spec(quantity: Any) -> tuple[str, str | None] | None:
    for ifc_type, attr, unit_type in _QUANTITY_TYPES:
        if quantity.is_a(ifc_type):
            return attr, unit_type
    return None


def _quantity_rows(
    element: Any,
    project_units: dict[str, dict[str, Any]],
    records: dict[int, str],
    max_relationships: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list(getattr(element, "IsDefinedBy", None) or ()):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        definition = getattr(relation, "RelatingPropertyDefinition", None)
        if definition is None or not definition.is_a("IfcElementQuantity"):
            continue
        for quantity in list(getattr(definition, "Quantities", None) or ()):
            spec = _quantity_spec(quantity)
            if spec is None:
                continue
            value_attr, unit_type = spec
            parser_value = getattr(quantity, value_attr, None)
            require(parser_value is not None, f"quantity parser value missing: #{quantity.id()}")
            lexical, decimal_text = _quantity_lexical(records, quantity)
            try:
                parser_decimal = Decimal(str(parser_value))
            except InvalidOperation as exc:
                raise ModelInventoryError(
                    f"quantity parser value is not Decimal-compatible: #{quantity.id()}"
                ) from exc
            require(
                parser_decimal == Decimal(decimal_text),
                f"source lexical/parser numeric mismatch: quantity #{quantity.id()}",
            )
            explicit_unit = getattr(quantity, "Unit", None)
            if explicit_unit is not None:
                unit = _unit_summary(explicit_unit, "explicit_quantity_unit")
            elif unit_type and unit_type in project_units:
                unit = dict(project_units[unit_type])
            elif unit_type is None:
                unit = None
            else:
                unit = {
                    "step_id": None,
                    "ifc_type": "UNRESOLVED",
                    "unit_type": unit_type,
                    "name": None,
                    "prefix": None,
                    "source": "unresolved",
                }
            rows.append(
                {
                    "relationship_step_id": int(relation.id()),
                    "set_step_id": int(definition.id()),
                    "set_name": _string(getattr(definition, "Name", None)),
                    "quantity_step_id": int(quantity.id()),
                    "quantity_type": str(quantity.is_a()),
                    "name": _string(getattr(quantity, "Name", None)),
                    "value_lexical": lexical,
                    "value_decimal": decimal_text,
                    "parser_numeric_value": float(parser_value),
                    "parser_numeric_value_is_authority": False,
                    "source_token_is_authority": True,
                    "unit": unit,
                }
            )
            require(
                len(rows) <= max_relationships,
                "declared-quantity relationship budget exceeded for one entry",
            )
    rows.sort(key=lambda row: (row["set_step_id"], row["quantity_step_id"]))
    return rows


def _target_ref(relation: Any, target: Any) -> dict[str, Any]:
    return {
        "relationship_step_id": int(relation.id()),
        "relationship_type": str(relation.is_a()),
        "target_step_id": int(target.id()),
        "target_global_id": _string(getattr(target, "GlobalId", None)),
        "target_ifc_type": str(target.is_a()),
    }


def _containment_rows(entity: Any, max_relationships: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list(getattr(entity, "ContainedInStructure", None) or ()):
        target = getattr(relation, "RelatingStructure", None)
        if target is None:
            continue
        rows.append(_target_ref(relation, target))
    require(len(rows) <= max_relationships, "containment relationship budget exceeded")
    rows.sort(key=lambda row: row["relationship_step_id"])
    return rows


def _decomposition_rows(entity: Any, max_relationships: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list(getattr(entity, "Decomposes", None) or ()):
        target = getattr(relation, "RelatingObject", None)
        if target is None:
            continue
        rows.append(_target_ref(relation, target))
    require(len(rows) <= max_relationships, "decomposition relationship budget exceeded")
    rows.sort(key=lambda row: row["relationship_step_id"])
    return rows


def _material_rows(entity: Any, max_relationships: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list(getattr(entity, "HasAssociations", None) or ()):
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        material = getattr(relation, "RelatingMaterial", None)
        require(material is not None, f"material relation has no RelatingMaterial: #{relation.id()}")
        rows.append(
            {
                "association_step_id": int(relation.id()),
                "relating_material_step_id": _entity_id(material),
                "relating_material_type": str(material.is_a()),
            }
        )
    require(len(rows) <= max_relationships, "material relationship budget exceeded")
    rows.sort(key=lambda row: row["association_step_id"])
    return rows


def _classification(entity: Any, policy: dict[str, Any]) -> tuple[str, str]:
    rules = policy["classification"]
    ifc_type = str(entity.is_a())
    if ifc_type in rules["evidence_not_applicable_exact_types"]:
        return "EVIDENCE_NOT_APPLICABLE", rules["evidence_not_applicable_reason"]
    if ifc_type in rules["out_of_declared_evidence_scope_exact_types"]:
        return "OUT_OF_DECLARED_EVIDENCE_SCOPE", rules["out_of_scope_reason"]
    if entity.is_a(rules["evidence_required_supertype"]):
        return "EVIDENCE_REQUIRED", "POLICY_REQUIRES_ENVIRONMENTAL_EVIDENCE"
    raise ModelInventoryError(f"enumerated IFC type is not classified by policy: {ifc_type}")


def _enumerated_entities(model: Any, policy: dict[str, Any]) -> list[Any]:
    by_step: dict[int, Any] = {}
    for ifc_type in policy["enumeration_types"]:
        try:
            entities = list(model.by_type(ifc_type))
        except Exception as exc:
            raise ModelInventoryError(f"unable to enumerate {ifc_type}: {exc}") from exc
        for entity in entities:
            step_id = int(entity.id())
            if step_id in by_step:
                continue
            by_step[step_id] = entity
    limit = int(policy["resource_limits"]["max_enumerated_objects"])
    require(by_step, "inventory policy enumerated zero objects")
    require(len(by_step) <= limit, f"enumerated object budget exceeded: {len(by_step)} > {limit}")
    return [by_step[key] for key in sorted(by_step)]


def _validate_policy(policy: dict[str, Any]) -> None:
    require(policy.get("policy_version") == "3.0.0", "unsupported inventory policy version")
    require(policy.get("policy_type") == "PROOFGRID_MODEL_INVENTORY_POLICY", "wrong policy type")
    require(policy.get("determinism", {}).get("network_resolution") == "FORBIDDEN", "network resolution must be forbidden")
    require(policy.get("determinism", {}).get("source_path_is_authority") is False, "source path cannot be authority")
    require(policy.get("determinism", {}).get("source_bytes_are_authority") is True, "source bytes must be authority")
    boundary = policy.get("acceptance_boundary", {})
    require(boundary.get("synthetic_fixtures_may_satisfy_v30_acceptance") is False, "synthetic acceptance must be forbidden")
    require(boundary.get("real_user_authorized_ifc_required_for_v30_acceptance") is True, "real IFC authorization must be required")
    require(boundary.get("whole_building_lca_claimed") is False, "whole-building promotion rejected")
    require(boundary.get("scientific_validation_performed") is False, "scientific-validation promotion rejected")
    require(boundary.get("professional_review_performed") is False, "professional-review promotion rejected")
    require(boundary.get("certified") is False, "certification promotion rejected")


def _validate_authorization(
    auth_path: Path | None, source_sha: str, synthetic_input: bool
) -> tuple[str | None, bytes | None]:
    if synthetic_input:
        require(auth_path is None, "synthetic/test input must not carry a real-source authorization manifest")
        return None, None
    require(auth_path is not None, "real v3.0 mode requires --authorization-manifest")
    auth, auth_raw = load_json(auth_path)
    validate_schema(auth, AUTH_SCHEMA, "real IFC authorization")
    require(auth.get("source_sha256") == source_sha, "authorization/source SHA-256 mismatch")
    require(auth.get("synthetic") is False, "real authorization cannot mark source synthetic")
    return sha256_bytes(auth_raw), auth_raw


def _validate_identity_policy(entries: list[dict[str, Any]], policy: dict[str, Any]) -> None:
    ids = policy["identity_policy"]
    step_ids: set[int] = set()
    global_ids: set[str] = set()
    for entry in entries:
        step_id = entry["step_id"]
        require(step_id not in step_ids, f"duplicate inventory STEP id: {step_id}")
        step_ids.add(step_id)
        global_id = entry["global_id"]
        if global_id:
            require(global_id not in global_ids, f"duplicate non-empty GlobalId: {global_id}")
            global_ids.add(global_id)
        else:
            require(ids.get("allow_missing_global_id") is True, f"missing GlobalId rejected: STEP #{step_id}")


def _identity_set_sha(entries: list[dict[str, Any]]) -> str:
    identities = [
        {
            "source_sha256": entry["source_sha256"],
            "step_id": entry["step_id"],
            "global_id": entry["global_id"],
            "ifc_type": entry["ifc_type"],
            "classification_state": entry["classification_state"],
        }
        for entry in entries
    ]
    return sha256_bytes(canonical_json_bytes(identities))


def build_records(
    ifc_path: Path,
    policy_path: Path,
    *,
    synthetic_input: bool,
    authorization_manifest: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    ifc_path = Path(ifc_path)
    require(ifc_path.is_file(), f"IFC file not found: {ifc_path}")
    require(ifc_path.suffix.lower() == ".ifc", "v3.0 accepts .ifc STEP files only")
    source_raw = ifc_path.read_bytes()

    policy, policy_raw = load_json(Path(policy_path))
    _validate_policy(policy)
    max_source = int(policy["resource_limits"]["max_source_bytes"])
    require(0 < len(source_raw) <= max_source, f"IFC source size outside policy budget: {len(source_raw)}")
    source_sha = sha256_bytes(source_raw)
    policy_sha = sha256_bytes(policy_raw)
    authorization_sha, _ = _validate_authorization(
        authorization_manifest, source_sha, synthetic_input
    )

    max_records = int(policy["resource_limits"]["max_step_records"])
    step_records = _scan_step_records(source_raw, max_records)

    try:
        import ifcopenshell  # type: ignore
    except ImportError as exc:
        raise ModelInventoryError("IfcOpenShell is required; install requirements-proofgrid.txt") from exc
    try:
        model = ifcopenshell.open(str(ifc_path))
    except Exception as exc:
        raise ModelInventoryError(f"unable to parse IFC file: {exc}") from exc

    schema = str(getattr(model, "schema", "unknown"))
    require(schema and schema.lower() != "unknown", "IFC schema could not be resolved")
    adapter_version = str(getattr(ifcopenshell, "version", "unknown"))
    require(adapter_version != "unknown", "IfcOpenShell version could not be resolved")

    project_units = _project_unit_map(model)
    entities = _enumerated_entities(model, policy)
    max_relationships = int(policy["resource_limits"]["max_relationships_per_entry"])
    entries: list[dict[str, Any]] = []
    for entity in entities:
        state, reason = _classification(entity, policy)
        entries.append(
            {
                "source_sha256": source_sha,
                "step_id": int(entity.id()),
                "global_id": _string(getattr(entity, "GlobalId", None)),
                "ifc_type": str(entity.is_a()),
                "name": _string(getattr(entity, "Name", None)),
                "classification_state": state,
                "classification_reason": reason,
                "containment": _containment_rows(entity, max_relationships),
                "decomposition": _decomposition_rows(entity, max_relationships),
                "material_associations": _material_rows(entity, max_relationships),
                "declared_quantities": _quantity_rows(
                    entity, project_units, step_records, max_relationships
                ),
            }
        )
    entries.sort(key=lambda entry: entry["step_id"])
    _validate_identity_policy(entries, policy)

    enumerated_count = len(entities)
    classified_count = len(entries)
    require(
        enumerated_count == classified_count,
        f"silent-drop invariant failed: enumerated={enumerated_count}, classified={classified_count}",
    )
    counts = {
        "EVIDENCE_REQUIRED": 0,
        "EVIDENCE_NOT_APPLICABLE": 0,
        "OUT_OF_DECLARED_EVIDENCE_SCOPE": 0,
    }
    for entry in entries:
        counts[entry["classification_state"]] += 1
    require(sum(counts.values()) == enumerated_count, "every enumerated object must be classified exactly once")

    admission = {
        "schema_version": "3.0",
        "record_type": "ProofGridModelAdmission",
        "verdict": "MODEL_BYTES_PINNED_TEST_ONLY" if synthetic_input else "MODEL_BYTES_PINNED",
        "source_sha256": source_sha,
        "source_size_bytes": len(source_raw),
        "ifc_schema": schema,
        "adapter": {"name": "ifcopenshell", "version": adapter_version},
        "inventory_policy_sha256": policy_sha,
        "authorization_manifest_sha256": authorization_sha,
        "network_resolution": "FORBIDDEN",
        "source_path_is_authority": False,
        "synthetic_input": synthetic_input,
        "acceptance_eligible": not synthetic_input,
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    admission["integrity"]["content_sha256"] = _self_hash(admission)
    validate_schema(admission, ADMISSION_SCHEMA, "v3.0 model admission")

    basis = {
        "schema_version": "3.0",
        "record_type": "ProofGridModelInventoryBasis",
        "verdict": (
            "MODEL_INVENTORY_BASIS_TEST_ONLY"
            if synthetic_input
            else "MODEL_INVENTORY_BASIS_CLOSED_FOR_POLICY"
        ),
        "source": {
            "sha256": source_sha,
            "size_bytes": len(source_raw),
            "ifc_schema": schema,
            "adapter_name": "ifcopenshell",
            "adapter_version": adapter_version,
        },
        "inventory_policy_sha256": policy_sha,
        "authorization_manifest_sha256": authorization_sha,
        "inventory_summary": {
            "enumerated_count": enumerated_count,
            "classified_count": classified_count,
            "evidence_required_count": counts["EVIDENCE_REQUIRED"],
            "evidence_not_applicable_count": counts["EVIDENCE_NOT_APPLICABLE"],
            "out_of_declared_scope_count": counts["OUT_OF_DECLARED_EVIDENCE_SCOPE"],
        },
        "entries": entries,
        "identity_set_sha256": _identity_set_sha(entries),
        "zero_silent_drops": True,
        "synthetic_input": synthetic_input,
        "acceptance_eligible": not synthetic_input,
        "whole_building_lca_claimed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This inventory basis is complete only for the exact IFC revision under the exact inventory policy SHA-256.",
            "Policy closure does not establish a complete building LCA, environmental evidence coverage, scientific validity, professional review, regulatory acceptance, or certification.",
            "Declared quantity source lexical tokens are authority; parser numeric values are consistency evidence only.",
            "No source path, filename, fuzzy mapping, missing-as-zero rule, unit conversion, or scenario inference is evidentiary authority.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    basis["integrity"]["content_sha256"] = _self_hash(basis)
    validate_schema(basis, BASIS_SCHEMA, "v3.0 model inventory basis")

    basis_raw = pretty_json_bytes(basis)
    receipt = {
        "verdict": basis["verdict"],
        "source_sha256": source_sha,
        "inventory_policy_sha256": policy_sha,
        "authorization_manifest_sha256": authorization_sha,
        "model_admission_content_sha256": admission["integrity"]["content_sha256"],
        "inventory_record_content_sha256": basis["integrity"]["content_sha256"],
        "inventory_record_file_sha256": sha256_bytes(basis_raw),
        "identity_set_sha256": basis["identity_set_sha256"],
        "enumerated_count": enumerated_count,
        "classified_count": classified_count,
        "zero_silent_drops": True,
        "synthetic_input": synthetic_input,
        "acceptance_eligible": not synthetic_input,
        "whole_building_lca_claimed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return admission, basis, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rx-model-inventory-v30",
        description="Build a policy-closed IFC model inventory basis with exact source identity.",
    )
    parser.add_argument("--ifc", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=POLICY_SCHEMA_PATH,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-test-input", action="store_true")
    mode.add_argument("--real-authorized-input", action="store_true")
    parser.add_argument("--authorization-manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    synthetic = bool(args.synthetic_test_input)
    if args.real_authorized_input and args.authorization_manifest is None:
        parser.error("--real-authorized-input requires --authorization-manifest")
    if synthetic and args.authorization_manifest is not None:
        parser.error("--synthetic-test-input cannot use --authorization-manifest")

    try:
        admission, basis, receipt = build_records(
            args.ifc,
            args.policy,
            synthetic_input=synthetic,
            authorization_manifest=args.authorization_manifest,
        )
    except ModelInventoryError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "model-admission.json").write_bytes(pretty_json_bytes(admission))
    (args.output_dir / "model-inventory-basis.json").write_bytes(pretty_json_bytes(basis))
    (args.output_dir / "model-inventory-basis-receipt.json").write_bytes(
        pretty_json_bytes(receipt)
    )
    print(f"RESULT: {basis['verdict']}")
    print(f"SOURCE_SHA256: {basis['source']['sha256']}")
    print(f"INVENTORY_COUNT: {basis['inventory_summary']['enumerated_count']}")
    print(f"IDENTITY_SET_SHA256: {basis['identity_set_sha256']}")
    print(f"ACCEPTANCE_ELIGIBLE: {str(basis['acceptance_eligible']).lower()}")
    print("WHOLE_BUILDING_LCA: false")
    print("CERTIFIED: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
