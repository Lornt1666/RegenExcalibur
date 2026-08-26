import copy
import unittest
from reference import real_model_environmental_suitability_decision_v32 as v32


class V32DecisionTests(unittest.TestCase):
    def record(self):
        return {
            "verdict": v32.VERDICT,
            "decision": v32.DECISION,
            "reference_basis_compatibility": {
                "ifc_quantity_unit": "m3",
                "environmental_reference_unit": "m3",
                "unit_compatible_without_conversion": True,
                "unit_conversion_performed": False,
            },
            "decision_reasons": [
                "IFC_CANDIDATE_STRENGTH_CLASS_NOT_ENCODED",
                "MODEL_WIDE_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_ZERO",
                "ENVIRONMENTAL_SOURCE_INTERNAL_C25_30_VS_C30_37_NAMING_DISCREPANCY",
                "EXPLICIT_MATERIAL_SPECIFICATION_EVIDENCE_REQUIRED_BEFORE_MAPPING",
            ],
            "authority_boundaries": {
                "mapping_authorized": False,
                "environmental_mapping_performed": False,
                "impact_calculation_permitted": False,
                "impact_calculation_performed": False,
                "scientific_suitability_confirmed": False,
                "professional_review_performed": False,
                "regulator_acceptance_implied": False,
                "certified": False,
            },
            "missing_semantics_are_zero": False,
            "fuzzy_or_name_only_equivalence_allowed": False,
        }

    def reject(self, mutate):
        r = self.record()
        mutate(r)
        with self.assertRaises(v32.SuitabilityError):
            v32.validate_decision(r)

    def test_exact_unresolved_state_accepts(self):
        v32.validate_decision(self.record())

    def test_mapping_authorization_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("mapping_authorized", True))

    def test_mapping_execution_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("environmental_mapping_performed", True))

    def test_impact_calculation_permission_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("impact_calculation_permitted", True))

    def test_scientific_suitability_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("scientific_suitability_confirmed", True))

    def test_certification_promotion_rejected(self):
        self.reject(lambda r: r["authority_boundaries"].__setitem__("certified", True))

    def test_missing_semantics_as_zero_rejected(self):
        self.reject(lambda r: r.__setitem__("missing_semantics_are_zero", True))

    def test_fuzzy_equivalence_rejected(self):
        self.reject(lambda r: r.__setitem__("fuzzy_or_name_only_equivalence_allowed", True))

    def test_unit_conversion_promotion_rejected(self):
        self.reject(lambda r: r["reference_basis_compatibility"].__setitem__("unit_conversion_performed", True))

    def test_wrong_decision_rejected(self):
        self.reject(lambda r: r.__setitem__("decision", "SUITABILITY_CONFIRMED_FOR_EXPLICIT_MAPPING"))


if __name__ == "__main__":
    unittest.main()
