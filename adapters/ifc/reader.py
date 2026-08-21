"""IfcOpenShell-backed IFC inspection adapter for RegenExcalibur ProofGrid.

This adapter intentionally performs read-only structural ingestion. It does not
infer code compliance, quantities, embodied carbon, engineering adequacy, or
professional conclusions from IFC content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class IFCAdapterError(ValueError):
    """Raised when an IFC file cannot be safely inspected."""


def _entity_summary(entity: Any) -> dict[str, Any]:
    return {
        "step_id": entity.id(),
        "global_id": getattr(entity, "GlobalId", None),
        "name": getattr(entity, "Name", None),
        "ifc_type": entity.is_a(),
    }


def inspect_ifc(path: Path) -> dict[str, Any]:
    """Open a real IFC STEP file with IfcOpenShell and return a bounded summary."""
    path = Path(path)
    if not path.is_file():
        raise IFCAdapterError(f"IFC file not found: {path}")
    if path.suffix.lower() != ".ifc":
        raise IFCAdapterError("IFC adapter accepts .ifc STEP files only in v0.2")

    try:
        import ifcopenshell  # type: ignore
    except ImportError as exc:
        raise IFCAdapterError(
            "IfcOpenShell is required for IFC ingestion; install requirements-proofgrid.txt"
        ) from exc

    try:
        model = ifcopenshell.open(str(path))
    except Exception as exc:
        raise IFCAdapterError(f"unable to parse IFC file: {exc}") from exc

    def entities(type_name: str) -> list[Any]:
        try:
            return list(model.by_type(type_name))
        except Exception as exc:
            raise IFCAdapterError(f"unable to query {type_name}: {exc}") from exc

    projects = entities("IfcProject")
    sites = entities("IfcSite")
    buildings = entities("IfcBuilding")
    storeys = entities("IfcBuildingStorey")
    spaces = entities("IfcSpace")
    elements = entities("IfcElement")

    return {
        "adapter": "ifcopenshell",
        "adapter_version": getattr(ifcopenshell, "version", "unknown"),
        "source": str(path),
        "schema": str(getattr(model, "schema", "unknown")),
        "counts": {
            "projects": len(projects),
            "sites": len(sites),
            "buildings": len(buildings),
            "storeys": len(storeys),
            "spaces": len(spaces),
            "elements": len(elements),
        },
        "projects": [_entity_summary(entity) for entity in projects[:25]],
        "buildings": [_entity_summary(entity) for entity in buildings[:100]],
        "limitations": [
            "Read-only structural inspection only.",
            "No quantity takeoff, LCA, code-compliance, engineering, or certification conclusion is produced.",
            "Entity counts and metadata reflect the source IFC model and parser interpretation only.",
        ],
    }
