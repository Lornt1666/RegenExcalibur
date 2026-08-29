import unittest
from regen_promptos.requirement_graph import (
    hash_graph, minimal_graph, validate_requirement_graph,
)


class TestRequirementGraph(unittest.TestCase):
    def test_valid_graph_passes(self):
        r = validate_requirement_graph(minimal_graph())
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["invariants_checked"], 11)
        self.assertIsNotNone(r["hash"])

    def test_missing_acceptance_fails(self):
        g = minimal_graph()
        g["nodes"] = [n for n in g["nodes"] if n["type"] != "AcceptanceCriterion"]
        # Removing the AC node leaves its 'satisfies' edge with source 'ac-1',
        # which no longer exists -> structural INVALID before invariant 1.
        r = validate_requirement_graph(g)
        self.assertEqual(r["status"], "INVALID")
        self.assertTrue(any("edge source 'ac-1' not a node" in e for e in r["errors"]))

    def test_missing_acceptance_invariant_fires(self):
        # Clean removal: drop the AC node AND every edge touching it so the
        # structural check passes and invariant 1 must fire.
        g = minimal_graph()
        g["nodes"] = [n for n in g["nodes"] if n["type"] != "AcceptanceCriterion"]
        g["edges"] = [e for e in g["edges"]
                        if e.get("source") != "ac-1" and e.get("target") != "ac-1"]
        r = validate_requirement_graph(g)
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any("invariant 1" in e for e in r["errors"]))

    def test_blocked_plus_verified_rejected(self):
        g = minimal_graph()
        g["nodes"][1]["status"] = "BLOCKED"
        for n in g["nodes"]:
            if n["id"] == "comp-1":
                n["status"] = "VERIFIED"
        r = validate_requirement_graph(g)
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any("invariant 4" in e for e in r["errors"]))
        self.assertIn("comp-1", r["contaminated_nodes"])

    def test_assumption_cannot_become_fact(self):
        g = minimal_graph()
        g["nodes"].append({
            "id": "asm-1", "type": "Assumption", "statement": "x",
            "status": "ACCEPTED", "provenance_hash": "f" * 64,
            "epistemic_class": "FACT", "priority": "normal",
        })
        r = validate_requirement_graph(g)
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any("invariant 6" in e for e in r["errors"]))

    def test_hash_stable(self):
        g = minimal_graph()
        self.assertEqual(hash_graph(g), hash_graph(g))
        g2 = minimal_graph()
        g2["nodes"][0]["statement"] = "different"
        self.assertNotEqual(hash_graph(g), hash_graph(g2))


if __name__ == "main":
    unittest.main()
