import unittest
from reference import third_contribution_v26 as v26

class V26Tests(unittest.TestCase):
    def rec(self):
        return {'verdict':v26.VERDICT,'calculation_scope':'SINGLE_MAPPED_DECLARED_RESULT_ROW','calculation':{'scaled_result_decimal':v26.EXPECTED_RESULT,'scaled_result_unit':'kg CO2 eqv.'},'impact_calculation_performed':True,'environmental_mapping_verified':True,'source_declared_result_selected':True,'environmental_coverage_status':'CALCULATED_CONTRIBUTION_NOT_YET_ADMITTED','rxep_binding_performed':False,'contribution_set_admission_performed':False,'aggregate_recomputed':False,'unit_conversion_performed':False,'scenario_inference_performed':False,'whole_building_completeness_evaluated':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}
    def test_positive(self): v26.validate_record(self.rec())
    def test_result_mismatch_rejected(self):
        r=self.rec(); r['calculation']['scaled_result_decimal']='3889'
        with self.assertRaises(v26.V26Error): v26.validate_record(r)
    def test_rxep_promotion_rejected(self):
        r=self.rec(); r['rxep_binding_performed']=True
        with self.assertRaises(v26.V26Error): v26.validate_record(r)
    def test_set_promotion_rejected(self):
        r=self.rec(); r['contribution_set_admission_performed']=True
        with self.assertRaises(v26.V26Error): v26.validate_record(r)
    def test_aggregate_recompute_rejected(self):
        r=self.rec(); r['aggregate_recomputed']=True
        with self.assertRaises(v26.V26Error): v26.validate_record(r)
    def test_unit_conversion_rejected(self):
        r=self.rec(); r['unit_conversion_performed']=True
        with self.assertRaises(v26.V26Error): v26.validate_record(r)
    def test_certification_rejected(self):
        r=self.rec(); r['certified']=True
        with self.assertRaises(v26.V26Error): v26.validate_record(r)

if __name__=='__main__': unittest.main()
