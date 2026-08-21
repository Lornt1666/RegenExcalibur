import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "reference" / "environmental_contribution_set.py"
spec = importlib.util.spec_from_file_location("environmental_contribution_set", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class ContributionSetV18Tests(unittest.TestCase):
    def write_json(self, path: Path, value: dict) -> bytes:
        raw = mod.pretty_json_bytes(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return raw

    def hash_record(self, record: dict) -> dict:
        record = copy.deepcopy(record)
        record["integrity"]["content_sha256"] = mod.ZERO_DIGEST
        record["integrity"]["content_sha256"] = mod.sha256_bytes(mod.canonical_json_bytes(record))
        return record

    def hash_receipt(self, receipt: dict) -> dict:
        receipt = copy.deepcopy(receipt)
        receipt.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = mod.sha256_bytes(mod.canonical_json_bytes(receipt))
        return receipt

    def make_member(self, root: Path, prefix: str = "m1", *, rxep_id_suffix: str = "") -> dict:
        calc = {
            "schema_version": "1.0",
            "record_type": "ProofGridMappedDeclaredResultCalculation",
            "verdict": mod.CALC_VERDICT,
            "calculation_scope": "SINGLE_MAPPED_DECLARED_RESULT_ROW",
            "inputs": {
                "ifc_source_sha256": "1" * 64,
                "element_global_id": "ELEMENT-1",
                "product_flow_uuid": "FLOW-1",
                "product_flow_version": "00.00.001",
                "quantity_record_content_sha256": "2" * 64,
                "mapping_record_content_sha256": "3" * 64,
                "closure_record_content_sha256": "4" * 64,
                "declaration_bundle_content_sha256": "5" * 64
            },
            "selection": {"indicator_code": "GWP-total", "indicator_uuid": "INDICATOR-1", "module": "A1-A3", "scenario": None},
            "calculation": {"scaled_result_decimal": "12.5", "scaled_result_unit": "kg CO2 eqv."},
            "calculation_performed": True,
            "aggregation_performed": False,
            "missing_modules_are_zero": False,
            "unit_conversion_performed": False,
            "scenario_inference_performed": False,
            "fuzzy_mapping_performed": False,
            "scientific_validation_performed": False,
            "professional_review_performed": False,
            "certified": False,
            "integrity": {"content_sha256": mod.ZERO_DIGEST, "canonicalization": mod.CANONICALIZATION, "signature": None}
        }
        calc = self.hash_record(calc)
        calc_path = root / f"{prefix}-calc.json"
        calc_raw = self.write_json(calc_path, calc)
        calc_receipt = self.hash_receipt({"verdict": mod.CALC_VERDICT, "record_content_sha256": calc["integrity"]["content_sha256"], "record_file_sha256": mod.sha256_bytes(calc_raw)})
        calc_receipt_path = root / f"{prefix}-calc-receipt.json"
        calc_receipt_raw = self.write_json(calc_receipt_path, calc_receipt)

        rxep = {
            "id": "rxep:test" + rxep_id_suffix,
            "subject": {"id": "ELEMENT-1", "type": "ifc-declaration-environmental-contribution"},
            "claim": {"type": "scaled_declared_environmental_contribution", "statement": "test"},
            "measurement": {
                "value": 12.5,
                "value_decimal": "12.5",
                "decimal_value_is_authority": True,
                "numeric_value_is_authority": False,
                "unit": "kg CO2 eqv.",
                "indicator_code": "GWP-total",
                "indicator_uuid": "INDICATOR-1",
                "module": "A1-A3",
                "scenario": None
            },
            "methodology": {"name": "test", "version": "1"},
            "sources": [
                {"path": "calc.json", "sha256": mod.sha256_bytes(calc_raw), "kind": "calculation-record", "content_sha256": calc["integrity"]["content_sha256"]},
                {"path": "calc-receipt.json", "sha256": mod.sha256_bytes(calc_receipt_raw), "kind": "calculation-receipt", "receipt_sha256": calc_receipt["receipt_sha256"]}
            ],
            "software": {"name": "test", "version": "1"},
            "jurisdiction": "test",
            "review": {"state": "CALCULATED", "reviewer": None},
            "limitations": ["test"],
            "aggregation_performed": False,
            "scientific_validation_performed": False,
            "professional_review_performed": False,
            "certified": False,
            "integrity": {"content_sha256": mod.ZERO_DIGEST, "canonicalization": mod.CANONICALIZATION, "signature": None}
        }
        rxep = self.hash_record(rxep)
        rxep_path = root / f"{prefix}-rxep.json"
        rxep_raw = self.write_json(rxep_path, rxep)
        rxep_receipt = self.hash_receipt({
            "verdict": mod.RXEP_VERDICT,
            "record_content_sha256": rxep["integrity"]["content_sha256"],
            "record_file_sha256": mod.sha256_bytes(rxep_raw),
            "review_state": "CALCULATED",
            "certified": False,
            "v16_record_content_sha256": calc["integrity"]["content_sha256"],
            "v16_calculation_receipt_sha256": calc_receipt["receipt_sha256"]
        })
        rxep_receipt_path = root / f"{prefix}-rxep-receipt.json"
        rxep_receipt_raw = self.write_json(rxep_receipt_path, rxep_receipt)
        return {
            "member_id": prefix,
            "rxep_record_path": rxep_path.name,
            "rxep_record_content_sha256": rxep["integrity"]["content_sha256"],
            "rxep_record_file_sha256": mod.sha256_bytes(rxep_raw),
            "rxep_receipt_path": rxep_receipt_path.name,
            "rxep_receipt_sha256": rxep_receipt["receipt_sha256"],
            "rxep_receipt_file_sha256": mod.sha256_bytes(rxep_receipt_raw),
            "calculation_record_path": calc_path.name,
            "calculation_record_content_sha256": calc["integrity"]["content_sha256"],
            "calculation_record_file_sha256": mod.sha256_bytes(calc_raw),
            "calculation_receipt_path": calc_receipt_path.name,
            "calculation_receipt_sha256": calc_receipt["receipt_sha256"],
            "calculation_receipt_file_sha256": mod.sha256_bytes(calc_receipt_raw)
        }

    def make_request(self, root: Path, members: list[dict]) -> Path:
        req = {
            "schema_version": "1.0",
            "request_version": "1.8.0",
            "set_id": "set-1",
            "scope_id": "scope-test",
            "completeness_status": "PARTIAL",
            "compatibility": {"indicator_code": "GWP-total", "indicator_uuid": "INDICATOR-1", "unit": "kg CO2 eqv.", "module": "A1-A3", "scenario": None},
            "members": members
        }
        p = root / "request.json"
        self.write_json(p, req)
        return p

    def test_single_partial_member_admitted_without_sum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = mod.build_set(self.make_request(root, [self.make_member(root)]))
            self.assertEqual(record["member_count"], 1)
            self.assertEqual(record["completeness_status"], "PARTIAL")
            self.assertFalse(record["aggregation_performed"])
            self.assertFalse(record["sum_performed"])
            self.assertFalse(record["missing_contributions_are_zero"])

    def test_exact_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            member = self.make_member(root)
            duplicate = copy.deepcopy(member); duplicate["member_id"] = "m2"
            with self.assertRaisesRegex(mod.ContributionSetError, "duplicate RXEP record"):
                mod.build_set(self.make_request(root, [member, duplicate]))

    def test_semantic_duplicate_rewrapped_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.make_member(root, "m1")
            second = self.make_member(root, "m2", rxep_id_suffix="-rewrapped")
            with self.assertRaisesRegex(mod.ContributionSetError, "semantic duplicate"):
                mod.build_set(self.make_request(root, [first, second]))

    def test_unit_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = self.make_request(root, [self.make_member(root)])
            req = json.loads(request.read_text()); req["compatibility"]["unit"] = "kgCO2e"; self.write_json(request, req)
            with self.assertRaisesRegex(mod.ContributionSetError, "unit"):
                mod.build_set(request)

    def test_indicator_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = self.make_request(root, [self.make_member(root)])
            req = json.loads(request.read_text()); req["compatibility"]["indicator_uuid"] = "OTHER"; self.write_json(request, req)
            with self.assertRaisesRegex(mod.ContributionSetError, "indicator UUID"):
                mod.build_set(request)

    def test_module_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = self.make_request(root, [self.make_member(root)])
            req = json.loads(request.read_text()); req["compatibility"]["module"] = "A4"; self.write_json(request, req)
            with self.assertRaisesRegex(mod.ContributionSetError, "module"):
                mod.build_set(request)

    def test_scenario_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = self.make_request(root, [self.make_member(root)])
            req = json.loads(request.read_text()); req["compatibility"]["scenario"] = {"name": "s1"}; self.write_json(request, req)
            with self.assertRaisesRegex(mod.ContributionSetError, "scenario"):
                mod.build_set(request)

    def test_review_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            member = self.make_member(root)
            p = root / member["rxep_record_path"]
            record = json.loads(p.read_text()); record["review"]["state"] = "INDEPENDENTLY_VERIFIED"; record = self.hash_record(record)
            raw = self.write_json(p, record); member["rxep_record_content_sha256"] = record["integrity"]["content_sha256"]; member["rxep_record_file_sha256"] = mod.sha256_bytes(raw)
            rp = root / member["rxep_receipt_path"]
            receipt = json.loads(rp.read_text()); receipt["record_content_sha256"] = record["integrity"]["content_sha256"]; receipt["record_file_sha256"] = mod.sha256_bytes(raw); receipt["review_state"] = "INDEPENDENTLY_VERIFIED"; receipt = self.hash_receipt(receipt)
            rr = self.write_json(rp, receipt); member["rxep_receipt_sha256"] = receipt["receipt_sha256"]; member["rxep_receipt_file_sha256"] = mod.sha256_bytes(rr)
            with self.assertRaisesRegex(mod.ContributionSetError, "CALCULATED"):
                mod.build_set(self.make_request(root, [member]))

    def test_complete_status_not_yet_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = self.make_request(root, [self.make_member(root)])
            req = json.loads(request.read_text()); req["completeness_status"] = "DECLARED_SCOPE_COMPLETE"; self.write_json(request, req)
            with self.assertRaisesRegex(mod.ContributionSetError, "schema validation"):
                mod.build_set(request)


if __name__ == "__main__":
    unittest.main()
