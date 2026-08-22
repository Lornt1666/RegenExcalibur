import copy
import unittest

import reference.rxep_partial_set_total_v21 as m


def valid_envelope():
    e = {
        "id": "rxep:proofgrid:v21:partial-set-total",
        "subject": {"id": "proofgrid:v19:two-distinct-elements-partial", "type": "environmental-contribution-set"},
        "claim": {"type": "partial_contribution_set_exact_decimal_total", "statement": "bounded synthetic partial total"},
        "measurement": {
            "value": float(m.EXPECTED_V20["value_decimal"]),
            "value_decimal": m.EXPECTED_V20["value_decimal"],
            "decimal_value_is_authority": True,
            "numeric_value_is_authority": False,
            "unit": m.EXPECTED_V20["unit"],
            "indicator_code": m.EXPECTED_COMPATIBILITY["indicator_code"],
            "indicator_uuid": m.EXPECTED_COMPATIBILITY["indicator_uuid"],
            "module": m.EXPECTED_COMPATIBILITY["module"],
            "scenario": None,
            "member_count": 2,
            "completeness_status": "PARTIAL",
            "aggregation_scope": "ADMITTED_SET_MEMBERS_ONLY",
        },
        "methodology": {"name": "test", "version": "2.1.0"},
        "sources": [{"path": "v2.0/record.json", "sha256": m.EXPECTED_V20["record_file"]}],
        "software": {"name": m.ENGINE_NAME, "version": m.ENGINE_VERSION},
        "jurisdiction": "SYNTHETIC_TEST_ONLY",
        "review": {"state": "CALCULATED", "reviewer": None},
        "limitations": ["synthetic unit test"],
        "integrity": {"content_sha256": m.ZERO_DIGEST, "signature": None},
        "verdict": m.VERDICT,
        "aggregation_performed": True,
        "sum_performed": True,
        "completeness_status": "PARTIAL",
        "whole_building_lca_claimed": False,
        "declared_scope_complete_claimed": False,
        "missing_contributions_are_zero": False,
        "missing_modules_are_zero": False,
        "unit_conversion_performed": False,
        "scenario_inference_performed": False,
        "environmental_claim_independently_verified": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "software_reproduction": {
            "independent_runner_count": 2,
            "byte_identical": True,
            "comparison_receipt_sha256": m.EXPECTED_V20["comparison"],
        },
    }
    e["integrity"]["content_sha256"] = m.sha256_bytes(m.canonical_json_bytes(e))
    return e


def rehash(e):
    e = copy.deepcopy(e)
    e["integrity"]["content_sha256"] = m.ZERO_DIGEST
    e["integrity"]["content_sha256"] = m.sha256_bytes(m.canonical_json_bytes(e))
    return e


class RXEPPartialSetTotalV21Tests(unittest.TestCase):
    def test_valid_calculated_partial_envelope(self):
        m.verify_profile(valid_envelope())

    def test_review_promotion_rejected(self):
        e = valid_envelope()
        e["review"] = {"state": "INDEPENDENTLY_VERIFIED", "reviewer": "invented"}
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_numeric_authority_promotion_rejected(self):
        e = valid_envelope()
        e["measurement"]["numeric_value_is_authority"] = True
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_decimal_authority_removal_rejected(self):
        e = valid_envelope()
        e["measurement"]["decimal_value_is_authority"] = False
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_completeness_promotion_rejected(self):
        e = valid_envelope()
        e["completeness_status"] = "DECLARED_SCOPE_COMPLETE"
        e["measurement"]["completeness_status"] = "DECLARED_SCOPE_COMPLETE"
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_whole_building_claim_rejected(self):
        e = valid_envelope()
        e["whole_building_lca_claimed"] = True
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_missing_zero_inference_rejected(self):
        e = valid_envelope()
        e["missing_contributions_are_zero"] = True
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_environmental_independent_verification_promotion_rejected(self):
        e = valid_envelope()
        e["environmental_claim_independently_verified"] = True
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(rehash(e))

    def test_scientific_professional_certification_promotions_rejected(self):
        for key in ("scientific_validation_performed", "professional_review_performed", "certified"):
            e = valid_envelope()
            e[key] = True
            with self.assertRaises(m.RXEPPartialTotalError, msg=key):
                m.verify_profile(rehash(e))

    def test_content_hash_tamper_rejected(self):
        e = valid_envelope()
        e["claim"]["statement"] += " tamper"
        with self.assertRaises(m.RXEPPartialTotalError):
            m.verify_profile(e)

    def test_noncanonical_decimal_rejected(self):
        with self.assertRaises(m.RXEPPartialTotalError):
            m.canonical_decimal("2.33392195157455485E+4")


if __name__ == "__main__":
    unittest.main()
