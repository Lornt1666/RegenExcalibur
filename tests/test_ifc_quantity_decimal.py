from __future__ import annotations

import copy
import json
import unittest

from reference import ifc_declaration_product_map as v15
from reference import ifc_quantity_decimal as quantity

PRODUCT_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
PRODUCT_VERSION = "00.00.001"


def source_bytes(token: str = "1000.", *, entity_type: str = "IFCQUANTITYWEIGHT", step_id: int = 7, duplicate: bool = False, name: str = "Mass") -> bytes:
    entity = f"#{step_id}={entity_type}('{name}',$,$,{token},$);"
    duplicate_entity = f"\n#{step_id}={entity_type}('{name}',$,$,{token},$);" if duplicate else ""
    return (
        "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        "FILE_NAME('fixture.ifc','2026-01-01T00:00:00',(),(),'ProofGrid','ProofGrid','');\n"
        "FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
        + entity + duplicate_entity + "\nENDSEC;\nEND-ISO-10303-21;\n"
    ).encode("ascii")


def seal_record(value: dict) -> dict:
    value = copy.deepcopy(value)
    value["integrity"] = {
        "content_sha256": quantity.ZERO_DIGEST,
        "canonicalization": quantity.CANONICALIZATION,
        "signature": None,
    }
    value["integrity"]["content_sha256"] = quantity.sha256_bytes(quantity.canonical_json_bytes(value))
    return value


def seal_receipt(value: dict) -> dict:
    value = copy.deepcopy(value)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = quantity.sha256_bytes(quantity.canonical_json_bytes(value))
    return value


def mapping_fixture(raw_source: bytes, *, parser_value: float = 1000.0, step_id: int = 7, unit_identity: str = "kg", entity_type: str = "IfcQuantityWeight", name: str = "Mass") -> tuple[dict, bytes, dict]:
    record = seal_record({
        "schema_version": "1.0",
        "record_type": "ProofGridIFCDeclarationProductMapping",
        "verdict": v15.VERDICT,
        "mapping_id": "RX-V15-MAP-001",
        "ifc": {
            "extraction_file_sha256": "1" * 64,
            "source_sha256": quantity.sha256_bytes(raw_source),
            "schema": "IFC4",
            "element": {"step_id": 3, "global_id": "1BXL7DJx51bvggyIPU2Xi5", "ifc_type": "IfcWall", "name": "Mapped Wall"},
            "material": {"association_step_id": 5, "material_step_id": 4, "declared_name": "RX-MATERIAL-UNRELATED-TO-WOOD-PANEL", "source_type": "IfcMaterial"},
            "quantity": {
                "set_step_id": 8,
                "quantity_step_id": step_id,
                "name": name,
                "ifc_quantity_type": entity_type,
                "value": parser_value,
                "unit_identity": unit_identity,
                "unit": {"step_id": 1, "ifc_type": "IfcSIUnit", "unit_type": "MASSUNIT", "name": "GRAM", "prefix": "KILO", "source": "project_unit_context"},
                "value_source": "declared_ifc_element_quantity",
                "numerical_conversion_applied": False,
            },
        },
        "declaration": {
            "closure_content_sha256": "2" * 64,
            "closure_receipt_sha256": "3" * 64,
            "source_sha256": "4" * 64,
            "process_xml_sha256": "5" * 64,
            "process_dataset_uuid": "57a4ae65-d305-421e-b21f-a3f0c35b8abe",
            "format_version": "1.3",
            "product_flow_uuid": PRODUCT_UUID,
            "product_flow_version": PRODUCT_VERSION,
            "product_flow_sha256": "6" * 64,
            "reference_quantity_decimal": "1",
            "reference_unit": "kg",
        },
        "review": {"state": "REVIEWED_MAPPING_DECISION", "reviewer": "synthetic reviewer", "role": "test", "rationale": "exact IDs", "reference": "unit-test"},
        "mapping_artifact": {"file_sha256": "7" * 64, "artifact_version": "1.5.0"},
        "mapping_method": "EXPLICIT_REVIEWED_ARTIFACT",
        "fuzzy_matching_performed": False,
        "automatic_name_mapping_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": ["test fixture"],
    })
    raw = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt = seal_receipt({
        "verdict": v15.VERDICT,
        "certified": False,
        "engine": {"name": v15.ENGINE_NAME, "version": v15.ENGINE_VERSION},
        "mapping_id": record["mapping_id"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": quantity.sha256_bytes(raw),
        "ifc_source_sha256": record["ifc"]["source_sha256"],
        "closure_content_sha256": record["declaration"]["closure_content_sha256"],
        "closure_receipt_sha256": record["declaration"]["closure_receipt_sha256"],
        "product_flow_uuid": PRODUCT_UUID,
        "product_flow_version": PRODUCT_VERSION,
        "reference_unit": "kg",
        "mapping_method": "EXPLICIT_REVIEWED_ARTIFACT",
        "fuzzy_matching_performed": False,
        "automatic_name_mapping_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": ["test fixture"],
    })
    return record, raw, receipt


class IFCQuantityDecimalTests(unittest.TestCase):
    def test_source_lexical_is_authority(self):
        raw_source = source_bytes("1000.")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        record = quantity.extract(mapping, mapping_raw, receipt, raw_source)
        self.assertEqual(record["verdict"], quantity.VERDICT)
        self.assertEqual(record["quantity"]["quantity_lexical"], "1000.")
        self.assertEqual(record["quantity"]["quantity_decimal"], "1000")
        self.assertEqual(record["quantity"]["mapped_parser_numeric_string"], "1000.0")
        self.assertTrue(record["quantity"]["source_token_is_authority"])
        self.assertFalse(record["quantity"]["parser_numeric_value_is_authority"])
        self.assertFalse(record["calculation_performed"])
        self.assertFalse(record["certified"])

    def test_exponent_token_canonicalizes_without_float_authority(self):
        raw_source = source_bytes("1.E+3")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        record = quantity.extract(mapping, mapping_raw, receipt, raw_source)
        self.assertEqual(record["quantity"]["quantity_lexical"], "1.E+3")
        self.assertEqual(record["quantity"]["quantity_decimal"], "1000")

    def test_source_hash_mismatch_rejected(self):
        raw_source = source_bytes()
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "raw IFC source SHA-256 mismatch"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source + b" ")

    def test_missing_quantity_step_id_rejected(self):
        raw_source = source_bytes(step_id=8)
        mapping, mapping_raw, receipt = mapping_fixture(raw_source, step_id=7)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "missing or ambiguous"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_duplicate_quantity_step_id_rejected(self):
        raw_source = source_bytes(duplicate=True)
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "missing or ambiguous: 2"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_wrong_entity_type_rejected(self):
        raw_source = source_bytes(entity_type="IFCQUANTITYLENGTH")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "entity type mismatch"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_malformed_numeric_token_rejected(self):
        raw_source = source_bytes("not-a-number")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "unsupported or malformed STEP numeric token"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_nonfinite_numeric_token_rejected(self):
        raw_source = source_bytes("NaN")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        with self.assertRaises(quantity.QuantityDecimalError):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_parser_numeric_disagreement_rejected(self):
        raw_source = source_bytes("1000.")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source, parser_value=999.0)
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "parser quantity disagrees"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_non_kg_mapped_unit_rejected(self):
        raw_source = source_bytes("1000.")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source, unit_identity="g")
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "requires mapped unit identity kg"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_mapping_receipt_tamper_rejected(self):
        raw_source = source_bytes()
        mapping, mapping_raw, receipt = mapping_fixture(raw_source)
        receipt["ifc_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "receipt digest mismatch"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_quantity_name_mismatch_rejected(self):
        raw_source = source_bytes(name="Gross Mass")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source, name="Mass")
        with self.assertRaisesRegex(quantity.QuantityDecimalError, "quantity source name mismatch"):
            quantity.extract(mapping, mapping_raw, receipt, raw_source)

    def test_step_splitter_ignores_semicolon_inside_string(self):
        raw_source = source_bytes(name="Mass; gross")
        mapping, mapping_raw, receipt = mapping_fixture(raw_source, name="Mass; gross")
        record = quantity.extract(mapping, mapping_raw, receipt, raw_source)
        self.assertEqual(record["ifc_identity"]["quantity_name"], "Mass; gross")


if __name__ == "__main__":
    unittest.main()
