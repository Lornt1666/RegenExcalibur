from __future__ import annotations

import copy
import json
import unittest

from reference import declaration_product_identity_closure as closure
from reference import declaration_evidence_bundle as v14

SRC = "a" * 64
PROCESS = "b" * 64
PROCESS_UUID = "57a4ae65-d305-421e-b21f-a3f0c35b8abe"
PRODUCT_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
PRODUCT_VERSION = "00.00.001"
FLOW_PROPERTY_UUID = "93a60a56-a3c8-11da-a746-0800200b9a66"
UNIT_GROUP_UUID = "ad38d542-3fe9-439d-9b95-2f5f7752acaf"


def pretty(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def seal_record(value: dict) -> dict:
    value = copy.deepcopy(value)
    value["integrity"] = {
        "content_sha256": v14.ZERO_DIGEST,
        "canonicalization": v14.CANONICALIZATION,
        "signature": None,
    }
    value["integrity"]["content_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(value))
    return value


def seal_receipt(value: dict) -> dict:
    value = copy.deepcopy(value)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(value))
    return value


def basis_fixture(version: str = "1.3") -> tuple[dict, bytes, dict]:
    record = seal_record({
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredReferenceBasis",
        "verdict": "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE",
        "parent": {
            "source_sha256": SRC,
            "process_xml_sha256": PROCESS,
            "process_dataset_uuid": PROCESS_UUID,
            "format_version": version,
        },
        "process_reference": {
            "exchange_amount_decimal": "1",
            "exchange_amount_lexical": "1.0",
            "product_flow_uuid": PRODUCT_UUID,
            "product_flow_version": PRODUCT_VERSION,
            "quantitative_reference_type": "Reference flow(s)",
            "reference_exchange_internal_id": "42",
        },
        "product_flow": {
            "names": [{"language": "en", "value": "wood panel"}],
            "reference_flow_property_internal_id": "0",
            "sha256": "c" * 64,
            "uuid": PRODUCT_UUID,
            "version": PRODUCT_VERSION,
        },
        "flow_property": {
            "flow_mean_decimal": "1",
            "flow_mean_lexical": "1.0",
            "master_sha256": "d" * 64,
            "names": [{"language": "en", "value": "Mass"}],
            "reference_unit_group_uuid": UNIT_GROUP_UUID,
            "uuid": FLOW_PROPERTY_UUID,
            "version": "03.00.000",
        },
        "reference_unit": {
            "factor_decimal": "1",
            "factor_lexical": "1",
            "name": "kg",
            "reference_unit_internal_id": "0",
            "unit_group_master_sha256": "e" * 64,
            "unit_group_uuid": UNIT_GROUP_UUID,
            "unit_group_version": "25.00.000",
        },
        "declared_reference_basis": {
            "basis_status": "IDENTITY_CHAIN_VERIFIED",
            "identity_chain": True,
            "product_flow_uuid": PRODUCT_UUID,
            "quantity_decimal": "1",
            "statement": "1 kg of the referenced product flow",
            "unit": "kg",
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    })
    raw = pretty(record)
    receipt = seal_receipt({
        "verdict": record["verdict"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": v14.sha256_bytes(raw),
        "source_sha256": SRC,
        "process_dataset_uuid": PROCESS_UUID,
        "format_version": version,
        "certified": False,
    })
    return record, raw, receipt


def v14_fixture(basis: dict, basis_raw: bytes, basis_receipt: dict, version: str = "1.3") -> tuple[dict, bytes, dict]:
    record = seal_record({
        "schema_version": "1.0",
        "record_type": "ProofGridDeclarationEvidenceBundle",
        "verdict": "DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE",
        "source_identity": {
            "source_sha256": SRC,
            "process_xml_sha256": PROCESS,
            "process_dataset_uuid": PROCESS_UUID,
            "format_version": version,
            "canonical_source_content_sha256": "f" * 64,
        },
        "parent_evidence": {
            "declared_indicators": {
                "record_content_sha256": "1" * 64,
                "record_file_sha256": "2" * 64,
                "receipt_sha256": "3" * 64,
            },
            "declared_reference_basis": {
                "record_content_sha256": basis["integrity"]["content_sha256"],
                "record_file_sha256": v14.sha256_bytes(basis_raw),
                "receipt_sha256": basis_receipt["receipt_sha256"],
            },
            "amount_semantics": {
                "evidence_file_sha256": "4" * 64,
                "integration_receipt_sha256": "5" * 64,
                "accepted_parent_v13_head": v14.V13_ACCEPTED_HEAD,
            },
        },
        "environmental_results": {
            "indicator_scope": {"canonical_unit": "kg CO2 eqv.", "code": "GWP-total"},
            "rows": [{"value_decimal": "15", "canonical_unit": "kg CO2 eqv."}],
            "row_count": 1,
            "value_origin": "DECLARED_IN_SOURCE",
            "aggregation_performed": False,
            "missing_modules_are_zero": False,
        },
        "declared_reference_basis": copy.deepcopy(basis["declared_reference_basis"]),
        "amount_semantics": {
            "format_version": version,
            "reference_exchange_internal_id": "42",
            "mean_amount": {"lexical": "1.0", "decimal": "1"},
            "resulting_amount_present": False,
            "resulting_amount": None,
            "selection_policy": v14.AMOUNT_POLICY,
        },
        "dimension_separation": {
            "environmental_result_unit": "kg CO2 eqv.",
            "product_reference_unit": "kg",
            "same_dimension": False,
            "unit_interchange_permitted": False,
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": ["test fixture"],
    })
    raw = pretty(record)
    receipt = seal_receipt({
        "verdict": record["verdict"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": v14.sha256_bytes(raw),
        "source_identity": copy.deepcopy(record["source_identity"]),
        "parent_evidence": copy.deepcopy(record["parent_evidence"]),
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    })
    return record, raw, receipt


def case(version: str = "1.3"):
    basis, basis_raw, basis_receipt = basis_fixture(version)
    parent, parent_raw, parent_receipt = v14_fixture(basis, basis_raw, basis_receipt, version)
    return parent, parent_raw, parent_receipt, basis, basis_raw, basis_receipt


def bind_case(values):
    return closure.bind(*values)


class DeclarationProductIdentityClosureTests(unittest.TestCase):
    def test_v12_and_v13_preserve_complete_identity_closure(self):
        for version in ("1.2", "1.3"):
            with self.subTest(version=version):
                record = bind_case(case(version))
                self.assertEqual(record["verdict"], closure.VERDICT)
                self.assertEqual(record["product_flow"]["uuid"], PRODUCT_UUID)
                self.assertEqual(record["product_flow"]["version"], PRODUCT_VERSION)
                self.assertEqual(record["product_flow"]["names"][0]["value"], "wood panel")
                self.assertEqual(record["flow_property"]["uuid"], FLOW_PROPERTY_UUID)
                self.assertEqual(record["flow_property"]["reference_unit_group_uuid"], UNIT_GROUP_UUID)
                self.assertEqual(record["reference_unit"]["name"], "kg")
                self.assertEqual(record["reference_unit"]["factor_decimal"], "1")
                self.assertFalse(record["building_quantity_multiplication_performed"])
                self.assertFalse(record["calculated"])
                self.assertFalse(record["certified"])

    def test_repeated_binding_is_byte_deterministic(self):
        values = case("1.3")
        self.assertEqual(closure.v14.canonical_json_bytes(bind_case(values)), closure.v14.canonical_json_bytes(bind_case(values)))

    def test_product_flow_uuid_mismatch_fails_even_if_basis_is_resealed(self):
        values = list(case("1.3"))
        basis = copy.deepcopy(values[3])
        basis["product_flow"]["uuid"] = "wrong-product"
        basis = seal_record({k: v for k, v in basis.items() if k != "integrity"})
        basis_raw = pretty(basis)
        basis_receipt = seal_receipt({
            "verdict": basis["verdict"], "record_content_sha256": basis["integrity"]["content_sha256"],
            "record_file_sha256": v14.sha256_bytes(basis_raw), "source_sha256": SRC,
            "process_dataset_uuid": PROCESS_UUID, "format_version": "1.3", "certified": False,
        })
        values[3:6] = [basis, basis_raw, basis_receipt]
        with self.assertRaisesRegex(closure.ClosureError, "product-flow UUID closure mismatch"):
            bind_case(tuple(values))

    def test_product_flow_version_mismatch_fails(self):
        basis, _, _ = basis_fixture("1.3")
        basis["product_flow"]["version"] = "99.99.999"
        with self.assertRaisesRegex(closure.ClosureError, "product-flow version closure mismatch"):
            closure.validate_internal_identity(basis)

    def test_reference_exchange_mismatch_fails(self):
        values = list(case("1.3"))
        parent = copy.deepcopy(values[0])
        parent["amount_semantics"]["reference_exchange_internal_id"] = "99"
        parent = seal_record({k: v for k, v in parent.items() if k != "integrity"})
        parent_raw = pretty(parent)
        parent_receipt = seal_receipt({
            "verdict": parent["verdict"], "record_content_sha256": parent["integrity"]["content_sha256"],
            "record_file_sha256": v14.sha256_bytes(parent_raw), "source_identity": parent["source_identity"],
            "parent_evidence": parent["parent_evidence"], "calculated": False,
            "environmental_values_transformed": False, "building_quantity_multiplication_performed": False,
            "aggregation_performed": False, "unit_conversion_performed": False,
            "scientific_validation_performed": False, "professional_review_performed": False, "certified": False,
        })
        values[:3] = [parent, parent_raw, parent_receipt]
        with self.assertRaisesRegex(closure.ClosureError, "amount-semantics/reference-exchange mismatch"):
            bind_case(tuple(values))

    def test_v14_parent_basis_hash_mismatch_fails(self):
        values = list(case("1.3"))
        parent = copy.deepcopy(values[0])
        parent["parent_evidence"]["declared_reference_basis"]["record_content_sha256"] = "9" * 64
        parent = seal_record({k: v for k, v in parent.items() if k != "integrity"})
        parent_raw = pretty(parent)
        parent_receipt = seal_receipt({
            "verdict": parent["verdict"], "record_content_sha256": parent["integrity"]["content_sha256"],
            "record_file_sha256": v14.sha256_bytes(parent_raw), "source_identity": parent["source_identity"],
            "parent_evidence": parent["parent_evidence"], "calculated": False,
            "environmental_values_transformed": False, "building_quantity_multiplication_performed": False,
            "aggregation_performed": False, "unit_conversion_performed": False,
            "scientific_validation_performed": False, "professional_review_performed": False, "certified": False,
        })
        values[:3] = [parent, parent_raw, parent_receipt]
        with self.assertRaisesRegex(closure.ClosureError, "basis content-hash mismatch"):
            bind_case(tuple(values))

    def test_source_process_mismatch_fails(self):
        values = list(case("1.3"))
        parent = copy.deepcopy(values[0])
        parent["source_identity"]["source_sha256"] = "8" * 64
        parent = seal_record({k: v for k, v in parent.items() if k != "integrity"})
        parent_raw = pretty(parent)
        parent_receipt = seal_receipt({
            "verdict": parent["verdict"], "record_content_sha256": parent["integrity"]["content_sha256"],
            "record_file_sha256": v14.sha256_bytes(parent_raw), "source_identity": parent["source_identity"],
            "parent_evidence": parent["parent_evidence"], "calculated": False,
            "environmental_values_transformed": False, "building_quantity_multiplication_performed": False,
            "aggregation_performed": False, "unit_conversion_performed": False,
            "scientific_validation_performed": False, "professional_review_performed": False, "certified": False,
        })
        values[:3] = [parent, parent_raw, parent_receipt]
        with self.assertRaisesRegex(closure.ClosureError, "source SHA-256 mismatch"):
            bind_case(tuple(values))

    def test_flow_property_unit_group_mismatch_fails(self):
        basis, _, _ = basis_fixture("1.3")
        basis["flow_property"]["reference_unit_group_uuid"] = "wrong-group"
        with self.assertRaisesRegex(closure.ClosureError, "flow-property/reference-unit-group mismatch"):
            closure.validate_internal_identity(basis)

    def test_reference_unit_name_and_factor_mutations_fail(self):
        basis, _, _ = basis_fixture("1.3")
        basis["reference_unit"]["name"] = "g"
        with self.assertRaisesRegex(closure.ClosureError, "reference-unit/basis-unit mismatch"):
            closure.validate_internal_identity(basis)
        basis, _, _ = basis_fixture("1.3")
        basis["reference_unit"]["factor_decimal"] = "1000"
        with self.assertRaisesRegex(closure.ClosureError, "non-identity reference-unit factor"):
            closure.validate_internal_identity(basis)

    def test_certification_promotion_fails(self):
        values = list(case("1.3"))
        parent = copy.deepcopy(values[0])
        parent["certified"] = True
        parent = seal_record({k: v for k, v in parent.items() if k != "integrity"})
        parent_raw = pretty(parent)
        parent_receipt = seal_receipt({
            "verdict": parent["verdict"], "record_content_sha256": parent["integrity"]["content_sha256"],
            "record_file_sha256": v14.sha256_bytes(parent_raw), "source_identity": parent["source_identity"],
            "parent_evidence": parent["parent_evidence"], "calculated": False,
            "environmental_values_transformed": False, "building_quantity_multiplication_performed": False,
            "aggregation_performed": False, "unit_conversion_performed": False,
            "scientific_validation_performed": False, "professional_review_performed": False, "certified": False,
        })
        values[:3] = [parent, parent_raw, parent_receipt]
        with self.assertRaisesRegex(closure.ClosureError, "certified promotion rejected"):
            bind_case(tuple(values))


if __name__ == "__main__":
    unittest.main()
