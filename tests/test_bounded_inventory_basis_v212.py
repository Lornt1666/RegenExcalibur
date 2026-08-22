import copy, unittest
from reference import bounded_inventory_basis_v212 as m

class V212Tests(unittest.TestCase):
    def manifest(self):
        members=[]
        for mid,(element,pred,succ,sid) in m.EXPECTED_MEMBERS.items():
            members.append({'inventory_entry_id':mid,'element_global_id':element,'predecessor_inventory_source_sha256':pred,'covered_successor_source_sha256':succ,'semantic_identity_sha256':sid})
        members.sort(key=lambda x:x['inventory_entry_id'])
        return {'schema_version':'1.0','manifest_id':m.EXPECTED_MANIFEST_ID,'basis_scope_type':'BOUNDED_SYNTHETIC_TEST_INVENTORY','membership_closed':True,'member_count':3,'members':members,'whole_model_inventory_claimed':False,'whole_model_completeness_evaluated':False,'whole_building_scope':False,'whole_building_completeness_evaluated':False,'whole_building_lca_claimed':False}
    def closure(self):
        manifest=self.manifest()
        return {'verdict':m.VERDICT,'basis':{'basis_scope_type':'BOUNDED_SYNTHETIC_TEST_INVENTORY','manifest_member_count':3,'manifest_membership_closed':True},'v211_covered_member_count':3,'one_to_one_membership_match':True,'bounded_scope_membership_complete':True,'bounded_scope_evidence_coverage_complete':True,'coverage_ratio_rational':{'numerator':'3','denominator':'3'},'members':copy.deepcopy(manifest['members']),'whole_model_inventory_claimed':False,'whole_model_completeness_evaluated':False,'whole_building_scope':False,'whole_building_completeness_evaluated':False,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'missing_contributions_are_zero':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}
    def test_manifest_accepts_exact_membership(self): self.assertEqual(len(m.verify_manifest(self.manifest())),3)
    def test_missing_member_rejected(self):
        x=self.manifest(); x['members'].pop(); x['member_count']=2
        with self.assertRaises(m.BasisClosureError): m.verify_manifest(x)
    def test_extra_member_rejected(self):
        x=self.manifest(); x['members'].append(copy.deepcopy(x['members'][0])); x['members'][-1]['inventory_entry_id']='extra'; x['member_count']=4
        with self.assertRaises(m.BasisClosureError): m.verify_manifest(x)
    def test_duplicate_member_rejected(self):
        x=self.manifest(); x['members'][1]['inventory_entry_id']=x['members'][0]['inventory_entry_id']
        with self.assertRaises(m.BasisClosureError): m.verify_manifest(x)
    def test_wrong_semantic_identity_rejected(self):
        x=self.manifest(); x['members'][0]['semantic_identity_sha256']='0'*64
        with self.assertRaises(m.BasisClosureError): m.verify_manifest(x)
    def reject_closure(self,fn):
        x=self.closure(); fn(x)
        with self.assertRaises(m.BasisClosureError): m.verify_closure(x)
    def test_whole_model_promotion_rejected(self): self.reject_closure(lambda x:x.__setitem__('whole_model_inventory_claimed',True))
    def test_whole_building_promotion_rejected(self): self.reject_closure(lambda x:x.__setitem__('whole_building_lca_claimed',True))
    def test_declared_scope_promotion_rejected(self): self.reject_closure(lambda x:x.__setitem__('declared_scope_complete_claimed',True))
    def test_missing_zero_rejected(self): self.reject_closure(lambda x:x.__setitem__('missing_contributions_are_zero',True))
    def test_certification_rejected(self): self.reject_closure(lambda x:x.__setitem__('certified',True))

if __name__=='__main__': unittest.main()
