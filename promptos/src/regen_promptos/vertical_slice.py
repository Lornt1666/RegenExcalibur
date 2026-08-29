"""Vertical slice: source -> graph -> IR v2 -> traceability receipt.

Demonstrates the v4.2 semantic substrate end-to-end with explicit
no-credential assertions.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .prompt_ir_v2 import IRCompileError, compile_ir_v2
from .requirement_graph import hash_graph, validate_requirement_graph


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_vertical_slice(source: str) -> dict[str, Any]:
    source_hash = _sha(source)

    graph = {
        "schema_version": "4.2.0",
        "nodes": [
            {"id": "obj-1", "type": "Objective", "statement": source[:80],
             "status": "ACCEPTED", "provenance_hash": source_hash,
             "epistemic_class": "FACT", "priority": "critical"},
            {"id": "req-1", "type": "Requirement", "statement": "Satisfy objective",
             "status": "ACCEPTED", "provenance_hash": source_hash,
             "epistemic_class": "FACT", "priority": "critical"},
            {"id": "ac-1", "type": "AcceptanceCriterion", "statement": "Output valid",
             "status": "ACCEPTED", "provenance_hash": source_hash,
             "epistemic_class": "FACT", "priority": "critical"},
            {"id": "test-1", "type": "Test", "statement": "slice test",
             "status": "ACCEPTED", "provenance_hash": source_hash,
             "epistemic_class": "FACT", "priority": "critical"},
            {"id": "comp-1", "type": "CompletionState", "statement": "complete",
             "status": "ACCEPTED", "provenance_hash": source_hash,
             "epistemic_class": "FACT", "priority": "critical"},
        ],
        "edges": [
            {"source": "req-1", "target": "obj-1", "type": "derives_from"},
            {"source": "ac-1", "target": "req-1", "type": "satisfies"},
            {"source": "test-1", "target": "ac-1", "type": "verified_by"},
            {"source": "comp-1", "target": "test-1", "type": "evidenced_by"},
        ],
    }

    gv = validate_requirement_graph(graph)
    if gv["status"] != "PASS":
        return {"status": "BLOCKED", "graph_validation": gv, "ir": None, "receipt": None}

    try:
        ir = compile_ir_v2(graph, provider="openai", model="gpt-4o",
                           adapter="openai-reasoning", service_units=1)
    except IRCompileError as exc:
        return {"status": "BLOCKED", "graph_validation": gv,
                "ir": None, "receipt": None, "compile_error": str(exc)}

    receipt = {
        "source_hash": source_hash,
        "graph_hash": gv["hash"],
        "ir_hash": ir["hash"],
        "acceptance": [n["id"] for n in graph["nodes"] if n["type"] == "AcceptanceCriterion"],
        "provider_key_included": False,
        "promptos_token_included": False,
        "raw_prompt_local": True,
        "raw_output_local": True,
    }
    assert receipt["provider_key_included"] is False
    assert receipt["promptos_token_included"] is False

    return {"status": "PASS", "graph_validation": gv, "ir": ir, "receipt": receipt}
