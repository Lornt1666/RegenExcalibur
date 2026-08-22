import unittest
from reference import source_inventory_gap_v23 as v23

class V23Tests(unittest.TestCase):
    def entries(self):
        rows=[]
        for e in v23.COVERED:
            rows.append({**e,'evidence_status':'EVIDENCE_COVERED','assumed_zero':False,'coverage_source':'ACCEPTED_V1_9_SEMANTIC_CONTRIBUTION'})
        rows.append({'inventory_entry_id':'uncovered-third','element_global_id':v23.UNCOVERED_GLOBAL_ID,'ifc_source_sha256':'a'*64,'semantic_identity_sha256':None,'evidence_status':'EVIDENCE_UNCOVERED','uncovered_reason':'NO_ACCEPTED_ENVIRONMENTAL_CONTRIBUTION','assumed_zero':False,'coverage_source':None})
        return rows
    def test_positive_entries(self): v23.validate_entries(self.entries())
    def test_uncovered_zero_rejected(self):
        x=self.entries(); x[-1]['assumed_zero']=True
        with self.assertRaises(v23.InventoryGapError): v23.validate_entries(x)
    def test_fake_covered_rejected(self):
        x=self.entries(); x[-1]['evidence_status']='EVIDENCE_COVERED'; x[-1]['semantic_identity_sha256']='c'*64
        with self.assertRaises(v23.InventoryGapError): v23.validate_entries(x)
    def test_duplicate_rejected(self):
        x=self.entries(); x[-1]['ifc_source_sha256']=x[0]['ifc_source_sha256']; x[-1]['element_global_id']=x[0]['element_global_id']
        with self.assertRaises(v23.InventoryGapError): v23.validate_entries(x)
    def test_size_drift_rejected(self):
        with self.assertRaises(v23.InventoryGapError): v23.validate_entries(self.entries()[:2])
    def test_covered_wrong_semantic_rejected(self):
        x=self.entries(); x[0]['semantic_identity_sha256']='d'*64
        with self.assertRaises(v23.InventoryGapError): v23.validate_entries(x)

if __name__=='__main__': unittest.main()
