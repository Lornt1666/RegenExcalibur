import copy
import json
import socket
import unittest

from reference import model_inventory_v30 as v30


class FakeProduct:
    def __init__(self, typ: str):
        self.typ = typ

    def is_a(self, typ=None):
        if typ is None:
            return self.typ
        if typ == "IfcElement":
            return self.typ in {"IfcWall", "IfcOpeningElement"}
        return self.typ == typ


class V30UnitTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(v30.DEFAULT_POLICY.read_text(encoding="utf-8"))

    def test_policy_accepts_canonical_policy(self):
        v30.validate_policy(self.policy)

    def test_policy_rejects_synthetic_gate_promotion(self):
        policy = copy.deepcopy(self.policy)
        policy["source_requirements"]["synthetic_source_may_close_gate"] = True
        with self.assertRaisesRegex(v30.InventoryError, "synthetic"):
            v30.validate_policy(policy)

    def test_policy_file_hash_is_immutable(self):
        raw = v30.DEFAULT_POLICY.read_bytes()
        self.assertEqual(v30.policy_hash(raw), v30.EXPECTED_POLICY_SHA256)
        self.assertNotEqual(v30.policy_hash(raw + b"\n"), v30.EXPECTED_POLICY_SHA256)

    def test_real_authorization_accepts_real_only(self):
        auth = {
            "schema_version": "1.0",
            "authorization_version": "3.0.0",
            "source_classification": "USER_AUTHORIZED_REAL_IFC",
            "user_authorized": True,
            "synthetic": False,
            "reconstructed": False,
            "authorized_purpose": "ProofGrid v3.0 authoritative model inventory basis",
            "authorization_reference": "user-supplied-file:example.ifc",
        }
        self.assertEqual(v30.validate_authorization(auth, preflight=False), v30.REAL_VERDICT)

    def test_synthetic_cannot_close_real_gate(self):
        auth = {
            "schema_version": "1.0",
            "authorization_version": "3.0.0",
            "source_classification": "SYNTHETIC_TEST_FIXTURE",
            "user_authorized": False,
            "synthetic": True,
            "reconstructed": False,
            "authorized_purpose": "ProofGrid v3.0 authoritative model inventory basis",
            "authorization_reference": "ci:synthetic",
        }
        with self.assertRaises(v30.InventoryError):
            v30.validate_authorization(auth, preflight=False)
        self.assertEqual(v30.validate_authorization(auth, preflight=True), v30.PREFLIGHT_VERDICT)

    def test_step_arg_parser_preserves_numeric_token(self):
        args = v30._split_step_args("'Mass',$,$,250.,$")
        self.assertEqual(args[3], "250.")

    def test_step_arg_parser_handles_nested_and_escaped_strings(self):
        args = v30._split_step_args("'A''B',(#1,#2),$,(1.,2.)")
        self.assertEqual(len(args), 4)
        self.assertEqual(args[0], "'A''B'")
        self.assertEqual(args[1], "(#1,#2)")

    def test_multiline_step_records(self):
        text = """ISO-10303-21;
DATA;
#12=IFCQUANTITYWEIGHT(
'Mass',$,$,250.,$);
ENDSEC;
END-ISO-10303-21;
"""
        records = v30.step_records(text, 10000)
        self.assertIn(12, records)
        self.assertEqual(v30.exact_quantity_token(records, 12, "IfcQuantityWeight"), "250.")

    def test_duplicate_step_record_rejected(self):
        text = "#1=IFCWALL('a');\n#1=IFCWALL('b');\n"
        with self.assertRaisesRegex(v30.InventoryError, "duplicate STEP"):
            v30.step_records(text, 10000)

    def test_exact_lexical_parser_mismatch_rejected(self):
        self.assertTrue(v30.verify_lexical_parser_consistency("250.", 250.0, 12))
        with self.assertRaisesRegex(v30.InventoryError, "lexical/parser"):
            v30.verify_lexical_parser_consistency("250.0000000000000001", 250.0, 12)

    def test_resource_limits_rejected(self):
        limits = {"max_file_bytes": 100, "max_total_entities": 10, "max_enumerated_products": 5}
        v30.enforce_resource_counts(file_bytes=100, total_entities=10, products=5, limits=limits)
        with self.assertRaisesRegex(v30.InventoryError, "file"):
            v30.enforce_resource_counts(file_bytes=101, total_entities=1, products=1, limits=limits)
        with self.assertRaisesRegex(v30.InventoryError, "entity"):
            v30.enforce_resource_counts(file_bytes=1, total_entities=11, products=1, limits=limits)
        with self.assertRaisesRegex(v30.InventoryError, "product"):
            v30.enforce_resource_counts(file_bytes=1, total_entities=1, products=6, limits=limits)

    def test_python_network_escape_is_blocked(self):
        with v30.deny_python_network():
            with self.assertRaises(v30.NetworkEscapeAttempt):
                socket.create_connection(("example.com", 80), timeout=0.01)

    def test_classification(self):
        self.assertEqual(v30.classify(FakeProduct("IfcWall"), self.policy), ("EVIDENCE_REQUIRED", None))
        self.assertEqual(v30.classify(FakeProduct("IfcOpeningElement"), self.policy), ("EVIDENCE_NOT_APPLICABLE", "OPENING_VOID_FEATURE"))
        self.assertEqual(v30.classify(FakeProduct("IfcBuilding"), self.policy), ("OUT_OF_DECLARED_EVIDENCE_SCOPE", "NON_ELEMENT_PRODUCT"))

    def basis(self, verdict=v30.PREFLIGHT_VERDICT):
        return {
            "schema_version": "1.0",
            "record_type": "ProofGridModelInventoryBasis",
            "verdict": verdict,
            "production_gate_satisfied": verdict == v30.REAL_VERDICT,
            "source": {"sha256": "a" * 64},
            "policy": {"sha256": "b" * 64},
            "authorization": {"source_classification": v30.REAL_AUTH if verdict == v30.REAL_VERDICT else v30.PREFLIGHT_AUTH},
            "inventory": {
                "enumerated_count": 2,
                "entries": [
                    {"source_sha256": "a" * 64, "step_id": 1, "global_id": "g1", "ifc_type": "IfcWall", "policy_state": "EVIDENCE_REQUIRED", "policy_reason": None},
                    {"source_sha256": "a" * 64, "step_id": 2, "global_id": "g2", "ifc_type": "IfcOpeningElement", "policy_state": "EVIDENCE_NOT_APPLICABLE", "policy_reason": "OPENING_VOID_FEATURE"},
                ],
            },
            "closure": {"parser_enumerated_count": 2, "silent_drop_count": 0, "every_enumerated_object_classified_exactly_once": True},
            "claims": {"whole_building_lca_claimed": False, "scientific_validation_performed": False, "professional_review_performed": False, "regulator_accepted": False, "certified": False},
            "limitations": ["test"],
            "integrity": {"content_sha256": "0" * 64, "canonicalization": v30.CANONICALIZATION, "signature": None},
        }

    def test_basis_rejects_duplicate_globalid(self):
        record = self.basis()
        record["inventory"]["entries"][1]["global_id"] = "g1"
        with self.assertRaisesRegex(v30.InventoryError, "duplicate non-empty GlobalId"):
            v30.validate_basis(record)

    def test_basis_rejects_silent_drop(self):
        record = self.basis()
        record["closure"]["silent_drop_count"] = 1
        with self.assertRaisesRegex(v30.InventoryError, "silent drops"):
            v30.validate_basis(record)

    def test_basis_rejects_missing_reason(self):
        record = self.basis()
        record["inventory"]["entries"][1]["policy_reason"] = None
        with self.assertRaisesRegex(v30.InventoryError, "missing reason"):
            v30.validate_basis(record)

    def test_preflight_cannot_satisfy_production(self):
        record = self.basis()
        record["production_gate_satisfied"] = True
        with self.assertRaisesRegex(v30.InventoryError, "preflight"):
            v30.validate_basis(record)

    def test_real_verdict_requires_real_authorization(self):
        record = self.basis(v30.REAL_VERDICT)
        record["authorization"]["source_classification"] = v30.PREFLIGHT_AUTH
        with self.assertRaisesRegex(v30.InventoryError, "real authorization"):
            v30.validate_basis(record)

    def test_claim_promotion_rejected(self):
        record = self.basis()
        record["claims"]["certified"] = True
        with self.assertRaisesRegex(v30.InventoryError, "certified"):
            v30.validate_basis(record)


if __name__ == "__main__":
    unittest.main()
