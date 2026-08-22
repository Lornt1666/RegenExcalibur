import unittest
from reference import uncovered_remediation_v24 as v24

class V24Tests(unittest.TestCase):
    def rec(self):
        return {"verdict":v24.VERDICT,"remediation_state":"READY_FOR_EXPLICIT_MAPPING","environmental_coverage_status":"EVIDENCE_UNCOVERED","successor_source":{"predecessor_source_sha256":v24.PREDECESSOR_SOURCE_SHA,"successor_source_sha256":"a"*64,"element_global_id":v24.ELEMENT_GLOBAL_ID},"material_evidence":{"declared_name":v24.MATERIAL_NAME},"quantity_evidence":{"quantity_decimal":"250","source_token_is_authority":True,"parser_numeric_value_is_authority":False,"unit":"kg"},"environmental_mapping_performed":False,"environmental_factor_selected":False,"impact_calculation_performed":False,"assumed_zero":False,"whole_building_scope":False,"whole_building_completeness_evaluated":False,"whole_building_lca_claimed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False}
    def test_positive(self): v24.validate_record(self.rec())
    def test_same_source_rejected(self):
        r=self.rec(); r['successor_source']['successor_source_sha256']=v24.PREDECESSOR_SOURCE_SHA
        with self.assertRaises(v24.RemediationError): v24.validate_record(r)
    def test_element_mutation_rejected(self):
        r=self.rec(); r['successor_source']['element_global_id']='wrong'
        with self.assertRaises(v24.RemediationError): v24.validate_record(r)
    def test_mapping_promotion_rejected(self):
        r=self.rec(); r['environmental_mapping_performed']=True
        with self.assertRaises(v24.RemediationError): v24.validate_record(r)
    def test_zero_rejected(self):
        r=self.rec(); r['assumed_zero']=True
        with self.assertRaises(v24.RemediationError): v24.validate_record(r)
    def test_float_authority_rejected(self):
        r=self.rec(); r['quantity_evidence']['parser_numeric_value_is_authority']=True
        with self.assertRaises(v24.RemediationError): v24.validate_record(r)
    def test_decimal(self): self.assertEqual(v24.canonical_decimal('250.'),'250')

if __name__=='__main__': unittest.main()
