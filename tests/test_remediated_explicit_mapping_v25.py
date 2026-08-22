import unittest
from reference import remediated_explicit_mapping_v25 as v25

class V25Tests(unittest.TestCase):
    def rec(self):
        return {
            'verdict':v25.VERDICT,
            'mapping_state':'EXPLICIT_REVIEWED_MAPPING',
            'mapping_decision':{'review':{'state':'REVIEWED_MAPPING_DECISION','role':'synthetic_test_mapping_decision','rationale':'exact ids only'}},
            'source_identity':{'ifc_source_sha256':v25.SUCCESSOR_SOURCE_SHA,'element_global_id':v25.ELEMENT_GLOBAL_ID,'material_association_step_id':v25.MATERIAL_ASSOCIATION_STEP_ID,'material_step_id':v25.MATERIAL_STEP_ID,'quantity_set_step_id':v25.QUANTITY_SET_STEP_ID,'quantity_step_id':v25.QUANTITY_STEP_ID,'quantity_decimal':v25.QUANTITY_DECIMAL},
            'declaration_identity':{'product_flow_uuid':v25.V141['product_flow_uuid'],'product_flow_version':v25.V141['product_flow_version']},
            'environmental_mapping_performed':True,'environmental_source_identity_selected':True,'environmental_factor_selected':False,'impact_calculation_performed':False,'environmental_coverage_status':'EVIDENCE_UNCOVERED','assumed_zero':False,'fuzzy_mapping_performed':False,'name_only_mapping_performed':False,'professional_review_performed':False,'scientific_validation_performed':False,'certified':False,
        }
    def test_positive(self): v25.validate_record(self.rec())
    def test_wrong_source_rejected(self):
        r=self.rec(); r['source_identity']['ifc_source_sha256']='a'*64
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_wrong_element_rejected(self):
        r=self.rec(); r['source_identity']['element_global_id']='wrong'
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_wrong_quantity_rejected(self):
        r=self.rec(); r['source_identity']['quantity_decimal']='251'
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_wrong_product_rejected(self):
        r=self.rec(); r['declaration_identity']['product_flow_uuid']='wrong'
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_missing_review_rejected(self):
        r=self.rec(); r['mapping_decision']['review']['state']='DRAFT'
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_fuzzy_rejected(self):
        r=self.rec(); r['fuzzy_mapping_performed']=True
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_impact_rejected(self):
        r=self.rec(); r['impact_calculation_performed']=True
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_factor_rejected(self):
        r=self.rec(); r['environmental_factor_selected']=True
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)
    def test_coverage_promotion_rejected(self):
        r=self.rec(); r['environmental_coverage_status']='EVIDENCE_COVERED'
        with self.assertRaises(v25.MappingV25Error): v25.validate_record(r)

if __name__=='__main__': unittest.main()
