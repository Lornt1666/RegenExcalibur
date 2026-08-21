from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from reference import declaration_evidence_bundle as v14
from reference import ifc_declaration_product_map as v15
from reference import mapped_declared_result_scale as scaler
from tests.test_ifc_declaration_product_map import declaration_parent, write_json

INDICATOR_UUID = "6a37f984-a4b3-458a-a20a-64418c145fa2"
PRODUCT_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
PRODUCT_VERSION = "00.00.001"


def reseal_record(record: dict) -> dict:
    result = copy.deepcopy(record)
    result["integrity"]["content_sha256"] = scaler.ZERO_DIGEST
    result["integrity"]["content_sha256"] = scaler.sha256_bytes(scaler.canonical_json_bytes(result))
    return result


def reseal_receipt(receipt: dict) -> dict:
    result = copy.deepcopy(receipt)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = scaler.sha256_bytes(scaler.canonical_json_bytes(result))
    return result


def fixture(root: Path):
    bundle_path, bundle_receipt_path, _, _, bundle, bundle_receipt, _, _ = declaration_parent(root)
    # Replace the minimal v1.5 unit-test environmental row with the exact v1.6 positive control semantics.
    bundle = copy.deepcopy(bundle)
    bundle["environmental_results"] = {
        "indicator_scope": {
            "canonical_unit": "kg CO2 eqv.",
            "catalogue": "EN15804+A2_EF3.0",
            "catalogue_version": "04.00.016",
            "code": "GWP-total",
            "indicator_uuid": INDICATOR_UUID,
            "unit_group_uuid": "1ebf3012-d0db-4de2-aefd-ef30cedb0be1",
        },
        "rows": [{
            "calculated": False,
            "canonical_unit": "kg CO2 eqv.",
            "indicator_uuid": INDICATOR_UUID,
            "module": "A1-A3",
            "reference_unit_internal_id": "0",
            "reference_unit_mean_value_decimal": "1",
            "reference_unit_name": "kg CO2-Äqv.",
            "scenario": None,
            "source_location": {"amount_ordinal": 1, "lcia_result_ordinal": 7, "path": "processDataSet/LCIAResults/LCIAResult[7]/other/amount[1]"},
            "source_reference_version": None,
            "unit_conversion_performed": False,
            "unit_group_uuid": "1ebf3012-d0db-4de2-aefd-ef30cedb0be1",
            "value_decimal": "15.559479677163699",
            "value_lexical": "15.559479677163699",
            "value_origin": "DECLARED_IN_SOURCE",
        }],
        "row_count": 1,
        "value_origin": "DECLARED_IN_SOURCE",
        "aggregation_performed": False,
        "missing_modules_are_zero": False,
    }
    bundle = reseal_record(bundle)
    bundle_raw = write_json(bundle_path, bundle)
    bundle_receipt = copy.deepcopy(bundle_receipt)
    bundle_receipt["record_content_sha256"] = bundle["integrity"]["content_sha256"]
    bundle_receipt["record_file_sha256"] = scaler.sha256_bytes(bundle_raw)
    bundle_receipt["row_count"] = 1
    bundle_receipt = reseal_receipt(bundle_receipt)
    write_json(bundle_receipt_path, bundle_receipt)

    mapping = {
        "schema_version": "1.0",
        "record_type": "ProofGridIFCDeclarationProductMapping",
        "verdict": v15.VERDICT,
        "mapping_id": "RX-V16-PARENT-MAP",
        "ifc": {
            "extraction_file_sha256": "a" * 64,
            "source_sha256": "b" * 64,
            "schema": "IFC4",
            "element": {"step_id": 4, "global_id": "1BXL7DJx51bvggyIPU2Xi5", "ifc_type": "IfcWall", "name": "Mapped Wall"},
            "material": {"association_step_id": 6, "material_step_id": 5, "declared_name": "UNRELATED-NAME", "source_type": "IfcMaterial"},
            "quantity": {
                "set_step_id": 8,
                "quantity_step_id": 7,
                "name": "Mass",
                "ifc_quantity_type": "IfcQuantityWeight",
                "value": 1000.0,
                "unit_identity": "kg",
                "unit": {"unit_type": "MASSUNIT", "name": "GRAM", "prefix": "KILO", "source": "project_unit_context"},
                "value_source": "IfcElementQuantity",
                "numerical_conversion_applied": False,
            },
        },
        "declaration": {
            "bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "bundle_receipt_sha256": bundle_receipt["receipt_sha256"],
            "source_sha256": bundle["source_identity"]["source_sha256"],
            "process_dataset_uuid": bundle["source_identity"]["process_dataset_uuid"],
            "basis_record_content_sha256": bundle["parent_evidence"]["declared_reference_basis"]["record_content_sha256"],
            "basis_receipt_sha256": bundle["parent_evidence"]["declared_reference_basis"]["receipt_sha256"],
            "product_flow_uuid": PRODUCT_UUID,
            "product_flow_version": PRODUCT_VERSION,
            "reference_quantity_decimal": "1",
            "reference_unit": "kg",
        },
        "review": {"state": "REVIEWED_MAPPING_DECISION", "reviewer": "synthetic", "role": "test", "rationale": "explicit IDs", "reference": "v1.6-test"},
        "mapping_artifact": {"file_sha256": "c" * 64, "artifact_version": "1.5.0"},
        "mapping_method": v15.MAPPING_METHOD,
        "fuzzy_matching_performed": False,
        "automatic_name_mapping_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": ["synthetic v1.6 parent mapping"],
        "integrity": {"content_sha256": scaler.ZERO_DIGEST, "canonicalization": scaler.CANONICALIZATION, "signature": None},
    }
    mapping = reseal_record(mapping)
    mapping_path = root / "mapping-result.json"
    mapping_raw = write_json(mapping_path, mapping)
    mapping_receipt = v15.build_receipt(mapping, mapping_raw)
    mapping_receipt_path = root / "mapping-receipt.json"
    write_json(mapping_receipt_path, mapping_receipt)

    request = {
        "schema_version": "1.0",
        "request_version": "1.6.0",
        "bindings": {
            "mapping_record_content_sha256": mapping["integrity"]["content_sha256"],
            "mapping_receipt_sha256": mapping_receipt["receipt_sha256"],
            "declaration_bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "declaration_bundle_receipt_sha256": bundle_receipt["receipt_sha256"],
        },
        "selection": {"indicator_uuid": INDICATOR_UUID, "module": "A1-A3", "scenario": None},
    }
    request_path = root / "request.json"
    write_json(request_path, request)
    return mapping_path, mapping_receipt_path, bundle_path, bundle_receipt_path, request_path, mapping, mapping_receipt, bundle, bundle_receipt, request


class MappedDeclaredResultScalingTests(unittest.TestCase):
    def run_scale(self, f):
        return scaler.scale(*f[:5])

    def test_exact_decimal_positive_control(self):
        with tempfile.TemporaryDirectory() as td:
            f = fixture(Path(td))
            record = self.run_scale(f)
            self.assertEqual(record["verdict"], scaler.VERDICT)
            self.assertEqual(record["calculation"]["mapped_quantity"]["value_decimal"], "1000")
            self.assertEqual(record["calculation"]["reference_quantity"]["value_decimal"], "1")
            self.assertEqual(record["calculation"]["declared_result"]["value_decimal"], "15.559479677163699")
            self.assertEqual(record["calculation"]["scale_factor_decimal"], "1000")
            self.assertEqual(record["calculation"]["scaled_result_decimal"], "15559.479677163699")
            self.assertEqual(record["calculation"]["scaled_result_unit"], "kg CO2 eqv.")
            self.assertTrue(record["calculation_performed"])
            self.assertFalse(record["aggregation_performed"])
            self.assertFalse(record["missing_modules_are_zero"])
            self.assertFalse(record["unit_conversion_performed"])
            self.assertFalse(record["certified"])

    def test_wrong_scenario_does_not_default_infer(self):
        with tempfile.TemporaryDirectory() as td:
            f = fixture(Path(td)); path=f[4]; request=copy.deepcopy(f[9])
            request["selection"]["scenario"] = {"name": "default", "group": "x", "default": True}
            write_json(path, request)
            with self.assertRaisesRegex(scaler.ScalingError, "found 0"):
                self.run_scale(f)

    def test_duplicate_exact_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f = fixture(Path(td)); bundle_path=f[2]; receipt_path=f[3]; bundle=copy.deepcopy(f[7]); receipt=copy.deepcopy(f[8]); request_path=f[4]; request=copy.deepcopy(f[9]); mapping_path=f[0]; mapping_receipt_path=f[1]; mapping=copy.deepcopy(f[5]); mapping_receipt=copy.deepcopy(f[6])
            bundle["environmental_results"]["rows"].append(copy.deepcopy(bundle["environmental_results"]["rows"][0]))
            bundle["environmental_results"]["row_count"] = 2
            bundle=reseal_record(bundle); raw=write_json(bundle_path,bundle)
            receipt["record_content_sha256"]=bundle["integrity"]["content_sha256"]; receipt["record_file_sha256"]=scaler.sha256_bytes(raw); receipt["row_count"]=2; receipt=reseal_receipt(receipt); write_json(receipt_path,receipt)
            mapping["declaration"]["bundle_content_sha256"]=bundle["integrity"]["content_sha256"]; mapping["declaration"]["bundle_receipt_sha256"]=receipt["receipt_sha256"]; mapping=reseal_record(mapping); mraw=write_json(mapping_path,mapping); mapping_receipt=v15.build_receipt(mapping,mraw); write_json(mapping_receipt_path,mapping_receipt)
            request["bindings"].update({"mapping_record_content_sha256":mapping["integrity"]["content_sha256"],"mapping_receipt_sha256":mapping_receipt["receipt_sha256"],"declaration_bundle_content_sha256":bundle["integrity"]["content_sha256"],"declaration_bundle_receipt_sha256":receipt["receipt_sha256"]}); write_json(request_path,request)
            with self.assertRaisesRegex(scaler.ScalingError, "found 2"):
                scaler.scale(mapping_path,mapping_receipt_path,bundle_path,receipt_path,request_path)

    def test_source_row_calculated_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture(Path(td)); bundle_path=f[2]; receipt_path=f[3]; bundle=copy.deepcopy(f[7]); receipt=copy.deepcopy(f[8])
            bundle["environmental_results"]["rows"][0]["calculated"]=True
            bundle=reseal_record(bundle); raw=write_json(bundle_path,bundle); receipt["record_content_sha256"]=bundle["integrity"]["content_sha256"]; receipt["record_file_sha256"]=scaler.sha256_bytes(raw); receipt=reseal_receipt(receipt); write_json(receipt_path,receipt)
            with self.assertRaises(scaler.ScalingError):
                self.run_scale(f)

    def test_mapping_receipt_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture(Path(td)); path=f[1]; receipt=copy.deepcopy(f[6]); receipt["certified"]=True; receipt=reseal_receipt(receipt); write_json(path,receipt)
            with self.assertRaisesRegex(scaler.ScalingError, "certification"):
                self.run_scale(f)

    def test_mapping_unit_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture(Path(td)); path=f[0]; receipt_path=f[1]; mapping=copy.deepcopy(f[5]); mapping["ifc"]["quantity"]["unit_identity"]="lb"; mapping=reseal_record(mapping); raw=write_json(path,mapping); receipt=v15.build_receipt(mapping,raw); write_json(receipt_path,receipt)
            with self.assertRaisesRegex(scaler.ScalingError, "must be kg"):
                self.run_scale(f)

    def test_stale_request_binding_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture(Path(td)); path=f[4]; request=copy.deepcopy(f[9]); request["bindings"]["mapping_receipt_sha256"]="0"*64; write_json(path,request)
            with self.assertRaisesRegex(scaler.ScalingError, "request/mapping receipt"):
                self.run_scale(f)

    def test_repeat_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture(Path(td)); a=self.run_scale(f); b=self.run_scale(f)
            self.assertEqual(scaler.canonical_json_bytes(a),scaler.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"],b["integrity"]["content_sha256"])


if __name__ == "__main__":
    unittest.main()
