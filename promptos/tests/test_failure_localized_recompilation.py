"""Tests for failure-localized recompilation (v4.5)."""

from __future__ import annotations

import json
import unittest

from regen_promptos.failure_localized_recompilation import (
    FailureLocalizationError,
    FailureReport,
    localize_failure,
    recompile_targeted,
    run_failure_localized_recompilation,
)
from regen_promptos.requirement_graph import hash_graph, minimal_graph, validate_requirement_graph


class TestFailureLocalizedRecompilation(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = minimal_graph()
        self.graph["nodes"].append(
            {
                "id": "req-risk",
                "type": "Requirement",
                "statement": "Handle provider timeout with bounded retry.",
                "status": "ACCEPTED",
                "provenance_hash": "f" * 64,
                "epistemic_class": "ASSUMPTION",
                "confidence": 0.5,
                "priority": "low",
            }
        )
        self.graph["edges"].append(
            {"source": "req-risk", "target": "ac-1", "type": "satisfies"}
        )
        self.graph["graph_hash"] = hash_graph(self.graph)
        v = validate_requirement_graph(self.graph)
        self.assertEqual(v["status"], "PASS", v)

    def test_localize_failure_to_reported_node(self) -> None:
        report = FailureReport(
            source="eval-v1",
            summary="timeout handling missing",
            severity="high",
            affected_node_ids=("req-risk",),
            affected_planes=("semantic", "execution"),
        )
        implicated = localize_failure(self.graph, report)
        self.assertIn("req-risk", implicated)
        self.assertIn("ac-1", implicated)

    def test_localize_failure_unknown_node_raises(self) -> None:
        report = FailureReport(
            source="eval-v1",
            summary="x",
            severity="low",
            affected_node_ids=("no-such-node",),
            affected_planes=(),
        )
        with self.assertRaises(FailureLocalizationError):
            localize_failure(self.graph, report)

    def test_recompile_preserves_untouched_nodes(self) -> None:
        report = FailureReport(
            source="eval-v1",
            summary="timeout handling missing",
            severity="high",
            affected_node_ids=("req-risk",),
            affected_planes=("semantic",),
        )
        implicated = localize_failure(self.graph, report)
        plan = recompile_targeted(
            self.graph,
            implicated,
            patch={
                "req-risk": {
                    "statement": "Handle provider timeout with bounded retry and jitter.",
                    "confidence": 0.9,
                    "epistemic_class": "EVIDENCED",
                }
            },
            provider="openai",
            model="gpt-test",
        )
        self.assertIn("req-risk", plan.changed_node_ids)
        self.assertIn("obj-1", plan.preserved_node_ids)
        self.assertIn("ac-1", plan.preserved_node_ids)
        self.assertNotEqual(plan.original_graph_hash, plan.new_graph_hash)
        self.assertEqual(
            json.dumps(
                {n["id"]: n for n in self.graph["nodes"] if n["id"] == "obj-1"},
                sort_keys=True,
            ),
            json.dumps(
                {n["id"]: n for n in self.graph["nodes"] if n["id"] == "obj-1"},
                sort_keys=True,
            ),
        )

    def test_recompile_refuses_no_op_patch(self) -> None:
        report = FailureReport(
            source="eval-v1",
            summary="x",
            severity="low",
            affected_node_ids=("req-risk",),
            affected_planes=(),
        )
        implicated = localize_failure(self.graph, report)
        with self.assertRaises(FailureLocalizationError):
            recompile_targeted(
                self.graph, implicated, patch={}, provider="openai", model="gpt-test"
            )

    def test_end_to_end_receipt_has_no_secrets(self) -> None:
        report = FailureReport(
            source="eval-v1",
            summary="timeout handling missing",
            severity="high",
            affected_node_ids=("req-risk",),
            affected_planes=("semantic",),
            evidence={"provider_key": "sk-super-secret-value-123"},
        )
        receipt = run_failure_localized_recompilation(
            self.graph,
            report,
            patch={
                "req-risk": {
                    "statement": "Retry with jitter.",
                    "confidence": 0.95,
                }
            },
            provider="openai",
            model="gpt-test",
        )
        self.assertEqual(receipt["status"], "RECOMPILED")
        self.assertFalse(receipt["provider_key_included"])
        blob = json.dumps(receipt)
        self.assertNotIn("sk-super-secret-value-123", blob)
        self.assertIn("req-risk", receipt["implicated_node_ids"])
        self.assertIn("obj-1", receipt["recompilation"]["preserved_node_ids"])

    def test_localize_stops_at_objective_boundary(self) -> None:
        # Objective must not be pulled into the blast radius.
        report = FailureReport(
            source="eval-v1",
            summary="x",
            severity="low",
            affected_node_ids=("req-1",),
            affected_planes=(),
        )
        implicated = localize_failure(self.graph, report)
        self.assertNotIn("obj-1", implicated)


if __name__ == "__main__":
    unittest.main()
