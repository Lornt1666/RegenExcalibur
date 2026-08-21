import copy
import importlib.util
from decimal import Decimal
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).resolve().parents[1]/"reference"/"second_distinct_contribution_v19.py"
spec=importlib.util.spec_from_file_location("second_distinct_contribution_v19",MODULE_PATH)
m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)

class V19UnitTests(unittest.TestCase):
    def test_second_identity_is_distinct(self):
        self.assertNotEqual(m.SECOND_ELEMENT_GLOBAL_ID,"1BXL7DJx51bvggyIPU2Xi5")
        self.assertEqual(len(m.SECOND_ELEMENT_GLOBAL_ID),22)

    def test_expected_decimal_result(self):
        result=Decimal("500")*Decimal("15.559479677163699")
        self.assertEqual(m.v16.canonical_decimal(result),m.EXPECTED_RESULT_DECIMAL)

    def sample_calc(self):
        calc={"integrity":{"content_sha256":"a"*64}}
        raw=b"calc\n"
        receipt={"receipt_sha256":"b"*64}
        receipt_raw=b"receipt\n"
        return calc,raw,receipt,receipt_raw

    def valid_repro(self,calc,raw,receipt,receipt_raw):
        r={
          "verdict":m.REPRO_VERDICT,
          "independent_runner_count":2,
          "byte_identical":True,
          "calculation_record_content_sha256":calc["integrity"]["content_sha256"],
          "calculation_record_file_sha256":m.sha256_bytes(raw),
          "calculation_receipt_sha256":receipt["receipt_sha256"],
          "calculation_receipt_file_sha256":m.sha256_bytes(receipt_raw),
          "scaled_result_decimal":m.EXPECTED_RESULT_DECIMAL,
          "certified":False,
        }
        r["receipt_sha256"]=m.sha256_bytes(m.canonical_json_bytes(r))
        return r

    def test_reproduction_contract_accepts_two_runner_receipt(self):
        calc,raw,receipt,receipt_raw=self.sample_calc()
        r=self.valid_repro(calc,raw,receipt,receipt_raw)
        m.verify_reproduction(r,calc,raw,receipt,receipt_raw)

    def test_reproduction_single_runner_rejected(self):
        calc,raw,receipt,receipt_raw=self.sample_calc()
        r=self.valid_repro(calc,raw,receipt,receipt_raw)
        r["independent_runner_count"]=1
        shadow=copy.deepcopy(r); shadow.pop("receipt_sha256",None); r["receipt_sha256"]=m.sha256_bytes(m.canonical_json_bytes(shadow))
        with self.assertRaisesRegex(m.SecondContributionError,"independent reproduction"):
            m.verify_reproduction(r,calc,raw,receipt,receipt_raw)

    def test_reproduction_wrong_result_rejected(self):
        calc,raw,receipt,receipt_raw=self.sample_calc()
        r=self.valid_repro(calc,raw,receipt,receipt_raw)
        r["scaled_result_decimal"]="7779.7"
        shadow=copy.deepcopy(r); shadow.pop("receipt_sha256",None); r["receipt_sha256"]=m.sha256_bytes(m.canonical_json_bytes(shadow))
        with self.assertRaisesRegex(m.SecondContributionError,"result mismatch"):
            m.verify_reproduction(r,calc,raw,receipt,receipt_raw)

    def test_reproduction_certification_promotion_rejected(self):
        calc,raw,receipt,receipt_raw=self.sample_calc()
        r=self.valid_repro(calc,raw,receipt,receipt_raw)
        r["certified"]=True
        shadow=copy.deepcopy(r); shadow.pop("receipt_sha256",None); r["receipt_sha256"]=m.sha256_bytes(m.canonical_json_bytes(shadow))
        with self.assertRaisesRegex(m.SecondContributionError,"certification"):
            m.verify_reproduction(r,calc,raw,receipt,receipt_raw)

if __name__=="__main__":
    unittest.main()
