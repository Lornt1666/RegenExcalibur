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
        g["edges"] = [e for e in g["edges"] if e["type"] != "satisfies"]
        r = validate_requirement_graph(g)
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any("acceptance" in e for e in r["errors"]))

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


if __name__ == "__main__":
    unittest.main()
