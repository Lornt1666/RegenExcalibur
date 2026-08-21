import copy
import importlib.util
from decimal import Decimal
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).resolve().parents[1]/"reference"/"partial_contribution_set_total_v20.py"
spec=importlib.util.spec_from_file_location("partial_contribution_set_total_v20",MODULE_PATH)
m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)

FIRST_SEMANTIC={
 "closure_record_content_sha256":"cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd",
 "declaration_bundle_content_sha256":"8e71852027be10c4120f6185e0ae90127da9c72bf1e64f5c50b08442ed2c0aa0",
 "element_global_id":"1BXL7DJx51bvggyIPU2Xi5","ifc_source_sha256":"23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6",
 "indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","mapping_record_content_sha256":"194d3cf29b0f674ce5ca26ab1b0ce07f8cb87449d60090bf9271ac3726371fa7","module":"A1-A3","product_flow_uuid":"a7432abd-0881-4977-a817-f8aaf627fb91","product_flow_version":"00.00.001","quantity_record_content_sha256":"fd107f90c7909569a64ce2d456cba8777cb29578f90ff6c7a458edba1ddad41a","scenario":None,"unit":"kg CO2 eqv.","value_decimal":"15559.479677163699"
}
SECOND_SEMANTIC={
 "closure_record_content_sha256":"cdeb74b75d9065380cbf3a611efbd81c624b5694c3301f184b6747462d25d4bd",
 "declaration_bundle_content_sha256":"8e71852027be10c4120f6185e0ae90127da9c72bf1e64f5c50b08442ed2c0aa0",
 "element_global_id":"1CXL7DJx51bvggyIPU2Xi6","ifc_source_sha256":"14c4be5561131bd6213d45dd0e00064ac916da28f825450133b5dd48d1fcd54d",
 "indicator_code":"GWP-total","indicator_uuid":"6a37f984-a4b3-458a-a20a-64418c145fa2","mapping_record_content_sha256":"94ee0fc7cac96b79d2eb5af0b848fdaf03b04950b8b5caa648336aec550fe4d8","module":"A1-A3","product_flow_uuid":"a7432abd-0881-4977-a817-f8aaf627fb91","product_flow_version":"00.00.001","quantity_record_content_sha256":"45bda12207dde9dbe2a9e578b529668757aa22021cbc7695813d928092b88eb9","scenario":None,"unit":"kg CO2 eqv.","value_decimal":"7779.7398385818495"
}

def member(sid,semantic,rxep,calc):
    return {"semantic_identity_sha256":sid,"semantic_identity":copy.deepcopy(semantic),"rxep":{"record_content_sha256":rxep},"calculation":{"record_content_sha256":calc}}

def accepted_members():
    return [
      member("b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc",FIRST_SEMANTIC,"4e09bb1db2dd54fe5c5f41fd52200482fa9c8d98e3de5a77061e26b4751729a5","1eff779368d48de3a9c637d0a9298788487c67480d6134c18302af1bacf7848e"),
      member("75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950",SECOND_SEMANTIC,"09bf2bfd34ee2105b8744730ed629691cd30440605dfd2d3bd4f12c7ecb666d9","05011f7c34ccae116067d15071a8bde46a41dfa895ebcad8ee9f7408ba6c808c")
    ]

class V20Tests(unittest.TestCase):
    def test_exact_decimal_sum(self):
        self.assertEqual(Decimal("15559.479677163699")+Decimal("7779.7398385818495"),Decimal(m.EXPECTED_TOTAL))

    def test_accepted_members_aggregate_exactly(self):
        out=m.aggregate_verified_set({"members":accepted_members()})
        self.assertEqual(out["total_value_decimal"],m.EXPECTED_TOTAL)
        self.assertEqual(out["member_order"],sorted(m.EXPECTED_MEMBERS))

    def test_input_order_does_not_change_member_order_or_total(self):
        forward=m.aggregate_verified_set({"members":accepted_members()})
        reverse=m.aggregate_verified_set({"members":list(reversed(accepted_members()))})
        self.assertEqual(forward,reverse)

    def test_duplicate_member_rejected(self):
        members=accepted_members(); members[1]=copy.deepcopy(members[0])
        with self.assertRaises(m.PartialSetTotalError):
            m.aggregate_verified_set({"members":members})

    def test_noncanonical_decimal_rejected(self):
        with self.assertRaisesRegex(m.PartialSetTotalError,"not canonical"):
            m.canonical_decimal("1.00","test")

    def test_nonfinite_decimal_rejected(self):
        with self.assertRaisesRegex(m.PartialSetTotalError,"finite"):
            m.canonical_decimal("NaN","test")

    def test_exact_two_members_required(self):
        with self.assertRaisesRegex(m.PartialSetTotalError,"exactly two"):
            m.aggregate_verified_set({"members":accepted_members()[:1]})

if __name__=="__main__": unittest.main()
