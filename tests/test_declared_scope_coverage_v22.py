import copy
import json
from pathlib import Path
import tempfile
import unittest

import reference.declared_scope_coverage_v22 as m

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'conformance'/'declared-scope-coverage-v22'/'synthetic-scope-manifest.json'

def valid_record():
    slots=[
      {'slot_id':'ifc:1BXL7DJx51bvggyIPU2Xi5','kind':'IFC_ELEMENT','coverage_status':'COVERED','element_global_id':'1BXL7DJx51bvggyIPU2Xi5','semantic_identity_sha256':'b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc','rxep_record_content_sha256':'4e09bb1db2dd54fe5c5f41fd52200482fa9c8d98e3de5a77061e26b4751729a5'},
      {'slot_id':'ifc:1CXL7DJx51bvggyIPU2Xi6','kind':'IFC_ELEMENT','coverage_status':'COVERED','element_global_id':'1CXL7DJx51bvggyIPU2Xi6','semantic_identity_sha256':'75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950','rxep_record_content_sha256':'09bf2bfd34ee2105b8744730ed629691cd30440605dfd2d3bd4f12c7ecb666d9'},
      {'slot_id':m.EXPECTED_UNRESOLVED,'kind':'SYNTHETIC_REQUIRED_SLOT','coverage_status':'UNRESOLVED','element_global_id':None,'semantic_identity_sha256':None,'environmental_value_present':False},
    ]
    r={'schema_version':'1.0','record_type':'ProofGridDeclaredScopeCoverageV22','verdict':m.VERDICT,'manifest':{'manifest_id':m.EXPECTED_MANIFEST_ID,'file_sha256':m.EXPECTED_MANIFEST_FILE_SHA256,'synthetic':True,'real_project':False},'parent_v21':{},'parent_v20':{},'slots':slots,'declared_scope_slot_count':3,'covered_slot_count':2,'unresolved_slot_count':1,'coverage_status':'PARTIAL','coverage_percentage_calculated':False,'completeness_promotion_permitted':False,'environmental_arithmetic_performed':False,'additional_sum_performed':False,'unresolved_slots_are_zero':False,'missing_contributions_are_zero':False,'whole_building_lca_claimed':False,'declared_scope_complete_claimed':False,'scientific_validation_performed':False,'professional_review_performed':False,'certified':False,'limitations':['synthetic test'],'integrity':{'content_sha256':m.ZERO,'canonicalization':m.CANON}}
    r['integrity']['content_sha256']=m.sha(m.cbytes(r)); return r

def rehash(r):
    r=copy.deepcopy(r); r['integrity']['content_sha256']=m.ZERO; r['integrity']['content_sha256']=m.sha(m.cbytes(r)); return r

class Tests(unittest.TestCase):
    def test_manifest_valid_and_pinned(self): self.assertEqual(len(m.validate_manifest(MANIFEST)['required_slots']),3)
    def test_manifest_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'m.json'; p.write_bytes(MANIFEST.read_bytes()+b' ')
            with self.assertRaises(m.CoverageError): m.validate_manifest(p)
    def test_valid_partial_record(self): m.verify_record(valid_record())
    def test_complete_promotion_rejected(self):
        r=valid_record(); r['coverage_status']='COMPLETE'
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_completeness_permission_rejected(self):
        r=valid_record(); r['completeness_promotion_permitted']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_unresolved_zero_rejected(self):
        r=valid_record(); r['unresolved_slots_are_zero']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_missing_zero_rejected(self):
        r=valid_record(); r['missing_contributions_are_zero']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_environmental_arithmetic_rejected(self):
        r=valid_record(); r['environmental_arithmetic_performed']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_whole_building_promotion_rejected(self):
        r=valid_record(); r['whole_building_lca_claimed']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_unresolved_value_rejected(self):
        r=valid_record(); u=next(s for s in r['slots'] if s['coverage_status']=='UNRESOLVED'); u['environmental_value_present']=True
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_unresolved_member_rejected(self):
        r=valid_record(); u=next(s for s in r['slots'] if s['coverage_status']=='UNRESOLVED'); u['semantic_identity_sha256']=next(iter(m.V20['members']))
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_duplicate_member_rejected(self):
        r=valid_record(); c=[s for s in r['slots'] if s['coverage_status']=='COVERED']; c[1]['semantic_identity_sha256']=c[0]['semantic_identity_sha256']
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_slot_omission_rejected(self):
        r=valid_record(); r['slots']=r['slots'][:2]
        with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_review_certification_promotions_rejected(self):
        for key in ('scientific_validation_performed','professional_review_performed','certified'):
            r=valid_record(); r[key]=True
            with self.assertRaises(m.CoverageError): m.verify_record(rehash(r))
    def test_content_tamper_rejected(self):
        r=valid_record(); r['limitations'].append('tamper')
        with self.assertRaises(m.CoverageError): m.verify_record(r)
if __name__=='__main__': unittest.main()
