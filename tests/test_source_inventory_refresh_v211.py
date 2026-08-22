import copy, unittest
from reference import source_inventory_refresh_v211 as m

class V211RefreshTests(unittest.TestCase):
    def fixture(self):
        entries=[]
        for x in (m.FIRST,m.SECOND):
            entries.append({'inventory_entry_id':x['entry_id'],'element_global_id':x['element'],'predecessor_inventory_source_sha256':x['source'],'covered_successor_source_sha256':x['source'],'source_revision_changed':False,'source_revision_continuity_verified':True,'evidence_status':'EVIDENCE_COVERED','coverage_source':'ACCEPTED_V2_8_SEMANTIC_CONTRIBUTION','semantic_identity_sha256':x['sid'],'assumed_zero':False})
        entries.append({'inventory_entry_id':m.THIRD['entry_id'],'element_global_id':m.THIRD['element'],'predecessor_inventory_source_sha256':m.THIRD['predecessor'],'covered_successor_source_sha256':m.THIRD['successor'],'source_revision_changed':True,'source_revision_continuity_verified':True,'evidence_status':'EVIDENCE_COVERED_VIA_SUCCESSOR_SOURCE','coverage_source':'ACCEPTED_V2_8_SEMANTIC_CONTRIBUTION','semantic_identity_sha256':m.THIRD['sid'],'assumed_zero':False})
        entries.sort(key=lambda e:e['inventory_entry_id'])
        o={'schema_version':'1.0','record_type':'ProofGridDeclaredSyntheticInventoryEvidenceRefresh','verdict':m.VERDICT,'inventory_scope':{'inventory_id':'proofgrid:v23:declared-synthetic-source-inventory','inventory_scope_type':'DECLARED_SYNTHETIC_SOURCE_INVENTORY','inventory_entry_count':3,'whole_building_scope':False,'whole_model_inventory_claimed':False},'coverage':{'covered_entry_count':3,'uncovered_entry_count':0,'coverage_ratio_rational':{'numerator':'3','denominator':'3'},'rounded_decimal_coverage_authority_present':False,'declared_inventory_evidence_coverage_complete':True,'whole_building_completeness_evaluated':False},'entries':entries,'whole_building_completeness_evaluated':False,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'missing_contributions_are_zero':False,'uncovered_inventory_is_zero':False,'aggregation_recomputed':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False}
        return o
    def reject(self,fn):
        o=self.fixture(); fn(o)
        with self.assertRaises(m.InventoryRefreshError): m.verify_output(o)
    def test_accepts_exact_3_of_3(self): m.verify_output(self.fixture())
    def test_third_predecessor_mismatch_rejected(self): self.reject(lambda o:[e for e in o['entries'] if e['inventory_entry_id']==m.THIRD['entry_id']][0].__setitem__('predecessor_inventory_source_sha256','0'*64))
    def test_third_successor_mismatch_rejected(self): self.reject(lambda o:[e for e in o['entries'] if e['inventory_entry_id']==m.THIRD['entry_id']][0].__setitem__('covered_successor_source_sha256','0'*64))
    def test_third_semantic_identity_mismatch_rejected(self): self.reject(lambda o:[e for e in o['entries'] if e['inventory_entry_id']==m.THIRD['entry_id']][0].__setitem__('semantic_identity_sha256','0'*64))
    def test_continuity_loss_rejected(self): self.reject(lambda o:[e for e in o['entries'] if e['inventory_entry_id']==m.THIRD['entry_id']][0].__setitem__('source_revision_continuity_verified',False))
    def test_whole_building_promotion_rejected(self): self.reject(lambda o:o.__setitem__('whole_building_lca_claimed',True))
    def test_whole_model_promotion_rejected(self): self.reject(lambda o:o['inventory_scope'].__setitem__('whole_model_inventory_claimed',True))
    def test_missing_zero_rejected(self): self.reject(lambda o:o.__setitem__('missing_contributions_are_zero',True))
    def test_certification_promotion_rejected(self): self.reject(lambda o:o.__setitem__('certified',True))

if __name__=='__main__': unittest.main()
