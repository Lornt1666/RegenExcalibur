#!/usr/bin/env python3
"""ProofGrid v3.2 exact semantic-neighborhood probe for one real IFC candidate.

This module mines source evidence. It does not map names to environmental data
and does not infer concrete strength from abbreviations such as STB, Ortbeton,
or reinforced concrete. Literal strength-class observations are reported only
when the exact source strings contain them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element

from reference.model_inventory_v30 import exact_quantity_token, step_records

ENGINE_NAME = "RegenExcalibur ProofGrid Real IFC Suitability Semantic Probe"
ENGINE_VERSION = "3.2.0"
VERDICT = "REAL_MODEL_ENVIRONMENTAL_SOURCE_SUITABILITY_EVIDENCE_PROBE_VERIFIABLE"
SOURCE_SHA256 = "19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb"
SOURCE_BYTES = 9022255
STEP_ID = 9730
GLOBAL_ID = "3BmeJtEDj3AQO77Os2w7Ny"
IFC_TYPE = "IfcColumn"
MATERIAL_REL_STEP = 271324
MATERIAL_STEP = 9711
MATERIAL_NAME = "Ortbeton - bewehrt"
QSET_STEP = 9738
NET_VOLUME_STEP = 9737
NET_VOLUME_LEXICAL = "0.365000000000004"
NET_VOLUME_UNIT = "CUBIC_METRE"

class ProbeError(ValueError):
    pass

def require(cond: bool, msg: str) -> None:
    if not cond:
        raise ProbeError(msg)

def cbytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def pbytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [scalar(x) for x in value]
    if isinstance(value, dict):
        return {str(k): scalar(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if hasattr(value, "id") and hasattr(value, "is_a"):
        return {"step_id": int(value.id()), "ifc_type": str(value.is_a())}
    return str(value)

def entity_attributes(entity: Any) -> dict[str, Any]:
    info = entity.get_info(recursive=False)
    excluded = {"id", "type", "OwnerHistory", "ObjectPlacement", "Representation"}
    out = {k: scalar(v) for k, v in info.items() if k not in excluded and v is not None}
    return dict(sorted(out.items()))

def collect_strings(value: Any, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, str):
        found.append({"path": path or "$", "value": value})
    elif isinstance(value, dict):
        for k in sorted(value):
            found.extend(collect_strings(value[k], f"{path}.{k}" if path else str(k)))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(collect_strings(v, f"{path}[{i}]"))
    return found

def psets_for(element: Any, *, inherit: bool) -> dict[str, Any]:
    try:
        psets = ifcopenshell.util.element.get_psets(
            element, psets_only=False, qtos_only=False,
            should_inherit=inherit, verbose=True,
        )
    except TypeError:
        psets = ifcopenshell.util.element.get_psets(element, should_inherit=inherit)
    return scalar(psets)

def direct_material_associations(element: Any) -> list[dict[str, Any]]:
    rows = []
    for rel in getattr(element, "HasAssociations", ()) or ():
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        mat = rel.RelatingMaterial
        row = {
            "relationship_step_id": int(rel.id()),
            "relating_material_step_id": int(mat.id()),
            "relating_material_type": str(mat.is_a()),
            "material_attributes": entity_attributes(mat),
        }
        rows.append(row)
    rows.sort(key=lambda r: r["relationship_step_id"])
    return rows

def classification_associations(element: Any) -> list[dict[str, Any]]:
    rows = []
    for rel in getattr(element, "HasAssociations", ()) or ():
        if not rel.is_a("IfcRelAssociatesClassification"):
            continue
        cls = rel.RelatingClassification
        rows.append({
            "relationship_step_id": int(rel.id()),
            "classification_step_id": int(cls.id()),
            "classification_type": str(cls.is_a()),
            "classification_attributes": entity_attributes(cls),
        })
    rows.sort(key=lambda r: r["relationship_step_id"])
    return rows

def type_relations(element: Any) -> list[dict[str, Any]]:
    rows = []
    relations = list(getattr(element, "IsTypedBy", ()) or ())
    if not relations:
        for rel in getattr(element, "IsDefinedBy", ()) or ():
            if rel.is_a("IfcRelDefinesByType"):
                relations.append(rel)
    for rel in relations:
        typ = rel.RelatingType
        rows.append({
            "relationship_step_id": int(rel.id()),
            "type_step_id": int(typ.id()),
            "type_ifc_type": str(typ.is_a()),
            "type_attributes": entity_attributes(typ),
            "type_property_sets": psets_for(typ, inherit=False),
            "type_classifications": classification_associations(typ),
            "type_material_associations": direct_material_associations(typ),
        })
    rows.sort(key=lambda r: r["relationship_step_id"])
    return rows

def direct_property_relationships(element: Any) -> list[dict[str, Any]]:
    rows = []
    for rel in getattr(element, "IsDefinedBy", ()) or ():
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        propdef = rel.RelatingPropertyDefinition
        rows.append({
            "relationship_step_id": int(rel.id()),
            "property_definition_step_id": int(propdef.id()),
            "property_definition_type": str(propdef.is_a()),
            "property_definition_attributes": entity_attributes(propdef),
        })
    rows.sort(key=lambda r: r["relationship_step_id"])
    return rows

def containment(element: Any) -> list[dict[str, Any]]:
    rows = []
    for rel in getattr(element, "ContainedInStructure", ()) or ():
        parent = rel.RelatingStructure
        rows.append({
            "relationship_step_id": int(rel.id()),
            "parent_step_id": int(parent.id()),
            "parent_global_id": getattr(parent, "GlobalId", None),
            "parent_ifc_type": str(parent.is_a()),
            "parent_name": getattr(parent, "Name", None),
        })
    rows.sort(key=lambda r: r["relationship_step_id"])
    return rows

def net_volume_evidence(element: Any, source_text: str, max_record_chars: int = 1048576) -> dict[str, Any]:
    records = step_records(source_text, max_record_chars)
    matches = []
    for rel in getattr(element, "IsDefinedBy", ()) or ():
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef.is_a("IfcElementQuantity"):
            continue
        for q in pdef.Quantities:
            if int(q.id()) == NET_VOLUME_STEP:
                token = exact_quantity_token(records, int(q.id()), str(q.is_a()))
                unit = getattr(q, "Unit", None)
                if unit is None:
                    # Resolve project VOLUMEUNIT identity without numeric conversion.
                    project = element.wrapped_data.file.by_type("IfcProject")[0]
                    units = project.UnitsInContext.Units if project.UnitsInContext else ()
                    volume_units = [u for u in units if getattr(u, "UnitType", None) == "VOLUMEUNIT"]
                    require(len(volume_units) == 1, "expected exactly one project VOLUMEUNIT")
                    unit = volume_units[0]
                matches.append({
                    "property_relationship_step_id": int(rel.id()),
                    "quantity_set_step_id": int(pdef.id()),
                    "quantity_set_name": pdef.Name,
                    "quantity_step_id": int(q.id()),
                    "quantity_ifc_type": str(q.is_a()),
                    "quantity_name": q.Name,
                    "quantity_lexical": token,
                    "source_token_is_authority": True,
                    "parser_numeric_value": float(q.VolumeValue),
                    "parser_numeric_value_is_authority": False,
                    "unit_step_id": int(unit.id()),
                    "unit_ifc_type": str(unit.is_a()),
                    "unit_type": getattr(unit, "UnitType", None),
                    "unit_name": getattr(unit, "Name", None),
                    "unit_prefix": getattr(unit, "Prefix", None),
                })
    require(len(matches) == 1, f"expected exactly one NetVolume #9737, found {len(matches)}")
    return matches[0]

def strength_observations(neighborhood: dict[str, Any]) -> dict[str, Any]:
    strings = collect_strings(neighborhood)
    patterns = {
        "C25/30": re.compile(r"(?<![A-Z0-9])C\s*25\s*/\s*30(?![0-9])", re.I),
        "C30/37": re.compile(r"(?<![A-Z0-9])C\s*30\s*/\s*37(?![0-9])", re.I),
    }
    matches: dict[str, list[dict[str, str]]] = {k: [] for k in patterns}
    for item in strings:
        for label, pattern in patterns.items():
            if pattern.search(item["value"]):
                matches[label].append(item)
    return {
        "literal_strength_class_matches": matches,
        "c25_30_present": bool(matches["C25/30"]),
        "c30_37_present": bool(matches["C30/37"]),
        "strength_class_inference_from_stb_or_material_name_allowed": False,
    }

def build(ifc_path: Path) -> dict[str, Any]:
    raw = ifc_path.read_bytes()
    require(ifc_path.suffix.lower() == ".ifc", "native .ifc source required")
    require(len(raw) == SOURCE_BYTES, "real IFC byte-size mismatch")
    require(sha256(raw) == SOURCE_SHA256, "real IFC SHA-256 mismatch")
    text = raw.decode("utf-8")
    model = ifcopenshell.open(str(ifc_path))
    element = model.by_id(STEP_ID)
    require(element is not None and element.is_a(IFC_TYPE), "candidate STEP/type mismatch")
    require(getattr(element, "GlobalId", None) == GLOBAL_ID, "candidate GlobalId mismatch")
    mats = direct_material_associations(element)
    require(any(r["relationship_step_id"] == MATERIAL_REL_STEP and r["relating_material_step_id"] == MATERIAL_STEP and r["material_attributes"].get("Name") == MATERIAL_NAME for r in mats), "candidate material association mismatch")
    volume = net_volume_evidence(element, text)
    require(volume["quantity_set_step_id"] == QSET_STEP, "candidate quantity-set identity mismatch")
    require(volume["quantity_lexical"] == NET_VOLUME_LEXICAL, "candidate NetVolume lexical mismatch")
    require(volume["unit_type"] == "VOLUMEUNIT" and volume["unit_name"] == NET_VOLUME_UNIT and volume["unit_prefix"] is None, "candidate NetVolume unit mismatch")

    neighborhood = {
        "element": {
            "step_id": STEP_ID,
            "global_id": GLOBAL_ID,
            "ifc_type": IFC_TYPE,
            "attributes": entity_attributes(element),
            "direct_property_sets": psets_for(element, inherit=False),
            "inherited_property_sets": psets_for(element, inherit=True),
            "direct_property_relationships": direct_property_relationships(element),
            "type_relations": type_relations(element),
            "material_associations": mats,
            "classification_associations": classification_associations(element),
            "containment": containment(element),
            "net_volume": volume,
        }
    }
    strength = strength_observations(neighborhood)
    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridRealIFCSuitabilitySemanticProbe",
        "verdict": VERDICT,
        "source": {
            "sha256": SOURCE_SHA256,
            "file_bytes": SOURCE_BYTES,
            "upstream_repository": "RWTH-E3D/DigitalHub",
            "upstream_commit": "36565d529b4dadeca625de2b793d7e16700171e9",
            "upstream_path": "Version_2/DigitalHub_FM-ARC_v2.ifc",
        },
        "candidate": neighborhood["element"],
        "strength_class_evidence": strength,
        "authority_boundaries": {
            "fuzzy_name_mapping_allowed": False,
            "strength_class_inference_performed": False,
            "environmental_mapping_performed": False,
            "impact_calculation_performed": False,
            "scientific_suitability_decided": False,
            "professional_review_performed": False,
            "regulator_acceptance_implied": False,
            "certified": False,
        },
    }
    record["integrity"] = {
        "content_sha256": sha256(cbytes(record)),
        "canonicalization": "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false",
        "signature": None,
    }
    return record

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ifc", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        record = build(a.ifc)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(pbytes(record))
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {VERDICT}")
    print("C25_30_PRESENT=" + str(record["strength_class_evidence"]["c25_30_present"]).lower())
    print("C30_37_PRESENT=" + str(record["strength_class_evidence"]["c30_37_present"]).lower())
    print("MAPPING_PERFORMED=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
