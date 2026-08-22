import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "reference" / "scope_coverage_v22.py"
spec = importlib.util.spec_from_file_location("v22", MOD)
v22 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v22)


class V22Tests(unittest.TestCase):
    def manifest(self):
        return {
            "schema_version": "1.0",
            "manifest_version": "2.2.0",
            "scope_id": "proofgrid:v22:declared-synthetic-two-member-scope",
            "scope_type": "DECLARED_SYNTHETIC_EVIDENCE_SCOPE",
            "declared_scope_defined": True,
            "whole_building_scope": False,
            "expected_member_count": 2,
            "expected_members": [
                {"semantic_identity_sha256": k, "element_global_id": v}
                for k, v in v22.EXPECTED_MEMBERS.items()
            ],
            "missing_evidence_as_zero": False,
            "exclusions_and_unknowns": ["Synthetic bounded scope only."],
        }

    def test_valid_manifest(self):
        v22.verify_manifest(self.manifest())

    def test_whole_building_scope_rejected(self):
        m = self.manifest(); m["whole_building_scope"] = True
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)

    def test_missing_as_zero_rejected(self):
        m = self.manifest(); m["missing_evidence_as_zero"] = True
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)

    def test_missing_expected_member_rejected(self):
        m = self.manifest(); m["expected_members"] = m["expected_members"][:1]
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)

    def test_wrong_element_binding_rejected(self):
        m = self.manifest(); m["expected_members"][0]["element_global_id"] = "WRONG"
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)

    def test_duplicate_semantic_member_rejected(self):
        m = self.manifest(); m["expected_members"][1] = copy.deepcopy(m["expected_members"][0])
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)

    def test_exclusions_required(self):
        m = self.manifest(); m["exclusions_and_unknowns"] = []
        with self.assertRaises(v22.CoverageError): v22.verify_manifest(m)


if __name__ == "__main__":
    unittest.main()
