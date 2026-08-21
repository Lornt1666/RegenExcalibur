"""Evidence-controlled IFC quantity/material extraction for ProofGrid v0.4.

Only declared IFC relationships/quantities are extracted. No geometry-derived
quantities, environmental-factor mapping, LCA conclusions, code-compliance
conclusions, engineering conclusions, or certification conclusions are produced.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


class IFCExtractionError(ValueError):
    pass


_QUANTITY_TYPES: tuple[tuple[str, str, str | None], ...] = (
    ("IfcQuantityLength", "LengthValue", "LENGTHUNIT"),
    ("IfcQuantityArea", "AreaValue", "AREAUNIT"),
    ("IfcQuantityVolume", "VolumeValue", "VOLUMEUNIT"),
    ("IfcQuantityWeight", "WeightValue", "MASSUNIT"),
    ("IfcQuantityCount", "CountValue", None),
    ("IfcQuantityTime", "TimeValue", "TIMEUNIT"),
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _unit_summary(unit: Any) -> dict[str, Any]:
    return {
        "step_id": int(unit.id()),
        "ifc_type": str(unit.is_a()),
        "unit_type": _string(getattr(unit, "UnitType", None)),
        "name": _string(getattr(unit, "Name", None)),
        "prefix": _string(getattr(unit, "Prefix", None)),
    }


def _project_units(model: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    projects = list(model.by_type("IfcProject"))
    if not projects:
        return [], {}, ["NO_IFC_PROJECT_FOR_UNIT_CONTEXT"]
    if len(projects) > 1:
        warnings.append(f"MULTIPLE_IFC_PROJECTS:{len(projects)}")
    units_context = getattr(projects[0], "UnitsInContext", None)
    if units_context is None:
        return [], {}, warnings + ["NO_PROJECT_UNIT_ASSIGNMENT"]
    summaries: list[dict[str, Any]] = []
    by_type: dict[str, dict[str, Any]] = {}
    for unit in list(getattr(units_context, "Units", None) or ()):
        summary = _unit_summary(unit)
        summaries.append(summary)
        unit_type = summary["unit_type"]
        if unit_type:
            if unit_type in by_type:
                warnings.append(f"DUPLICATE_PROJECT_UNIT_TYPE:{unit_type}")
            else:
                by_type[unit_type] = summary
    return summaries, by_type, warnings


def _quantity_summary(quantity: Any, set_entity: Any, unit_by_type: dict[str, dict[str, Any]], warnings: list[str]) -> dict[str, Any] | None:
    value_attr: str | None = None
    unit_type: str | None = None
    for ifc_type, attr, mapped_unit_type in _QUANTITY_TYPES:
        if quantity.is_a(ifc_type):
            value_attr = attr
            unit_type = mapped_unit_type
            break
    if value_attr is None:
        warnings.append(f"UNSUPPORTED_QUANTITY_TYPE:{quantity.is_a()}:{quantity.id()}")
        return None
    value = getattr(quantity, value_attr, None)
    if value is None:
        warnings.append(f"MISSING_QUANTITY_VALUE:{quantity.is_a()}:{quantity.id()}")
        return None
    explicit_unit = getattr(quantity, "Unit", None)
    if explicit_unit is not None:
        unit = _unit_summary(explicit_unit)
        unit["source"] = "explicit_quantity_unit"
    elif unit_type and unit_type in unit_by_type:
        unit = dict(unit_by_type[unit_type])
        unit["source"] = "project_unit_context"
    else:
        unit = None
        if unit_type:
            warnings.append(f"MISSING_UNIT_CONTEXT:{unit_type}:quantity:{quantity.id()}")
    if unit is not None:
        unit = {
            "step_id": unit["step_id"],
            "ifc_type": unit["ifc_type"],
            "unit_type": unit["unit_type"],
            "name": unit["name"],
            "prefix": unit["prefix"],
            "source": unit["source"],
        }
    return {
        "set_name": _string(getattr(set_entity, "Name", None)),
        "set_step_id": int(set_entity.id()),
        "name": _string(getattr(quantity, "Name", None)),
        "quantity_step_id": int(quantity.id()),
        "ifc_quantity_type": str(quantity.is_a()),
        "value": float(value),
        "unit": unit,
        "value_source": "declared_ifc_element_quantity",
    }


def _material_entries(material: Any, association_step_id: int, warnings: list[str]) -> list[dict[str, Any]]:
    kind = str(material.is_a())

    def one(mat: Any, source_type: str) -> dict[str, Any]:
        name = _string(getattr(mat, "Name", None))
        if not name:
            warnings.append(f"MATERIAL_NAME_MISSING:{source_type}:{getattr(mat, 'id', lambda: 0)()}")
        return {
            "name": name,
            "material_step_id": int(mat.id()) if hasattr(mat, "id") else None,
            "association_step_id": association_step_id,
            "source_type": source_type,
        }

    if material.is_a("IfcMaterial"):
        return [one(material, "IfcMaterial")]

    if material.is_a("IfcMaterialLayerSetUsage"):
        layer_set = getattr(material, "ForLayerSet", None)
        if layer_set is None:
            warnings.append(f"MATERIAL_LAYER_SET_USAGE_MISSING_LAYER_SET:{material.id()}")
            return []
        material = layer_set
        kind = str(material.is_a())

    if material.is_a("IfcMaterialLayerSet"):
        rows: list[dict[str, Any]] = []
        for layer in list(getattr(material, "MaterialLayers", None) or ()):
            mat = getattr(layer, "Material", None)
            if mat is None:
                warnings.append(f"MATERIAL_LAYER_MISSING_MATERIAL:{layer.id()}")
                continue
            rows.append(one(mat, "IfcMaterialLayerSet"))
        return rows

    if material.is_a("IfcMaterialConstituentSet"):
        rows = []
        for constituent in list(getattr(material, "MaterialConstituents", None) or ()):
            mat = getattr(constituent, "Material", None)
            if mat is None:
                warnings.append(f"MATERIAL_CONSTITUENT_MISSING_MATERIAL:{constituent.id()}")
                continue
            rows.append(one(mat, "IfcMaterialConstituentSet"))
        return rows

    if material.is_a("IfcMaterialProfileSetUsage"):
        profile_set = getattr(material, "ForProfileSet", None)
        if profile_set is None:
            warnings.append(f"MATERIAL_PROFILE_SET_USAGE_MISSING_PROFILE_SET:{material.id()}")
            return []
        material = profile_set

    if material.is_a("IfcMaterialProfileSet"):
        rows = []
        for profile in list(getattr(material, "MaterialProfiles", None) or ()):
            mat = getattr(profile, "Material", None)
            if mat is None:
                warnings.append(f"MATERIAL_PROFILE_MISSING_MATERIAL:{profile.id()}")
                continue
            rows.append(one(mat, "IfcMaterialProfileSet"))
        return rows

    if material.is_a("IfcMaterialList"):
        return [one(mat, "IfcMaterialList") for mat in list(getattr(material, "Materials", None) or ())]

    warnings.append(f"UNSUPPORTED_MATERIAL_SELECT:{kind}:{material.id()}")
    return []


def _element_materials(element: Any, warnings: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list(getattr(element, "HasAssociations", None) or ()):
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        material = getattr(relation, "RelatingMaterial", None)
        if material is None:
            warnings.append(f"MATERIAL_ASSOCIATION_WITHOUT_MATERIAL:{relation.id()}")
            continue
        rows.extend(_material_entries(material, int(relation.id()), warnings))
    if not rows:
        warnings.append("NO_DECLARED_MATERIAL_ASSOCIATION")
    return rows


def _element_quantities(element: Any, unit_by_type: dict[str, dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_names: dict[str, tuple[float, int]] = {}
    for relation in list(getattr(element, "IsDefinedBy", None) or ()):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        definition = getattr(relation, "RelatingPropertyDefinition", None)
        if definition is None or not definition.is_a("IfcElementQuantity"):
            continue
        for quantity in list(getattr(definition, "Quantities", None) or ()):
            row = _quantity_summary(quantity, definition, unit_by_type, warnings)
            if row is None:
                continue
            key = str(row["name"] or row["ifc_quantity_type"])
            previous = seen_names.get(key)
            if previous is not None:
                previous_value, previous_step = previous
                if previous_value != row["value"]:
                    warnings.append(f"CONFLICTING_DECLARED_QUANTITY:{key}:steps:{previous_step},{row['quantity_step_id']}")
                else:
                    warnings.append(f"DUPLICATE_DECLARED_QUANTITY:{key}:steps:{previous_step},{row['quantity_step_id']}")
            else:
                seen_names[key] = (row["value"], row["quantity_step_id"])
            rows.append(row)
    if not rows:
        warnings.append("NO_DECLARED_QUANTITIES")
    return rows


def _spatial_summary(entity: Any, warnings: list[str]) -> dict[str, Any]:
    parents: list[Any] = []
    for rel in list(getattr(entity, "Decomposes", None) or ()):
        if rel.is_a("IfcRelAggregates"):
            parent = getattr(rel, "RelatingObject", None)
            if parent is not None:
                parents.append(parent)
    if len(parents) > 1:
        warnings.append(f"MULTIPLE_SPATIAL_PARENTS:{entity.id()}:{len(parents)}")
    parent = parents[0] if parents else None
    return {
        "step_id": int(entity.id()),
        "global_id": _string(getattr(entity, "GlobalId", None)),
        "name": _string(getattr(entity, "Name", None)),
        "ifc_type": str(entity.is_a()),
        "parent_step_id": int(parent.id()) if parent is not None else None,
        "parent_global_id": _string(getattr(parent, "GlobalId", None)) if parent is not None else None,
    }


def _spatial_hierarchy(model: Any, warnings: list[str]) -> dict[str, list[dict[str, Any]]]:
    mapping = {
        "projects": "IfcProject",
        "sites": "IfcSite",
        "buildings": "IfcBuilding",
        "storeys": "IfcBuildingStorey",
        "spaces": "IfcSpace",
    }
    return {key: [_spatial_summary(entity, warnings) for entity in list(model.by_type(ifc_type))] for key, ifc_type in mapping.items()}


def extract_ifc_declared_data(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise IFCExtractionError(f"IFC file not found: {path}")
    if path.suffix.lower() != ".ifc":
        raise IFCExtractionError("v0.4 extraction accepts .ifc STEP files only")
    try:
        import ifcopenshell  # type: ignore
    except ImportError as exc:
        raise IFCExtractionError("IfcOpenShell is required; install requirements-proofgrid.txt") from exc
    try:
        model = ifcopenshell.open(str(path))
    except Exception as exc:
        raise IFCExtractionError(f"unable to parse IFC file: {exc}") from exc

    units, unit_by_type, warnings = _project_units(model)
    spatial = _spatial_hierarchy(model, warnings)
    elements = list(model.by_type("IfcElement"))
    if not elements:
        warnings.append("NO_IFC_ELEMENTS")

    extracted: list[dict[str, Any]] = []
    for element in elements:
        element_warnings: list[str] = []
        materials = _element_materials(element, element_warnings)
        quantities = _element_quantities(element, unit_by_type, element_warnings)
        extracted.append({
            "step_id": int(element.id()),
            "global_id": _string(getattr(element, "GlobalId", None)),
            "name": _string(getattr(element, "Name", None)),
            "ifc_type": str(element.is_a()),
            "materials": materials,
            "quantities": quantities,
            "warnings": element_warnings,
        })

    return {
        "adapter": "ifcopenshell",
        "adapter_version": str(getattr(ifcopenshell, "version", "unknown")),
        "source": str(path),
        "source_sha256": _sha256_file(path),
        "schema": str(getattr(model, "schema", "unknown")),
        "units": units,
        "spatial": spatial,
        "elements": extracted,
        "warnings": warnings,
        "limitations": [
            "Only quantities explicitly declared through IfcElementQuantity are extracted.",
            "No geometry-derived quantity is calculated.",
            "Units are reported as declared; no unit conversion is performed.",
            "Material associations are reported from IFC relationships without mapping to environmental source records.",
            "No LCA, code-compliance, engineering, architectural, procurement, or certification conclusion is produced.",
        ],
    }
