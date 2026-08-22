import copy, hashlib, json, unittest
from reference import three_member_set_v28 as v28


def base_set():
    return {
        'members': [
            {'member_id':'first-accepted-contribution','semantic_identity_sha256':v28.V19['members'][0]},
            {'member_id':'second-distinct-contribution','semantic_identity_sha256':v28.V19['members'][1]},
        ]
    }

class ThreeMemberSetTests(unittest.TestCase):
    def test_third_semantic_identity_is_canonical(self):
        self.assertEqual(hashlib.sha256(json.dumps(v28.THIRD_IDENTITY,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),v28.THIRD_IDENTITY_SHA)
        self.assertNotIn(v28.THIRD_IDENTITY_SHA,v28.V19['members'])

    def test_build_set_is_partial_and_non_aggregating(self):
        s=base_set(); out=v28.build_set(s,{}, {},{}, {},{})
        self.assertEqual(out['member_count'],3)
        self.assertEqual(out['completeness_status'],'PARTIAL')
        self.assertFalse(out['aggregation_performed'])
        self.assertFalse(out['sum_performed'])
        self.assertFalse(out['missing_contributions_are_zero'])
        self.assertFalse(out['missing_modules_are_zero'])
        self.assertFalse(out['duplicate_members_permitted'])
        self.assertEqual(len({m['semantic_identity_sha256'] for m in out['members']}),3)

    def test_semantic_collision_rejected(self):
        s=base_set(); s['members'][1]['semantic_identity_sha256']=v28.THIRD_IDENTITY_SHA
        with self.assertRaises(v28.SetAdmissionError): v28.build_set(s,{}, {},{}, {},{})

    def test_receipt_preserves_no_whole_building_claim(self):
        out=v28.build_set(base_set(),{}, {},{}, {},{})
        r=v28.write_outputs(out,__import__('pathlib').Path(self._tmpdir()))
        self.assertFalse(r['whole_building_lca_claimed'])
        self.assertFalse(r['aggregation_performed']); self.assertFalse(r['sum_performed'])
        self.assertEqual(r['completeness_status'],'PARTIAL')

    def _tmpdir(self):
        import tempfile
        if not hasattr(self,'_td'):
            self._td=tempfile.TemporaryDirectory(); self.addCleanup(self._td.cleanup)
        return self._td.name

if __name__=='__main__': unittest.main()
