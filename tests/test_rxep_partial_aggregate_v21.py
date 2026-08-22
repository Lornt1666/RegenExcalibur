import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'reference/rxep_partial_aggregate_v21.py'
spec=importlib.util.spec_from_file_location('v21',MOD); v21=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v21)

class V21Tests(unittest.TestCase):
    def valid(self):
        return {
            'id':'rxep:test:v21',
            'subject':{'id':'scope','type':'partial-environmental-contribution-set'},
            'claim':{'type':'partial_contribution_set_exact_decimal_total','statement':'test'},
            'measurement':{'value':float(v21.Decimal(v21.EXPECTED['value_decimal'])),'value_decimal':v21.EXPECTED['value_decimal'],'decimal_value_is_authority':True,'numeric_value_is_authority':False,'numeric_value_role':'NON_AUTHORITATIVE_DISPLAY','unit':v21.EXPECTED['unit'],'indicator_code':v21.INDICATOR_CODE,'indicator_uuid':v21.INDICATOR_UUID,'module':v21.MODULE,'scenario':None},
            'methodology':{'name':'canonical_decimal_sum','version':'2.0.0'},
            'sources':[{'path':'a','sha256':v21.EXPECTED['record_file']}],
            'software':{'name':'test','version':'2.1.0'},
            'jurisdiction':'TEST',
            'review':{'state':'CALCULATED','reviewer':None},
            'limitations':['test'],
            'aggregation_performed':True,'sum_performed':True,'aggregation_scope':'ADMITTED_SET_MEMBERS_ONLY','member_count':2,
            'member_semantic_identity_sha256':list(v21.EXPECTED['member_semantic_identity_sha256']),
            'completeness_status':'PARTIAL','whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,
            'missing_contributions_are_zero':False,'missing_modules_are_zero':False,'unit_conversion_performed':False,
            'scenario_inference_performed':False,'duplicate_members_permitted':False,'scientific_validation_performed':False,
            'professional_review_performed':False,'certified':False,
            'integrity':{'content_sha256':'0'*64,'signature':None}
        }

    def test_exact_decimal_canonical(self): self.assertEqual(v21.canonical_decimal(v21.EXPECTED['value_decimal'],'x'),v21.EXPECTED['value_decimal'])
    def test_valid_profile(self): v21.verify_profile(self.valid())
    def test_numeric_authority_rejected(self):
        e=self.valid(); e['measurement']['numeric_value_is_authority']=True
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_complete_promotion_rejected(self):
        e=self.valid(); e['completeness_status']='COMPLETE'
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_whole_building_promotion_rejected(self):
        e=self.valid(); e['whole_building_lca_claimed']=True
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_declared_scope_promotion_rejected(self):
        e=self.valid(); e['declared_scope_complete_claimed']=True
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_review_promotion_rejected(self):
        e=self.valid(); e['review']={'state':'REVIEWED','reviewer':'test'}
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_certification_promotion_rejected(self):
        e=self.valid(); e['certified']=True
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_member_count_mismatch_rejected(self):
        e=self.valid(); e['member_count']=3
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_wrong_unit_rejected(self):
        e=self.valid(); e['measurement']['unit']='g CO2 eqv.'
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_wrong_module_rejected(self):
        e=self.valid(); e['measurement']['module']='A4'
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)
    def test_reaggregation_scope_rejected(self):
        e=self.valid(); e['aggregation_scope']='WHOLE_BUILDING'
        with self.assertRaises(v21.RXEPPartialAggregateError): v21.verify_profile(e)

if __name__=='__main__': unittest.main()
