import unittest
from regen_promptos.prompt_ir_v2 import compile_ir_v2, migrate_pir_v1
from regen_promptos.requirement_graph import minimal_graph, validate_requirement_graph
from regen_promptos.vertical_slice import run_vertical_slice


class TestPromptIRv2(unittest.TestCase):
    def test_migrate_pir_v1(self):
        pir = {"objective": "x", "requirements": ["r1"], "constraints": ["c1"]}
        sem = migrate_pir_v1(pir)
        self.assertEqual(sem["objective"], "x")
        self.assertEqual(sem["requirements"], ["r1"])

    def test_compile_from_valid_graph(self):
        g = minimal_graph()
        ir = compile_ir_v2(g, provider="openai", model="gpt-4o")
        self.assertEqual(ir["planes"]["model"]["provider"], "openai")
        self.assertEqual(ir["planes"]["commercial"]["provider_key_included"], False)
        self.assertIsNotNone(ir["hash"])

    def test_compile_refuses_blocked_graph(self):
        g = minimal_graph()
        g["nodes"][1]["status"] = "BLOCKED"
        for n in g["nodes"]:
            if n["id"] == "comp-1":
                n["status"] = "VERIFIED"
        with self.assertRaises(Exception):
            compile_ir_v2(g)

    def test_vertical_slice_passes(self):
        r = run_vertical_slice("Build a login page")
        self.assertEqual(r["status"], "PASS")
        self.assertFalse(r["receipt"]["provider_key_included"])
        self.assertFalse(r["receipt"]["promptos_token_included"])

    def test_vertical_slice_blocked_refused(self):
        g = minimal_graph()
        g["nodes"][1]["status"] = "BLOCKED"
        for n in g["nodes"]:
            if n["id"] == "comp-1":
                n["status"] = "VERIFIED"
        r = validate_requirement_graph(g)
        self.assertNotEqual(r["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
