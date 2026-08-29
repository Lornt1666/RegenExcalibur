"""Prompt IR v2 — five-plane canonical intermediate representation.

Planes: semantic, execution, model, verification, commercial.
Migrates PIR v1. Refuses blocked graphs at the compile boundary.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from .requirement_graph import RequirementGraphError, hash_graph, validate_requirement_graph

IR_VERSION = "4.2.0"

PLANES = ("semantic", "execution", "model", "verification", "commercial")


class IRCompileError(ValueError):
    pass


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def hash_ir(ir: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(ir).encode("utf-8")).hexdigest()


def migrate_pir_v1(pir: Mapping[str, Any]) -> dict[str, Any]:
    """Lift a PIR v1 dict into the semantic plane of IR v2."""
    return {
        "objective": pir.get("objective", ""),
        "audience": pir.get("audience", ""),
        "context": pir.get("context", ""),
        "invariants": list(pir.get("invariants", [])),
        "requirements": list(pir.get("requirements", [])),
        "constraints": list(pir.get("constraints", [])),
        "non_goals": list(pir.get("non_goals", [])),
        "assumptions": list(pir.get("assumptions", [])),
        "unknowns": list(pir.get("unknowns", [])),
        "risks": list(pir.get("risks", [])),
        "selected_operation": pir.get("selected_operation", "AUTO"),
        "selected_modules": list(pir.get("selected_modules", [])),
        "model_capabilities_required": list(pir.get("model_capabilities_required", [])),
        "tool_contract": pir.get("tool_contract", {}),
        "authority_contract": pir.get("authority_contract", {}),
        "evidence_contract": pir.get("evidence_contract", {}),
        "output_contract": pir.get("output_contract", {}),
        "source_provenance": pir.get("source_provenance", ""),
        "privacy_classification": pir.get("privacy_classification", "local"),
    }


def compile_ir_v2(
    graph: Mapping[str, Any],
    *,
    pir_v1: Optional[Mapping[str, Any]] = None,
    provider: str = "openai",
    model: str = "gpt-4o",
    adapter: str = "openai-reasoning",
    service_units: int = 1,
) -> dict[str, Any]:
    result = validate_requirement_graph(graph)
    if result["status"] != "PASS":
        raise IRCompileError(
            f"refusing to compile IR v2 from invalid graph: {result['errors']}"
        )
    if result.get("contaminated_nodes"):
        raise IRCompileError(
            f"refusing to compile: blocked nodes contaminate {result['contaminated_nodes']}"
        )

    semantic = migrate_pir_v1(pir_v1) if pir_v1 else {
        "objective": "", "audience": "", "context": "", "invariants": [],
        "requirements": [], "constraints": [], "non_goals": [], "assumptions": [],
        "unknowns": [], "risks": [], "selected_operation": "AUTO",
        "selected_modules": [], "model_capabilities_required": [],
        "tool_contract": {}, "authority_contract": {}, "evidence_contract": {},
        "output_contract": {}, "source_provenance": "", "privacy_classification": "local",
    }
    semantic["graph_hash"] = result["hash"]
    semantic["graph_node_count"] = len(graph.get("nodes", []))

    execution = {
        "dag_nodes": [{"id": n["id"], "type": n["type"]} for n in graph.get("nodes", [])],
        "dag_edges": list(graph.get("edges", [])),
        "retry_policy": "fail_closed",
        "timeout_seconds": 300,
    }
    model_plane = {
        "provider": provider, "model": model, "adapter": adapter,
        "prompt_organization": "structured",
    }
    verification = {
        "tests": [n["id"] for n in graph.get("nodes", []) if n["type"] == "Test"],
        "acceptance_criteria": [n["id"] for n in graph.get("nodes", []) if n["type"] == "AcceptanceCriterion"],
        "graders": [], "thresholds": {},
    }
    commercial = {
        "service_units": service_units,
        "entitlement_state": "unentitled",
        "settlement_id": None,
        "provider_key_included": False,
        "promptos_token_included": False,
    }

    ir = {
        "ir_version": IR_VERSION,
        "planes": {
            "semantic": semantic, "execution": execution, "model": model_plane,
            "verification": verification, "commercial": commercial,
        },
        "hash": None,
    }
    ir["hash"] = hash_ir(ir)
    return ir
