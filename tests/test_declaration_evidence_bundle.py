from __future__ import annotations

import copy
import json
import unittest

from reference import declaration_evidence_bundle as bundle

SRC = "a" * 64
PROCESS = "b" * 64
UUID = "57a4ae65-d305-421e-b21f-a3f0c35b8abe"
FLOW_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"


def seal_record(value: dict) -> dict:
    value = copy.deepcopy(value)
    value["integrity"] = {
        "content_sha256": bundle.ZERO_DIGEST,
        "canonicalization": bundle.CANONICALIZATION,
    }
    value["integrity"]["content_sha256"] = bundle.sha256_bytes(bundle.canonical_json_bytes(value))
    return value


def pretty_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def seal_receipt(value: dict) -> dict:
    value = copy.deepcopy(value)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = bundle.sha256_bytes(bundle.canonical_json_bytes(value))
    return value


def canonical_source(version: str) -> dict:
    if version == "1.2":
        conf = {
            "profile_validation_performed": True,
            "official_stack": copy.deepcopy(bundle.EXPECTED_V12_STACK),
            "official_stack_sha256": bundle.EXPECTED_V12_STACK_SHA256,
            "claim_token": "OEKOBAUDAT_V12_PROFILE_380_SYNTHETIC_AUTHORITY_SAFE_COMPATIBLE",
            "error_count": 0,
        }
    else:
        conf = {
            "profile_validation_performed": False,
            "verdict": "ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT",
            "xsd_validation": True,
            "master_data_identity_validation": True,
        }
    return seal_record({
        "verdict": "ADMITTED_ENVIRONMENTAL_SOURCE_IDENTITY_VERIFIABLE",
        "id": f"rx-source:{version}:{UUID}",
        "source": {"sha256": SRC, "format_version": version},
        "identity": {"process_xml_sha256": PROCESS, "process_dataset_uuid": UUID},
        "conformance": conf,
        "certified": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
    })


def indicator(version: str, canonical: dict, *, env_unit: str = "kg CO2 eqv.") -> tuple[dict, bytes, dict]:
    record = seal_record({
        "verdict": "DECLARED_ENVIRONMENTAL_INDICATORS_EXTRACTED_VERIFIABLE",
        "canonical_source": {
            "content_sha256": canonical["integrity"]["content_sha256"],
            "record_id": canonical["id"],
            "verdict": canonical["verdict"],
        },
        "source": {
            "sha256": SRC,
            "process_xml_sha256": PROCESS,
            "process_dataset_uuid": UUID,
            "format_version": version,
        },
        "indicator_scope": {"canonical_unit": env_unit, "indicator_uuid": "gwp", "code": "GWP-total"},
        "rows": [{
            "canonical_unit": env_unit,
            "indicator_uuid": "gwp",
            "module": "A1-A3",
            "scenario": None,
            "value_lexical": "15.0",
            "value_decimal": "15",
            "value_origin": "DECLARED_IN_SOURCE",
            "calculated": False,
            "unit_conversion_performed": False,
        }],
        "calculated": False,
        "unit_conversion_performed": False,
        "professional_review_performed": False,
        "certified": False,
    })
    raw = pretty_bytes(record)
    receipt = seal_receipt({
        "verdict": record["verdict"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": bundle.sha256_bytes(raw),
        "source_sha256": SRC,
        "process_xml_sha256": PROCESS,
        "process_dataset_uuid": UUID,
        "format_version": version,
        "certified": False,
    })
    return record, raw, receipt


def basis_record(version: str, *, source_sha: str = SRC, process_sha: str = PROCESS) -> tuple[dict, bytes, dict]:
    record = seal_record({
        "verdict": "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE",
        "parent": {
            "source_sha256": source_sha,
            "process_xml_sha256": process_sha,
            "process_dataset_uuid": UUID,
            "format_version": version,
        },
        "process_reference": {
            "reference_exchange_internal_id": "42",
            "exchange_amount_lexical": "1.0",
            "exchange_amount_decimal": "1",
            "product_flow_uuid": FLOW_UUID,
        },
        "declared_reference_basis": {
            "basis_status": "IDENTITY_CHAIN_VERIFIED",
            "identity_chain": True,
            "product_flow_uuid": FLOW_UUID,
            "quantity_decimal": "1",
            "unit": "kg",
            "statement": "1 kg of the referenced product flow",
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "professional_review_performed": False,
        "certified": False,
    })
    raw = pretty_bytes(record)
    receipt = seal_receipt({
        "verdict": record["verdict"],
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": bundle.sha256_bytes(raw),
        "source_sha256": source_sha,
        "process_dataset_uuid": UUID,
        "format_version": version,
        "certified": False,
    })
    return record, raw, receipt


def semantics(version: str, *, resulting: bool = False) -> tuple[dict, bytes, dict]:
    evidence = {
        "format_version": version,
        "reference_exchange_internal_id": "42",
        "mean_amount": {"lexical": "1.0", "decimal": "1"},
        "resulting_amount_present": resulting,
        "resulting_amount": {"lexical": "1.0", "decimal": "1"} if resulting else None,
        "selection_policy": bundle.AMOUNT_POLICY,
    }
    raw = pretty_bytes(evidence)
    receipt = {
        "verdict": "REFERENCE_EXCHANGE_AMOUNT_SEMANTICS_RESOLVED_VERIFIABLE",
        "accepted_parent_v13_head": bundle.V13_ACCEPTED_HEAD,
        "selection_policy": bundle.AMOUNT_POLICY,
        "controlled_resulting_amount_rejected": True,
        "building_quantity_multiplication_permitted": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "v12_evidence_file_sha256": bundle.sha256_bytes(raw) if version == "1.2" else "1" * 64,
        "v13_evidence_file_sha256": bundle.sha256_bytes(raw) if version == "1.3" else "2" * 64,
        "resulting_amount_absent_in_pinned_v12": not resulting if version == "1.2" else True,
        "resulting_amount_absent_in_pinned_v13": not resulting if version == "1.3" else True,
    }
    return evidence, raw, seal_receipt(receipt)


def make_case(version: str = "1.2", *, env_unit: str = "kg CO2 eqv."):
    canonical = canonical_source(version)
    ind, ind_raw, ind_receipt = indicator(version, canonical, env_unit=env_unit)
    bas, bas_raw, bas_receipt = basis_record(version)
    sem, sem_raw, sem_receipt = semantics(version)
    return canonical, ind, ind_raw, ind_receipt, bas, bas_raw, bas_receipt, sem, sem_raw, sem_receipt


def bind_case(case):
    canonical, ind, ind_raw, ind_receipt, bas, bas_raw, bas_receipt, sem, sem_raw, sem_receipt = case
    return bundle.bind(
        canonical,
        indicator_record=ind,
        indicator_raw=ind_raw,
        indicator_receipt=ind_receipt,
        basis_record=bas,
        basis_raw=bas_raw,
        basis_receipt=bas_receipt,
        semantics_evidence=sem,
        semantics_raw=sem_raw,
        semantics_integration_receipt=sem_receipt,
    )


class DeclarationEvidenceBundleTests(unittest.TestCase):
    def test_v12_and_v13_bind_without_calculation(self):
        for version in ("1.2", "1.3"):
            with self.subTest(version=version):
                record = bind_case(make_case(version))
                self.assertEqual(record["verdict"], bundle.VERDICT)
                self.assertEqual(record["environmental_results"]["row_count"], 1)
                self.assertEqual(record["declared_reference_basis"]["quantity_decimal"], "1")
                self.assertEqual(record["declared_reference_basis"]["unit"], "kg")
                self.assertEqual(record["dimension_separation"]["environmental_result_unit"], "kg CO2 eqv.")
                self.assertFalse(record["dimension_separation"]["unit_interchange_permitted"])
                self.assertFalse(record["building_quantity_multiplication_performed"])
                self.assertFalse(record["calculated"])
                self.assertFalse(record["certified"])

    def test_repeated_binding_is_deterministic(self):
        case = make_case("1.2")
        a = bind_case(case)
        b = bind_case(case)
        self.assertEqual(bundle.canonical_json_bytes(a), bundle.canonical_json_bytes(b))

    def test_cross_source_substitution_fails_even_when_basis_is_resealed(self):
        case = list(make_case("1.2"))
        bas, _, _ = basis_record("1.2", source_sha="c" * 64)
        bas_raw = pretty_bytes(bas)
        bas_receipt = seal_receipt({
            "verdict": bas["verdict"],
            "record_content_sha256": bas["integrity"]["content_sha256"],
            "record_file_sha256": bundle.sha256_bytes(bas_raw),
            "source_sha256": "c" * 64,
            "process_dataset_uuid": UUID,
            "format_version": "1.2",
            "certified": False,
        })
        case[4:7] = [bas, bas_raw, bas_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "parent source SHA-256 mismatch"):
            bind_case(tuple(case))

    def test_process_xml_substitution_fails(self):
        case = list(make_case("1.3"))
        bas, _, _ = basis_record("1.3", process_sha="d" * 64)
        bas_raw = pretty_bytes(bas)
        bas_receipt = seal_receipt({
            "verdict": bas["verdict"],
            "record_content_sha256": bas["integrity"]["content_sha256"],
            "record_file_sha256": bundle.sha256_bytes(bas_raw),
            "source_sha256": SRC,
            "process_dataset_uuid": UUID,
            "format_version": "1.3",
            "certified": False,
        })
        case[4:7] = [bas, bas_raw, bas_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "parent process XML SHA-256 mismatch"):
            bind_case(tuple(case))

    def test_tampered_indicator_receipt_fails(self):
        case = list(make_case("1.2"))
        receipt = copy.deepcopy(case[3])
        receipt["source_sha256"] = "f" * 64
        case[3] = receipt
        with self.assertRaisesRegex(bundle.BundleError, "receipt digest mismatch"):
            bind_case(tuple(case))

    def test_v12_forged_official_stack_fails(self):
        case = list(make_case("1.2"))
        canonical = copy.deepcopy(case[0])
        canonical["conformance"]["official_stack"]["validator"]["jar_sha256"] = "9" * 64
        canonical = seal_record({k: v for k, v in canonical.items() if k != "integrity"})
        ind, ind_raw, ind_receipt = indicator("1.2", canonical)
        case[0:4] = [canonical, ind, ind_raw, ind_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "official validator/profile stack mismatch"):
            bind_case(tuple(case))

    def test_v13_profile_promotion_fails(self):
        case = list(make_case("1.3"))
        canonical = copy.deepcopy(case[0])
        canonical["conformance"]["profile_validation_performed"] = True
        canonical = seal_record({k: v for k, v in canonical.items() if k != "integrity"})
        ind, ind_raw, ind_receipt = indicator("1.3", canonical)
        case[0:4] = [canonical, ind, ind_raw, ind_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "v1.3 profile overclaim rejected"):
            bind_case(tuple(case))

    def test_unresolved_resulting_amount_fails(self):
        case = list(make_case("1.3"))
        sem, sem_raw, sem_receipt = semantics("1.3", resulting=True)
        case[7:10] = [sem, sem_raw, sem_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "unresolved resultingAmount rejected|pinned absence proof missing"):
            bind_case(tuple(case))

    def test_environmental_product_unit_conflation_fails(self):
        with self.assertRaisesRegex(bundle.BundleError, "must remain distinct dimensions"):
            bind_case(make_case("1.2", env_unit="kg"))

    def test_parent_certification_promotion_fails(self):
        case = list(make_case("1.2"))
        ind = copy.deepcopy(case[1])
        ind["certified"] = True
        ind = seal_record({k: v for k, v in ind.items() if k != "integrity"})
        ind_raw = pretty_bytes(ind)
        ind_receipt = seal_receipt({
            "verdict": ind["verdict"],
            "record_content_sha256": ind["integrity"]["content_sha256"],
            "record_file_sha256": bundle.sha256_bytes(ind_raw),
            "source_sha256": SRC,
            "process_xml_sha256": PROCESS,
            "process_dataset_uuid": UUID,
            "format_version": "1.2",
            "certified": False,
        })
        case[1:4] = [ind, ind_raw, ind_receipt]
        with self.assertRaisesRegex(bundle.BundleError, "certification promotion rejected"):
            bind_case(tuple(case))


if __name__ == "__main__":
    unittest.main()
