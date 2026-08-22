import copy, unittest
from reference import three_member_partial_total_v29 as v29

class V29Tests(unittest.TestCase):
    def members(self):
        out=[]
        for i,(sid,val) in enumerate(v29.EXPECTED_MEMBERS.items()):
            sem={'ifc_source_sha256':'a'*64,'element_global_id':f'e{i}','product_flow_uuid':'p','product_flow_version':'1','quantity_record_content_sha256':'b'*64,'mapping_record_content_sha256':'c'*64,'closure_record_content_sha256':'d'*64,'declaration_bundle_content_sha256':'e'*64,'indicator_code':'GWP-total','indicator_uuid':'6a37f984-a4b3-458a-a20a-64418c145fa2','module':'A1-A3','scenario':None,'value_decimal':val,'unit':'kg CO2 eqv.'}
            # replace synthetic fields by tuning semantic hash is not possible; aggregate validates exact hash.
            out.append((sid,val))
        return out

    def test_expected_total_decimal(self):
        from decimal import Decimal
        self.assertEqual(sum((Decimal(v) for v in v29.EXPECTED_MEMBERS.values()),Decimal('0')),Decimal(v29.EXPECTED_TOTAL))

    def test_canonical_decimal_rejects_padding(self):
        with self.assertRaises(v29.TotalError): v29.canonical_decimal('27229.089435036473250','x')

    def test_canonical_decimal_rejects_nonfinite(self):
        with self.assertRaises(v29.TotalError): v29.canonical_decimal('NaN','x')

    def test_three_expected_members_are_unique(self):
        self.assertEqual(len(v29.EXPECTED_MEMBERS),3)
        self.assertEqual(len(set(v29.EXPECTED_MEMBERS)),3)

    def test_expected_parent_is_partial_three_member(self):
        self.assertEqual(v29.EXPECTED_SET['set_id'],'proofgrid-v28-three-distinct-members')

if __name__=='__main__': unittest.main()
