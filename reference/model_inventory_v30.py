#!/usr/bin/env python3
"""ProofGrid v3.0 authoritative IFC model-inventory engine.

The production verdict is unreachable unless the input is a native .ifc file
with USER_AUTHORIZED_REAL_IFC authorization and the immutable inventory policy
closes with zero silent drops. Synthetic fixtures can emit only the explicit
preflight verdict.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import re
import socket
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
AUTH_SCHEMA = ROOT / "schemas" / "model-source-authorization-v30.schema.json"
BASIS_SCHEMA = ROOT / "schemas" / "model-inventory-basis-v30.schema.json"
DEFAULT_POLICY = ROOT / "policies" / "inventory-policy-v30.json"
REAL_VERDICT = "MODEL_INVENTORY_BASIS_CLOSED_FOR_POLICY"
PREFLIGHT_VERDICT = "V30_ENGINE_PREFLIGHT_VERIFIABLE"
REAL_AUTH = "USER_AUTHORIZED_REAL_IFC"
PREFLIGHT_AUTH = "SYNTHETIC_TEST_FIXTURE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO = "0" * 64
EXPECTED_POLICY_SHA256 = "67b1da24c5ec579942d2d21919dcc688f28ee0bf1057d18f93aba2bf9aab500b"
SUPPORTED_QTYPES = {
    "IFCQUANTITYLENGTH": ("LengthValue", "LENGTHUNIT"),
    "IFCQUANTITYAREA": ("AreaValue", "AREAUNIT"),
    "IFCQUANTITYVOLUME": ("VolumeValue", "VOLUMEUNIT"),
    "IFCQUANTITYWEIGHT": ("WeightValue", "MASSUNIT"),
    "IFCQUANTITYCOUNT": ("CountValue", None),
    "IFCQUANTITYTIME": ("TimeValue", "TIMEUNIT"),
}


class InventoryError(ValueError):
    pass


class NetworkEscapeAttempt(InventoryError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise InventoryError(msg)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = Path(path).read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    require(isinstance(obj, dict), f"expected JSON object: {path}")
    return obj, raw


def validate_schema(obj: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise InventoryError(f"invalid {label} schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(obj), key=lambda e: list(e.path))
    if errors:
        preview = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6])
        raise InventoryError(f"{label} failed schema validation: {preview}")


def policy_hash(policy_raw: bytes) -> str:
    return sha256_bytes(policy_raw)


def validate_policy(policy: dict[str, Any]) -> None:
    require(policy.get("schema_version") == "1.0", "policy schema version mismatch")
    require(policy.get("policy_version") == "3.0.0", "policy version mismatch")
    source = policy.get("source_requirements", {})
    require(source.get("native_ifc_required") is True, "native IFC requirement missing")
    require(source.get("user_authorized_real_ifc_required") is True, "real IFC authorization requirement missing")
    require(source.get("synthetic_source_may_close_gate") is False, "synthetic source cannot close production gate")
    require(source.get("reconstructed_source_may_close_gate") is False, "reconstructed source cannot close production gate")
    enum = policy.get("enumeration", {})
    require(enum.get("roots") == ["IfcProduct"], "v3.0 enumeration root must be IfcProduct")
    require(enum.get("zero_silent_drops_required") is True, "zero silent drops policy missing")
    identity = policy.get("identity", {})
    require(identity.get("duplicate_source_step_policy") == "REJECT", "duplicate STEP must reject")
    require(identity.get("duplicate_nonempty_global_id_policy") == "REJECT", "duplicate GlobalId must reject")
    capture = policy.get("capture", {})
    require(capture.get("exact_step_quantity_lexical_tokens") is True, "exact STEP quantity policy missing")
    require(capture.get("parser_numeric_values_are_authority") is False, "parser numeric values cannot be authority")
    require(capture.get("source_step_tokens_are_authority") is True, "source STEP tokens must be authority")
    network = policy.get("network_policy", {})
    require(network.get("remote_resolution_allowed") is False, "remote resolution must be disabled")
    require(network.get("local_source_only") is True, "model parsing must be local-source only")


def validate_authorization(auth: dict[str, Any], *, preflight: bool) -> str:
    validate_schema(auth, AUTH_SCHEMA, "source authorization")
    classification = auth["source_classification"]
    if preflight:
        require(classification == PREFLIGHT_AUTH, "preflight requires SYNTHETIC_TEST_FIXTURE authorization")
        require(auth["synthetic"] is True, "preflight source must be marked synthetic")
        require(auth["reconstructed"] is False, "preflight source cannot be reconstructed")
        return PREFLIGHT_VERDICT
    require(classification == REAL_AUTH, "production closure requires USER_AUTHORIZED_REAL_IFC")
    require(auth["user_authorized"] is True, "real IFC must be user-authorized")
    require(auth["synthetic"] is False, "real production source cannot be synthetic")
    require(auth["reconstructed"] is False, "real production source cannot be reconstructed")
    return REAL_VERDICT


@contextlib.contextmanager
def deny_python_network() -> Iterator[None]:
    original_connect = socket.socket.connect
    original_create = socket.create_connection

    def blocked_connect(*args, **kwargs):
        raise NetworkEscapeAttempt("network access attempted during local IFC parse")

    def blocked_create(*args, **kwargs):
        raise NetworkEscapeAttempt("network access attempted during local IFC parse")

    socket.socket.connect = blocked_connect  # type: ignore[assignment]
    socket.create_connection = blocked_create  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = original_connect  # type: ignore[assignment]
        socket.create_connection = original_create  # type: ignore[assignment]


def schema_family(schema: str) -> str:
    upper = str(schema).upper()
    if upper.startswith("IFC4X3"):
        return "IFC4X3"
    if upper.startswith("IFC4"):
        return "IFC4"
    if upper.startswith("IFC2X3"):
        return "IFC2X3"
    return upper


def _split_step_args(text: str) -> list[str]:
    args: list[str] = []
    buf: list[str] = []
    depth = 0
    quoted = False
    i = 0
    while i < len(text):
        ch = text[i]
        if quoted:
            buf.append(ch)
            if ch == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    buf.append(text[i + 1])
                    i += 1
                else:
                    quoted = False
        else:
            if ch == "'":
                quoted = True
                buf.append(ch)
            elif ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                require(depth >= 0, "unbalanced STEP argument parentheses")
                buf.append(ch)
            elif ch == "," and depth == 0:
                args.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        i += 1
    require(not quoted and depth == 0, "unterminated STEP argument structure")
    args.append("".join(buf).strip())
    return args


def step_records(raw_text: str, max_chars: int) -> dict[int, tuple[str, str]]:
    records: dict[int, tuple[str, str]] = {}
    active_id: int | None = None
    buffer: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if active_id is None:
            match = re.match(r"^#(\d+)\s*=\s*", stripped, re.I)
            if not match:
                continue
            active_id = int(match.group(1))
            buffer = [stripped]
        else:
            buffer.append(stripped)
        joined = "".join(buffer)
        require(len(joined) <= max_chars, f"STEP record exceeds max_step_record_chars at #{active_id}")
        if joined.endswith(";"):
            require(active_id not in records, f"duplicate STEP record #{active_id}")
            rhs = joined.split("=", 1)[1][:-1].strip()
            parsed = re.match(r"^([A-Z0-9_]+)\((.*)\)$", rhs, re.I | re.S)
            if parsed:
                records[active_id] = (parsed.group(1).upper(), parsed.group(2))
            active_id = None
            buffer = []
    require(active_id is None, "unterminated STEP record")
    return records


def exact_quantity_token(records: dict[int, tuple[str, str]], quantity_step_id: int, ifc_type: str) -> str | None:
    item = records.get(int(quantity_step_id))
    require(item is not None, f"quantity STEP record #{quantity_step_id} missing from source bytes")
    entity, args_text = item
    require(entity == str(ifc_type).upper(), f"quantity STEP entity mismatch for #{quantity_step_id}")
    if entity not in SUPPORTED_QTYPES:
        return None
    args = _split_step_args(args_text)
    require(len(args) >= 4, f"quantity STEP record #{quantity_step_id} has too few arguments")
    token = args[3].strip()
    require(token not in {"", "$", "*"}, f"quantity STEP token missing for #{quantity_step_id}")
    return token


def verify_lexical_parser_consistency(lexical: str, parser_value: Any, quantity_step_id: int) -> bool:
    try:
        consistent = Decimal(lexical) == Decimal(str(float(parser_value)))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InventoryError(f"invalid exact quantity token at #{quantity_step_id}: {lexical}") from exc
    require(consistent, f"exact lexical/parser quantity mismatch at #{quantity_step_id}")
    return True


def enforce_resource_counts(*, file_bytes: int, total_entities: int, products: int, limits: dict[str, int]) -> None:
    require(file_bytes <= limits["max_file_bytes"], "IFC file exceeds max_file_bytes")
    require(total_entities <= limits["max_total_entities"], "total IFC entity budget exceeded")
    require(products <= limits["max_enumerated_products"], "enumerated product budget exceeded")


def unit_summary(unit: Any) -> dict[str, Any] | None:
    if unit is None:
        return None
    return {
        "step_id": int(unit.id()),
        "ifc_type": str(unit.is_a()),
        "unit_type": None if getattr(unit, "UnitType", None) is None else str(unit.UnitType),
        "name": None if getattr(unit, "Name", None) is None else str(unit.Name),
        "prefix": None if getattr(unit, "Prefix", None) is None else str(unit.Prefix),
    }


def project_units(model: Any) -> dict[str, dict[str, Any]]:
    projects = list(model.by_type("IfcProject"))
    if not projects or getattr(projects[0], "UnitsInContext", None) is None:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for unit in list(projects[0].UnitsInContext.Units or ()):
        summary = unit_summary(unit)
        if summary and summary["unit_type"] and summary["unit_type"] not in out:
            out[summary["unit_type"]] = summary
    return out


def material_entries(product: Any, max_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in list(getattr(product, "HasAssociations", None) or ()):
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        material = getattr(rel, "RelatingMaterial", None)
        rows.append({
            "association_step_id": int(rel.id()),
            "relating_material_step_id": int(material.id()) if material is not None else None,
            "relating_material_type": str(material.is_a()) if material is not None else None,
            "declared_name": str(getattr(material, "Name", None)) if material is not None and getattr(material, "Name", None) is not None else None,
        })
        require(len(rows) <= max_count, f"material association count exceeds policy for product #{product.id()}")
    return rows


def quantity_entries(product: Any, units: dict[str, dict[str, Any]], records: dict[int, tuple[str, str]], max_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in list(getattr(product, "IsDefinedBy", None) or ()):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        qset = getattr(rel, "RelatingPropertyDefinition", None)
        if qset is None or not qset.is_a("IfcElementQuantity"):
            continue
        for quantity in list(getattr(qset, "Quantities", None) or ()):
            qtype = str(quantity.is_a())
            upper = qtype.upper()
            unit_type = SUPPORTED_QTYPES.get(upper, (None, None))[1]
            explicit = unit_summary(getattr(quantity, "Unit", None))
            unit = explicit or (copy.deepcopy(units.get(unit_type)) if unit_type else None)
            if unit is not None:
                unit["source"] = "explicit_quantity_unit" if explicit else "project_unit_context"
            value_attr = SUPPORTED_QTYPES.get(upper, (None, None))[0]
            parser_value = None if value_attr is None else getattr(quantity, value_attr, None)
            lexical = exact_quantity_token(records, int(quantity.id()), qtype) if upper in SUPPORTED_QTYPES else None
            parser_consistent = None
            if lexical is not None and parser_value is not None:
                parser_consistent = verify_lexical_parser_consistency(lexical, parser_value, int(quantity.id()))
            rows.append({
                "set_step_id": int(qset.id()),
                "set_name": None if getattr(qset, "Name", None) is None else str(qset.Name),
                "quantity_step_id": int(quantity.id()),
                "quantity_name": None if getattr(quantity, "Name", None) is None else str(quantity.Name),
                "ifc_quantity_type": qtype,
                "quantity_lexical": lexical,
                "source_token_is_authority": lexical is not None,
                "parser_numeric_value": None if parser_value is None else float(parser_value),
                "parser_numeric_value_is_authority": False,
                "parser_consistent_with_source": parser_consistent,
                "unit": unit,
            })
            require(len(rows) <= max_count, f"quantity count exceeds policy for product #{product.id()}")
    return rows


def parent_refs(product: Any) -> dict[str, list[dict[str, Any]]]:
    containment: list[dict[str, Any]] = []
    for rel in list(getattr(product, "ContainedInStructure", None) or ()):
        parent = getattr(rel, "RelatingStructure", None)
        if parent is not None:
            containment.append({
                "relationship_step_id": int(rel.id()),
                "parent_step_id": int(parent.id()),
                "parent_global_id": None if getattr(parent, "GlobalId", None) is None else str(parent.GlobalId),
                "parent_ifc_type": str(parent.is_a()),
            })
    decomposition: list[dict[str, Any]] = []
    for rel in list(getattr(product, "Decomposes", None) or ()):
        parent = getattr(rel, "RelatingObject", None)
        if parent is not None:
            decomposition.append({
                "relationship_step_id": int(rel.id()),
                "parent_step_id": int(parent.id()),
                "parent_global_id": None if getattr(parent, "GlobalId", None) is None else str(parent.GlobalId),
                "parent_ifc_type": str(parent.is_a()),
            })
    return {
        "containment": sorted(containment, key=lambda x: x["relationship_step_id"]),
        "decomposition": sorted(decomposition, key=lambda x: x["relationship_step_id"]),
    }


def classify(product: Any, policy: dict[str, Any]) -> tuple[str, str | None]:
    typ = str(product.is_a())
    cls = policy["classification"]
    if typ in cls["evidence_not_applicable_types"]:
        return "EVIDENCE_NOT_APPLICABLE", cls["not_applicable_reason_by_type"][typ]
    if product.is_a("IfcElement"):
        return "EVIDENCE_REQUIRED", None
    return "OUT_OF_DECLARED_EVIDENCE_SCOPE", cls["out_of_scope_reason_for_non_element_product"]


def validate_basis(record: dict[str, Any]) -> None:
    validate_schema(record, BASIS_SCHEMA, "ModelInventoryBasis")
    inv = record["inventory"]
    entries = inv["entries"]
    require(inv["enumerated_count"] == len(entries), "inventory count mismatch")
    require(record["closure"]["parser_enumerated_count"] == len(entries), "parser/final count mismatch")
    require(record["closure"]["silent_drop_count"] == 0, "silent drops detected")
    require(record["closure"]["every_enumerated_object_classified_exactly_once"] is True, "classification closure missing")
    steps = [(e["source_sha256"], e["step_id"]) for e in entries]
    require(len(steps) == len(set(steps)), "duplicate source/STEP identity")
    gids = [e["global_id"] for e in entries if e["global_id"]]
    require(len(gids) == len(set(gids)), "duplicate non-empty GlobalId")
    allowed = {"EVIDENCE_REQUIRED", "EVIDENCE_NOT_APPLICABLE", "OUT_OF_DECLARED_EVIDENCE_SCOPE"}
    for entry in entries:
        require(entry["policy_state"] in allowed, "invalid policy state")
        if entry["policy_state"] != "EVIDENCE_REQUIRED":
            require(bool(entry["policy_reason"]), "non-required state missing reason")
    for key in ("whole_building_lca_claimed", "scientific_validation_performed", "professional_review_performed", "regulator_accepted", "certified"):
        require(record["claims"][key] is False, f"{key} promotion rejected")
    if record["verdict"] == REAL_VERDICT:
        require(record["production_gate_satisfied"] is True, "real verdict requires production gate")
        require(record["authorization"]["source_classification"] == REAL_AUTH, "real verdict requires real authorization")
    else:
        require(record["verdict"] == PREFLIGHT_VERDICT, "unexpected non-production verdict")
        require(record["production_gate_satisfied"] is False, "preflight cannot satisfy production gate")


def build_inventory(ifc_path: Path, policy_path: Path, auth_path: Path, *, preflight: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    ifc_path = Path(ifc_path)
    require(ifc_path.suffix.lower() == ".ifc", "native .ifc file required")
    policy, policy_raw = load_json(policy_path)
    validate_policy(policy)
    auth, auth_raw = load_json(auth_path)
    verdict = validate_authorization(auth, preflight=preflight)
    source_raw = ifc_path.read_bytes()
    limits = policy["resource_limits"]
    enforce_resource_counts(file_bytes=len(source_raw), total_entities=0, products=0, limits=limits)
    source_sha = sha256_bytes(source_raw)
    raw_text = source_raw.decode("utf-8", errors="strict")
    records = step_records(raw_text, limits["max_step_record_chars"])

    try:
        import ifcopenshell  # type: ignore
    except ImportError as exc:
        raise InventoryError("IfcOpenShell is required") from exc
    with deny_python_network():
        try:
            model = ifcopenshell.open(str(ifc_path))
        except NetworkEscapeAttempt:
            raise
        except Exception as exc:
            raise InventoryError(f"unable to parse IFC: {exc}") from exc
    schema = str(getattr(model, "schema", "unknown"))
    family = schema_family(schema)
    require(family in policy["source_requirements"]["allowed_schema_families"], f"unsupported IFC schema family: {schema}")
    total_entities = len(list(model))
    products = list(model.by_type("IfcProduct"))
    enforce_resource_counts(file_bytes=len(source_raw), total_entities=total_entities, products=len(products), limits=limits)
    units = project_units(model)

    step_seen: set[int] = set()
    gid_seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    counts = {key: 0 for key in ("EVIDENCE_REQUIRED", "EVIDENCE_NOT_APPLICABLE", "OUT_OF_DECLARED_EVIDENCE_SCOPE")}
    for product in products:
        step = int(product.id())
        require(step not in step_seen, f"duplicate product STEP ID: {step}")
        step_seen.add(step)
        gid_value = getattr(product, "GlobalId", None)
        gid = "" if gid_value is None else str(gid_value)
        require(bool(gid), f"enumerated product #{step} missing GlobalId")
        require(gid not in gid_seen, f"duplicate non-empty GlobalId: {gid}")
        gid_seen.add(gid)
        state, reason = classify(product, policy)
        counts[state] += 1
        parents = parent_refs(product)
        entries.append({
            "source_sha256": source_sha,
            "step_id": step,
            "global_id": gid,
            "ifc_type": str(product.is_a()),
            "name": None if getattr(product, "Name", None) is None else str(product.Name),
            "policy_state": state,
            "policy_reason": reason,
            "containment": parents["containment"],
            "decomposition": parents["decomposition"],
            "material_associations": material_entries(product, limits["max_material_associations_per_product"]),
            "declared_quantities": quantity_entries(product, units, records, limits["max_quantities_per_product"]),
        })
    entries.sort(key=lambda e: e["step_id"])
    identity_rows = [{"source_sha256": e["source_sha256"], "step_id": e["step_id"], "global_id": e["global_id"], "ifc_type": e["ifc_type"]} for e in entries]
    identity_set_sha = sha256_bytes(canonical_json_bytes(identity_rows))
    psha = policy_hash(policy_raw)
    require(psha == EXPECTED_POLICY_SHA256, "inventory policy SHA-256 drift rejected")
    authorization_digest = sha256_bytes(auth_raw)

    admission = {
        "verdict": "MODEL_BYTES_PINNED" if verdict == REAL_VERDICT else "PREFLIGHT_MODEL_BYTES_PINNED",
        "source_sha256": source_sha,
        "source_file_bytes": len(source_raw),
        "ifc_schema": schema,
        "ifc_schema_family": family,
        "parser": {"name": "IfcOpenShell", "version": str(getattr(ifcopenshell, "version", "unknown"))},
        "policy_sha256": psha,
        "authorization_sha256": authorization_digest,
        "source_classification": auth["source_classification"],
        "network_access_performed": False,
        "production_gate_satisfied": verdict == REAL_VERDICT,
    }
    admission["receipt_sha256"] = sha256_bytes(canonical_json_bytes(admission))

    basis = {
        "schema_version": "1.0",
        "record_type": "ProofGridModelInventoryBasis",
        "verdict": verdict,
        "production_gate_satisfied": verdict == REAL_VERDICT,
        "source": {
            "sha256": source_sha,
            "file_bytes": len(source_raw),
            "ifc_schema": schema,
            "ifc_schema_family": family,
            "parser": admission["parser"],
            "network_access_performed": False,
        },
        "policy": {"policy_id": policy["policy_id"], "policy_version": policy["policy_version"], "sha256": psha},
        "authorization": {
            "source_classification": auth["source_classification"],
            "user_authorized": auth["user_authorized"],
            "synthetic": auth["synthetic"],
            "reconstructed": auth["reconstructed"],
            "authorization_reference": auth["authorization_reference"],
            "authorization_sha256": authorization_digest,
        },
        "inventory": {
            "enumeration_root": "IfcProduct",
            "enumerated_count": len(entries),
            "classification_counts": counts,
            "identity_set_sha256": identity_set_sha,
            "entries": entries,
        },
        "closure": {
            "parser_total_entity_count": total_entities,
            "parser_enumerated_count": len(products),
            "final_inventory_count": len(entries),
            "silent_drop_count": len(products) - len(entries),
            "duplicate_source_step_count": 0,
            "duplicate_nonempty_global_id_count": 0,
            "every_enumerated_object_classified_exactly_once": True,
        },
        "claims": {
            "model_inventory_basis_closed_for_policy": verdict == REAL_VERDICT,
            "whole_building_lca_claimed": False,
            "scientific_validation_performed": False,
            "professional_review_performed": False,
            "regulator_accepted": False,
            "certified": False,
        },
        "limitations": [
            "Inventory closure is relative only to the exact IFC bytes and immutable inventory policy recorded here.",
            "Synthetic preflight fixtures cannot satisfy the production real-model gate.",
            "Model-inventory closure does not establish complete-building LCA, environmental evidence coverage, scientific validity, professional review, regulator acceptance, or certification.",
        ],
        "integrity": {"content_sha256": ZERO, "canonicalization": CANONICALIZATION, "signature": None},
    }
    basis["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(basis))
    validate_basis(basis)
    return admission, basis


def write_outputs(admission: dict[str, Any], basis: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    admission_path = output_dir / "model-admission-receipt.json"
    basis_path = output_dir / "model-inventory-basis.json"
    basis_receipt_path = output_dir / "model-inventory-basis-receipt.json"
    admission_raw = pretty_json_bytes(admission)
    basis_raw = pretty_json_bytes(basis)
    admission_path.write_bytes(admission_raw)
    basis_path.write_bytes(basis_raw)
    receipt = {
        "verdict": basis["verdict"],
        "production_gate_satisfied": basis["production_gate_satisfied"],
        "source_sha256": basis["source"]["sha256"],
        "policy_sha256": basis["policy"]["sha256"],
        "authorization_sha256": basis["authorization"]["authorization_sha256"],
        "inventory_count": basis["inventory"]["enumerated_count"],
        "inventory_identity_set_sha256": basis["inventory"]["identity_set_sha256"],
        "record_content_sha256": basis["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(basis_raw),
        "model_admission_receipt_sha256": admission["receipt_sha256"],
        "model_admission_file_sha256": sha256_bytes(admission_raw),
        "silent_drop_count": basis["closure"]["silent_drop_count"],
        "whole_building_lca_claimed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "regulator_accepted": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    basis_receipt_path.write_bytes(pretty_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifc", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    try:
        admission, basis = build_inventory(args.ifc, args.policy, args.authorization, preflight=args.preflight)
        receipt = write_outputs(admission, basis, args.output_dir)
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 2
    print(f"RESULT: {basis['verdict']}")
    print(f"SOURCE_SHA256={basis['source']['sha256']}")
    print(f"POLICY_SHA256={basis['policy']['sha256']}")
    print(f"INVENTORY_COUNT={basis['inventory']['enumerated_count']}")
    print(f"IDENTITY_SET_SHA256={basis['inventory']['identity_set_sha256']}")
    print(f"PRODUCTION_GATE_SATISFIED={str(basis['production_gate_satisfied']).lower()}")
    print(f"RECEIPT_SHA256={receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
