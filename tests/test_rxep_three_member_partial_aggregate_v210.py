import copy, unittest
from reference import rxep_three_member_partial_aggregate_v210 as m

class V210ProfileTests(unittest.TestCase):
    def fixture(self):
        e={
          "id":"rxep:test:v210",
          "subject":{"id":"scope","type":"partial-environmental-contribution-set","name":"Test"},
          "claim":{"type":"three_member_partial_contribution_set_exact_decimal_total","statement":"test"},
          "measurement":{"value":float(m.EXPECTED["value_decimal"]),"value_decimal":m.EXPECTED["value_decimal"],"decimal_value_is_authority":True,"numeric_value_is_authority":False,"numeric_value_role":"NON_AUTHORITATIVE_DISPLAY",**m.COMPAT},
          "methodology":{"name":"canonical_decimal_sum","version":"2.9.0","formula":"sum(admitted_member.value_decimal)","aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY"},
          "sources":[{"path":"a","sha256":"0"*64}],
          "software":{"name":m.ENGINE_NAME,"version":m.ENGINE_VERSION},
          "jurisdiction":"UNSPECIFIED_SYNTHETIC_TEST_CONTEXT",
          "review":{"state":"CALCULATED","reviewer":None},
          "limitations":["test only"],
          "aggregation_performed":True,"sum_performed":True,"aggregation_scope":"ADMITTED_SET_MEMBERS_ONLY",
          "member_count":3,"member_semantic_identity_sha256":list(m.EXPECTED["member_ids"]),
          "completeness_status":"PARTIAL","whole_building_lca_claimed":False,"declared_scope_complete_claimed":False,
          "missing_contributions_are_zero":False,"missing_modules_are_zero":False,"unit_conversion_performed":False,"scenario_inference_performed":False,"duplicate_members_permitted":False,
          "scientific_validation_performed":False,"professional_review_performed":False,"certified":False,
          "integrity":{"content_sha256":"0"*64,"signature":None},
        }
        e["integrity"]["content_sha256"]=m.sha256_bytes(m.canonical_json_bytes(e)); return e

    def assertReject(self, mutate):
        e=self.fixture(); mutate(e)
        with self.assertRaises(m.RXEPThreeAggregateError): m.verify_profile(e)

    def test_profile_accepts_bounded_state(self): m.verify_profile(self.fixture())
    def test_noncanonical_decimal_rejected(self):
        with self.assertRaises(m.RXEPThreeAggregateError): m.canonical_decimal("27229.089435036473250","x")
    def test_nonfinite_decimal_rejected(self):
        with self.assertRaises(m.RXEPThreeAggregateError): m.canonical_decimal("NaN","x")
    def test_numeric_authority_rejected(self): self.assertReject(lambda e:e["measurement"].__setitem__("numeric_value_is_authority",True))
    def test_review_promotion_rejected(self): self.assertReject(lambda e:e["review"].__setitem__("state","INDEPENDENTLY_VERIFIED"))
    def test_member_count_promotion_rejected(self): self.assertReject(lambda e:e.__setitem__("member_count",4))
    def test_completeness_promotion_rejected(self): self.assertReject(lambda e:e.__setitem__("completeness_status","COMPLETE"))
    def test_whole_building_promotion_rejected(self): self.assertReject(lambda e:e.__setitem__("whole_building_lca_claimed",True))
    def test_missing_zero_promotion_rejected(self): self.assertReject(lambda e:e.__setitem__("missing_contributions_are_zero",True))
    def test_unit_mismatch_rejected(self): self.assertReject(lambda e:e["measurement"].__setitem__("unit","kgCO2e"))
    def test_scenario_inference_rejected(self): self.assertReject(lambda e:e["measurement"].__setitem__("scenario",{"name":"A"}))
    def test_certification_promotion_rejected(self): self.assertReject(lambda e:e.__setitem__("certified",True))

if __name__=="__main__": unittest.main()
