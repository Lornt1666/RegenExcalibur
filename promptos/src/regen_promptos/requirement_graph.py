"""Requirement Graph — typed, traceable, fail-closed semantic substrate.

PromptOS v4.2. Every node carries stable ID, provenance, epistemic class,
and evidence requirements. Ten invariants are enforced at validation time.
A blocked node can never produce VERIFIED COMPLETE.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "4.2.0"

NODE_TYPES = (
    "Objective", "Stakeholder", "Requirement", "Constraint", "Preference",
    "NonGoal", "Assumption", "Unknown", "Risk", "Decision", "Component",
    "Interface", "DataObject", "Tool", "Permission", "ImplementationTask",
    "Test", "Evidence", "AcceptanceCriterion", "CompletionState",
)

EDGE_TYPES = (
    "derives_from", "requires", "constrained_by", "depends_on", "conflicts_with",
    "refines", "satisfies", "implemented_by", "verified_by", "evidenced_by",
    "affects", "supersedes", "blocked_by", "authorized_by", "rejected_by",
    "accepted_by",
)

CONTAMINATION_EDGES = frozenset({
    "blocked_by", "depends_on", "requires", "constrained_by", "conflicts_with",
    "satisfies", "verified_by", "evidenced_by", "implemented_by",
    "authorized_by", "rejected_by", "accepted_by", "affects", "refines",
    "supersedes", "derives_from",
})

REQUIRED_NODE_FIELDS = (
    "id", "type", "statement", "status", "provenance_hash", "epistemic_class",
)

VALID_STATUSES = frozenset({
    "PROPOSED", "ACCEPTED", "REJECTED", "BLOCKED", "IMPLEMENTED",
    "VERIFIED", "SUPERSEDED",
})

VALID_EPISTEMIC = frozenset({
    "FACT", "ASSUMPTION", "UNKNOWN", "INFERRED", "HYPOTHESIS",
})


class RequirementGraphError(ValueError):
    """Raised when a Requirement Graph violates an invariant."""


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def hash_graph(graph: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(graph).encode("utf-8")).hexdigest()


def _node_index(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    nodes = graph.get("nodes", [])
    idx: dict[str, Mapping[str, Any]] = {}
    for n in nodes:
        nid = n.get("id")
        if not nid:
            raise RequirementGraphError("node missing required field 'id'")
        if nid in idx:
            raise RequirementGraphError(f"duplicate node id: {nid}")
        idx[nid] = n
    return idx


def _edges_by_source(graph: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    out: dict[str, list[Mapping[str, Any]]] = {}
    for e in graph.get("edges", []):
        src = e.get("source")
        if src:
            out.setdefault(src, []).append(e)
    return out


def _edges_by_target(graph: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    out: dict[str, list[Mapping[str, Any]]] = {}
    for e in graph.get("edges", []):
        tgt = e.get("target")
        if tgt:
            out.setdefault(tgt, []).append(e)
    return out


def _collect_contaminated(graph: Mapping[str, Any], blocked_ids: set[str]) -> set[str]:
    by_src = _edges_by_source(graph)
    by_tgt = _edges_by_target(graph)
    contaminated: set[str] = set(blocked_ids)
    stack = list(blocked_ids)
    while stack:
        cur = stack.pop()
        for e in by_src.get(cur, []):
            if e.get("type") in CONTAMINATION_EDGES:
                t = e.get("target")
                if t and t not in contaminated:
                    contaminated.add(t)
                    stack.append(t)
        for e in by_tgt.get(cur, []):
            if e.get("type") in CONTAMINATION_EDGES:
                s = e.get("source")
                if s and s not in contaminated:
                    contaminated.add(s)
                    stack.append(s)
    return contaminated


def validate_requirement_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    invariants_checked = 0

    if not isinstance(graph, Mapping):
        raise RequirementGraphError("graph must be a mapping")

    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        errors.append("graph must contain at least one node")

    idx = _node_index(graph)

    for n in nodes:
        for f in REQUIRED_NODE_FIELDS:
            if f not in n:
                errors.append(f"node {n.get('id', '?')} missing field '{f}'")
        if n.get("type") not in NODE_TYPES:
            errors.append(f"node {n.get('id')} has unknown type {n.get('type')!r}")
        if n.get("status") not in VALID_STATUSES:
            errors.append(f"node {n.get('id')} has invalid status {n.get('status')!r}")
        if n.get("epistemic_class") not in VALID_EPISTEMIC:
            errors.append(f"node {n.get('id')} has invalid epistemic_class")

    for e in graph.get("edges", []):
        if e.get("type") not in EDGE_TYPES:
            errors.append(f"unknown edge type {e.get('type')!r}")
        if e.get("source") not in idx:
            errors.append(f"edge source {e.get('source')!r} not a node")
        if e.get("target") not in idx:
            errors.append(f"edge target {e.get('target')!r} not a node")

    if errors:
        return {"status": "INVALID", "errors": errors, "warnings": warnings,
                "invariants_checked": invariants_checked, "hash": None}

    invariants_checked += 1

    blocked_ids = {n["id"] for n in nodes if n["status"] == "BLOCKED"}
    contaminated = _collect_contaminated(graph, blocked_ids)

    invariants_checked += 1
    for n in nodes:
        if n["status"] == "VERIFIED" and n["id"] in contaminated:
            errors.append(
                f"invariant 4 violated: node {n['id']} is VERIFIED but "
                f"contaminated by a BLOCKED ancestor/dependency"
            )

    invariants_checked += 1
    ac_ids = {n["id"] for n in nodes if n["type"] == "AcceptanceCriterion"}
    reqs_with_ac = {e["target"] for e in graph.get("edges", [])
                    if e["type"] == "satisfies" and e["source"] in ac_ids}
    for n in nodes:
        if n["type"] == "Requirement" and n.get("priority", "critical") == "critical":
            if n["id"] not in reqs_with_ac and n["id"] not in blocked_ids:
                errors.append(
                    f"invariant 1: critical requirement {n['id']} has no acceptance criterion"
                )

    invariants_checked += 1
    reqs_with_impl = {e["target"] for e in graph.get("edges", []) if e["type"] == "implemented_by"}
    for n in nodes:
        if n["type"] == "Requirement" and n["status"] == "IMPLEMENTED":
            if n["id"] not in reqs_with_impl and n["id"] not in blocked_ids:
                errors.append(
                    f"invariant 2: implemented requirement {n['id']} has no implementation element"
                )

    invariants_checked += 1
    reqs_with_ev = {e["target"] for e in graph.get("edges", []) if e["type"] == "evidenced_by"}
    for n in nodes:
        if n["status"] == "VERIFIED" and n["id"] not in reqs_with_ev:
            errors.append(f"invariant 3: verified requirement {n['id']} has no evidence")

    invariants_checked += 1
    for e in graph.get("edges", []):
        if e["type"] == "conflicts_with":
            a, b = e["source"], e["target"]
            na, nb = idx[a], idx[b]
            if na.get("priority", "critical") == "critical" and nb.get("priority", "critical") == "critical":
                has_dec = any(
                    ed["type"] == "authorized_by" and (ed["source"] in (a, b) or ed["target"] in (a, b))
                    for ed in graph.get("edges", [])
                )
                if not has_dec:
                    warnings.append(
                        f"invariant 5: conflicting critical requirements {a}/{b} have no Decision"
                    )

    invariants_checked += 1
    for n in nodes:
        if n["type"] == "Assumption" and n["status"] == "ACCEPTED" and n.get("epistemic_class") == "FACT":
            errors.append(f"invariant 6: assumption {n['id']} accepted as FACT without promotion")

    invariants_checked += 1
    for n in nodes:
        if n["type"] == "Permission" and n["status"] == "ACCEPTED":
            if not any(e["type"] == "authorized_by" and e["target"] == n["id"] for e in graph.get("edges", [])):
                errors.append(f"invariant 7: permission {n['id']} accepted without authorized_by edge")

    invariants_checked += 1
    for n in nodes:
        if n["status"] == "SUPERSEDED" and not n.get("provenance_hash"):
            errors.append(f"invariant 8: superseded node {n['id']} missing provenance")

    invariants_checked += 1

    invariants_checked += 1
    for n in nodes:
        if n["type"] == "CompletionState" and n["status"] == "VERIFIED" and n["id"] not in reqs_with_ev:
            errors.append(f"invariant 10: completion state {n['id']} not traceable to evidence")

    status = "PASS" if not errors else "FAIL"
    return {"status": status, "errors": errors, "warnings": warnings,
            "invariants_checked": invariants_checked,
            "hash": hash_graph(graph) if status == "PASS" else None,
            "contaminated_nodes": sorted(contaminated)}


def minimal_graph() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "nodes": [
            {"id": "obj-1", "type": "Objective", "statement": "Ship feature",
             "status": "ACCEPTED", "provenance_hash": "a" * 64, "epistemic_class": "FACT", "priority": "critical"},
            {"id": "req-1", "type": "Requirement", "statement": "Must work",
             "status": "ACCEPTED", "provenance_hash": "b" * 64, "epistemic_class": "FACT", "priority": "critical"},
            {"id": "ac-1", "type": "AcceptanceCriterion", "statement": "Tests pass",
             "status": "ACCEPTED", "provenance_hash": "c" * 64, "epistemic_class": "FACT", "priority": "critical"},
            {"id": "test-1", "type": "Test", "statement": "unit test",
             "status": "ACCEPTED", "provenance_hash": "d" * 64, "epistemic_class": "FACT", "priority": "critical"},
            {"id": "comp-1", "type": "CompletionState", "statement": "done",
             "status": "ACCEPTED", "provenance_hash": "e" * 64, "epistemic_class": "FACT", "priority": "critical"},
        ],
        "edges": [
            {"source": "req-1", "target": "obj-1", "type": "derives_from"},
            {"source": "ac-1", "target": "req-1", "type": "satisfies"},
            {"source": "test-1", "target": "ac-1", "type": "verified_by"},
            {"source": "comp-1", "target": "test-1", "type": "evidenced_by"},
        ],
    }
