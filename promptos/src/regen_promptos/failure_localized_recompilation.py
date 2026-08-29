"""Failure-localized recompilation for RegenExcalibur PromptOS (v4.5).

When a compiled prompt fails independent evaluation, this module localizes the
failure to specific Requirement Graph nodes and Prompt IR v2 planes, then
produces a targeted recompilation that touches only the implicated surface.
Untouched requirements, constraints, and acceptance criteria are preserved by
hash identity — a recompilation that silently rewrites a passing requirement is
a defect, not a feature.

This module is pure and deterministic: no network, no provider keys, no
control-plane credentials. It operates on the semantic substrate (v4.2) and is
ready to bind to the independent evaluation engine (v4.4) and the evidence
ledger (v4.6).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from .prompt_ir_v2 import compile_ir_v2
from .requirement_graph import (
    NODE_TYPES,
    RequirementGraphError,
    hash_graph,
    validate_requirement_graph,
)

__all__ = [
    "FailureLocalizationError",
    "FailureReport",
    "RecompilationPlan",
    "localize_failure",
    "recompile_targeted",
    "run_failure_localized_recompilation",
]

_FAILURE_NODE_TYPES = {
    "Requirement", "Constraint", "Assumption", "Unknown", "Risk",
    "Component", "Interface", "DataObject", "Tool", "Test",
    "AcceptanceCriterion", "ImplementationTask",
}
_SEMANTIC_PLANES = ("semantic", "execution", "model", "verification", "commercial")


class FailureLocalizationError(RequirementGraphError):
    """Raised when a failure cannot be localized safely."""


@dataclass(frozen=True)
class FailureReport:
    """Structured failure evidence bound to graph nodes."""

    source: str
    summary: str
    severity: str
    affected_node_ids: tuple[str, ...]
    affected_planes: tuple[str, ...]
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "summary": self.summary,
            "severity": self.severity,
            "affected_node_ids": list(self.affected_node_ids),
            "affected_planes": list(self.affected_planes),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class RecompilationPlan:
    """A targeted recompilation: what changes, what is preserved, why."""

    original_graph_hash: str
    new_graph_hash: str
    changed_node_ids: tuple[str, ...]
    preserved_node_ids: tuple[str, ...]
    rationale: str
    ir: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_graph_hash": self.original_graph_hash,
            "new_graph_hash": self.new_graph_hash,
            "changed_node_ids": list(self.changed_node_ids),
            "preserved_node_ids": list(self.preserved_node_ids),
            "rationale": self.rationale,
            "ir": dict(self.ir),
        }


def _index_nodes(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(n["id"]): n for n in graph.get("nodes", []) if isinstance(n, dict) and "id" in n}


def _neighbors(graph: Mapping[str, Any], node_id: str) -> set[str]:
    out: set[str] = set()
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        if edge.get("source") == node_id:
            out.add(str(edge.get("target", "")))
        if edge.get("target") == node_id:
            out.add(str(edge.get("source", "")))
    out.discard("")
    return out


def localize_failure(
    graph: Mapping[str, Any],
    report: FailureReport,
) -> tuple[str, ...]:
    """Return the stable set of node IDs implicated by a failure report.

    Walks outward from each reported node along graph edges, stopping at
    Objective / NonGoal / CompletionState boundaries so the blast radius
    stays local. Raises if a reported node is absent or the graph is invalid.
    """
    validation = validate_requirement_graph(graph)
    if validation["status"] == "INVALID":
        raise FailureLocalizationError(
            "cannot localize failure against an invalid graph: "
            + "; ".join(validation["errors"])
        )
    nodes = _index_nodes(graph)
    implicated: set[str] = set()
    for nid in report.affected_node_ids:
        if nid not in nodes:
            raise FailureLocalizationError(f"failure references unknown node {nid!r}")
        implicated.add(nid)
        frontier = {nid}
        while frontier:
            nid = frontier.pop()
            for nb in _neighbors(graph, nid):
                nb_type = nodes.get(nb, {}).get("type")
                if nb_type in {"Objective", "NonGoal", "CompletionState"}:
                    continue
                if nb not in implicated:
                    implicated.add(nb)
                    frontier.add(nb)
    ordered = tuple(sorted(implicated))
    if not ordered:
        raise FailureLocalizationError("failure localized to zero nodes")
    return ordered


def _apply_targeted_patch(
    graph: Mapping[str, Any],
    implicated: tuple[str, ...],
    patch: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a new graph with only implicated nodes rewritten per patch."""
    nodes = [dict(n) for n in graph.get("nodes", [])]
    by_id = {n["id"]: n for n in nodes}
    for nid in implicated:
        if nid in patch:
            by_id[nid] = {**by_id[nid], **patch[nid]}
    new_nodes = [by_id[n["id"]] for n in nodes]
    new_graph = dict(graph)
    new_graph["nodes"] = new_nodes
    new_graph["graph_hash"] = hash_graph(new_graph)
    return new_graph


def recompile_targeted(
    graph: Mapping[str, Any],
    implicated: tuple[str, ...],
    *,
    patch: Mapping[str, Any],
    provider: str,
    model: str,
    adapter: str = "generic",
) -> RecompilationPlan:
    """Produce a recompilation that rewrites only implicated nodes.

    Preserved nodes must be byte-identical (by id + content hash) between the
    original and new graphs. The new IR is compiled from the patched graph.
    """
    original_hash = hash_graph(graph)
    patched = _apply_targeted_patch(graph, implicated, patch)
    new_hash = hash_graph(patched)
    if original_hash == new_hash:
        raise FailureLocalizationError("patch produced no graph change")

    original_nodes = {n["id"]: n for n in graph.get("nodes", [])}
    new_nodes = {n["id"]: n for n in patched.get("nodes", [])}
    preserved = tuple(
        sorted(
            nid for nid in original_nodes
            if nid not in implicated
            and json.dumps(original_nodes[nid], sort_keys=True)
            == json.dumps(new_nodes.get(nid), sort_keys=True)
        )
    )
    changed = tuple(sorted(set(implicated) - set(preserved)))
    if set(preserved) & set(changed):
        raise FailureLocalizationError("node classified as both changed and preserved")

    ir = compile_ir_v2(
        patched,
        provider=provider,
        model=model,
        adapter=adapter,
    )
    return RecompilationPlan(
        original_graph_hash=original_hash,
        new_graph_hash=new_hash,
        changed_node_ids=changed,
        preserved_node_ids=preserved,
        rationale=(
            f"localized to {len(changed)} changed / {len(preserved)} preserved nodes"
        ),
        ir=ir,
    )


def run_failure_localized_recompilation(
    graph: Mapping[str, Any],
    report: FailureReport,
    *,
    patch: Mapping[str, Any],
    provider: str,
    model: str,
    adapter: str = "generic",
) -> dict[str, Any]:
    """End-to-end: localize, recompile, return a traceable receipt."""
    implicated = localize_failure(graph, report)
    plan = recompile_targeted(
        graph, implicated, patch=patch, provider=provider, model=model, adapter=adapter,
    )
    return {
        "status": "RECOMPILED",
        "failure": report.to_dict(),
        "implicated_node_ids": list(implicated),
        "recompilation": plan.to_dict(),
        "provider_key_included": False,
        "raw_prompt_included": False,
        "raw_output_included": False,
    }
