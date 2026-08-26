import copy
import unittest
from reference import real_environmental_source_admission_v31 as v31


class V31Tests(unittest.TestCase):
    def record(self):
        return {
            "verdict": v31.VERDICT,
            "admission": {
                "admitted_for_normalization": True,
                "mapping_eligible": False,
                "impact_calculation_allowed_by_this_record": False,
            },
            "conformance": {
                "profile_validation_performed": True,
                "profile_compatible": True,
            },
            "rights": {
                "modified_or_raw_redistribution": "UNKNOWN_REQUIRES_SEPARATE_EVIDENCE",
            },
            "authority_boundaries": {
                "scientific_validity_proven_by_admission": False,
                "professional_suitability_proven_by_admission": False,
                "regulator_acceptance_implied": False,
                "certified": False,
                "building_result_reviewed": False,
                "ifc_mapping_performed": False,
                "building_impact_calculation_performed": False,
            },
        }

    def reject(self, mutate):
        r = self.record()
        mutate(r)
        with self.assertRaises(v31.AdmissionError):
            v31.validate_record(r)

    def test_bounded_record_accepts(self):
        v31.validate_record(self.record())

    def test_mapping_promotion_rejected(self):
        self.reject(lambda r: r["admission"].__setitem__("mapping_eligible", True))

    def test_calculation_promotion_rejected(self):
        self.reject(lambda r: r["admission"].__setitem__("impact_calculation_allowed_by_this_record", True))

    def test_certification_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("certified", True))

    def test_scientific_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("scientific_validity_proven_by_admission", True))

    def test_professional_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("professional_suitability_proven_by_admission", True))

    def test_ifc_mapping_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("ifc_mapping_performed", True))

    def test_modified_redistribution_overclaim_rejected(self):
        self.reject(lambda r: r["rights"].__setitem__("modified_or_raw_redistribution", "ALLOWED"))

    def test_decimal_canonicality(self):
        self.assertEqual(v31.canonical_decimal("181", "x"), "181")
        with self.assertRaises(v31.AdmissionError):
            v31.canonical_decimal("181.0", "x")


if __name__ == "__main__":
    unittest.main()
