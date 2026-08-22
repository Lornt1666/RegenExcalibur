import copy
import unittest

from reference import third_rxep_binding_v27 as v27


class ThirdRXEPProfileTests(unittest.TestCase):
    def envelope(self):
        e = {
            "id": "rxep:test:third",
            "subject": {"id": v27.EXPECTED["element"], "type": "ifc-declaration-environmental-contribution"},
            "claim": {"type": "scaled_declared_environmental_contribution", "statement": "test"},
            "measurement": {
                "value": float(v27.EXPECTED["value_decimal"]),
                "value_decimal": v27.EXPECTED["value_decimal"],
                "decimal_value_is_authority": True,
                "numeric_value_is_authority": False,
                "numeric_value_role": "NON_AUTHORITATIVE_DISPLAY",
                "unit": v27.EXPECTED["unit"],
                "indicator_code": v27.EXPECTED["indicator_code"],
                "indicator_uuid": v27.EXPECTED["indicator_uuid"],
                "module": v27.EXPECTED["module"],
                "scenario": None,
            },
            "methodology": {"name": "test", "version": "2.6.0"},
            "sources": [{"path": "accepted-v2.6/test.json", "sha256": "1" * 64}],
            "software": {"name": v27.ENGINE_NAME, "version": v27.ENGINE_VERSION},
            "jurisdiction": "UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
            "review": {"state": "CALCULATED", "reviewer": None},
            "limitations": ["test"],
            "rxep_binding_performed": True,
            "contribution_set_admission_performed": False,
            "aggregate_recomputed": False,
            "environmental_coverage_status": "RXEP_BOUND_CONTRIBUTION_NOT_YET_SET_ADMITTED",
            "whole_building_completeness_evaluated": False,
            "scientific_validation_performed": False,
            "professional_review_performed": False,
            "certified": False,
            "integrity": {"content_sha256": "0" * 64, "signature": None},
        }
        e["integrity"]["content_sha256"] = v27.sha256_bytes(v27.canonical_json_bytes(e))
        return e

    def test_valid_profile(self):
        v27.validate_profile(self.envelope())

    def test_decimal_is_canonical(self):
        self.assertEqual(v27.canonical_decimal(v27.EXPECTED["value_decimal"]), v27.EXPECTED["value_decimal"])
        with self.assertRaises(v27.ThirdRXEPError):
            v27.canonical_decimal("3889.869919290924750")

    def test_numeric_authority_promotion_rejected(self):
        e = self.envelope(); e["measurement"]["numeric_value_is_authority"] = True
        with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_decimal_authority_loss_rejected(self):
        e = self.envelope(); e["measurement"]["decimal_value_is_authority"] = False
        with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_review_promotion_rejected(self):
        for state in ("REVIEWED", "INDEPENDENTLY_VERIFIED"):
            e = self.envelope(); e["review"]["state"] = state
            with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_set_admission_promotion_rejected(self):
        e = self.envelope(); e["contribution_set_admission_performed"] = True
        with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_aggregate_promotion_rejected(self):
        e = self.envelope(); e["aggregate_recomputed"] = True
        with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_measurement_identity_mismatch_rejected(self):
        for key, value in (("unit", "kgCO2e"), ("indicator_code", "GWP-biogenic"), ("module", "A1"), ("scenario", {"name": "x"})):
            e = self.envelope(); e["measurement"][key] = value
            with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)

    def test_trust_promotion_rejected(self):
        for key in ("scientific_validation_performed", "professional_review_performed", "certified", "whole_building_completeness_evaluated"):
            e = self.envelope(); e[key] = True
            with self.assertRaises(v27.ThirdRXEPError): v27.validate_profile(e)


if __name__ == "__main__":
    unittest.main()
