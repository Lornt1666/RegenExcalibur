from __future__ import annotations

import copy
from datetime import date
from pathlib import Path
import tempfile
import unittest

from reference import environmental_admission_v091 as admission
from reference import environmental_source_identity_v101 as canonical
from tests.test_environmental_source_identity import build_source


def seal(body: dict) -> dict:
    value=copy.deepcopy(body); value.pop('receipt_sha256',None)
    value['receipt_sha256']=admission.sha256_bytes(admission.canonical_json_bytes(value)); return value


def preflight_for(source:Path,media_type:str,version:str)->dict:
    detected=admission.detect_source(source,media_type)
    return seal({
      'verdict':'ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE','state':'AWAITING_CONFORMANCE','certified':False,'normalization_permitted':False,
      'rights':{'decision':'AUTHORIZED_FOR_DECLARED_IMPORT_ONLY','status':'TEST_ONLY','transformation':'ALLOWED','redistribution':'PROHIBITED'},
      'source':{'path':source.name,'media_type':media_type,'declared_format':{'name':'ILCD+EPD','version':version},**detected},
      'routing':admission.route_for(version)})


def v12_conf(pre:dict)->dict:
    return seal({'claim_token':admission.V12_CLAIM,'compatibility_claim':True,'certified':False,'authority_inference_allowed':False,
      'package_manifest_sha256':pre['source']['package_manifest_sha256'],'official_validator':copy.deepcopy(admission.V12_OFFICIAL_VALIDATOR),
      'official_profile':copy.deepcopy(admission.V12_OFFICIAL_PROFILE),'positive_control':{'error_count':0,'warning_count':26,'is_positive':True}})


def v13_conf(pre:dict)->dict:
    return seal({'verdict':admission.V13_VERDICT,'certified':False,'format_conformance':{'xsd_validation':True,'master_data_identity_validation':True,'profile_validation_performed':False,'profile_status':'AUTHORITATIVE_V1_3_PROFILE_NOT_AVAILABLE_IN_GATE'},'synthetic_fixture':{'sha256':pre['source']['source_sha256'],'identity':{'epd_version':'1.3'}}})


def chain(source:Path,media:str,version:str):
    pre=preflight_for(source,media,version); conf=v12_conf(pre) if version=='1.2' else v13_conf(pre); final=admission.finalize(pre,conf); return pre,conf,final


class ExactStackCanonicalIdentityTests(unittest.TestCase):
    def test_v12_exact_stack_normalizes_metadata_only(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.2'); pre,conf,final=chain(source,media,'1.2')
            rec=canonical.build_record(source,pre,conf,final)
            self.assertEqual(rec['source']['format_version'],'1.2')
            self.assertEqual(rec['conformance']['official_validator'],admission.V12_OFFICIAL_VALIDATOR)
            self.assertEqual(rec['conformance']['official_profile'],admission.V12_OFFICIAL_PROFILE)
            self.assertFalse(rec['impact_values_normalized']); self.assertFalse(rec['scientific_validation_performed']); self.assertFalse(rec['professional_review_performed']); self.assertFalse(rec['certified']); self.assertFalse(rec['rxep_bridge']['review_state_elevation_permitted'])

    def test_previous_fake_profile_hash_is_rejected_before_canonicalization(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.2'); pre=preflight_for(source,media,'1.2'); conf=v12_conf(pre)
            conf['official_profile']['jar_sha256']='9'*64; conf=seal(conf)
            with self.assertRaisesRegex(admission.AdmissionError,'ÖKOBAUDAT profile stack'):
                admission.finalize(pre,conf)

    def test_old_incomplete_v10_style_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.2'); pre=preflight_for(source,media,'1.2'); conf=v12_conf(pre)
            conf.pop('official_validator'); conf['official_profile']={'coordinate':admission.V12_OFFICIAL_PROFILE['coordinate'],'jar_sha256':'9'*64}; conf=seal(conf)
            with self.assertRaises(admission.AdmissionError): admission.finalize(pre,conf)

    def test_forged_stack_cannot_be_rescued_by_forged_final_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.2'); pre=preflight_for(source,media,'1.2'); conf=v12_conf(pre); good=admission.finalize(pre,conf)
            forged_conf=copy.deepcopy(conf); forged_conf['official_validator']['jar_sha256']='8'*64; forged_conf=seal(forged_conf)
            forged_final=copy.deepcopy(good); forged_final['conformance']['official_validator']['jar_sha256']='8'*64; forged_final['conformance']['receipt_sha256']=forged_conf['receipt_sha256']; forged_final=seal(forged_final)
            with self.assertRaises(canonical.CanonicalizationError): canonical.build_record(source,pre,forged_conf,forged_final)

    def test_v13_remains_profile_false_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.3'); pre,conf,final=chain(source,media,'1.3')
            a=canonical.build_record(source,pre,conf,final); b=canonical.build_record(source,pre,conf,final)
            self.assertEqual(canonical.canonical_json_bytes(a),canonical.canonical_json_bytes(b)); self.assertFalse(a['conformance']['profile_validation_performed']); self.assertFalse(a['impact_values_normalized']); self.assertFalse(a['certified'])

    def test_post_admission_source_tamper_still_fails(self):
        with tempfile.TemporaryDirectory() as td:
            source,media=build_source(Path(td),'1.3'); pre,conf,final=chain(source,media,'1.3'); source.write_bytes(source.read_bytes()+b'\n')
            with self.assertRaises(canonical.CanonicalizationError): canonical.build_record(source,pre,conf,final)


if __name__=='__main__': unittest.main()
