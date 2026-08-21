import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "reference" / "mapped_declared_result_scale.py"
spec = importlib.util.spec_from_file_location("mapped_declared_result_scale", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class V16PureTests(unittest.TestCase):
    def test_canonical_decimal(self):
        self.assertEqual(mod.canonical_decimal(Decimal("1000.000")), "1000")
        self.assertEqual(mod.canonical_decimal(Decimal("15.559479677163699")), "15.559479677163699")

    def test_nonfinite_rejected(self):
        with self.assertRaises(mod.ScalingError):
            mod.require_canonical_decimal("NaN", "x")

    def test_noncanonical_decimal_rejected(self):
        with self.assertRaisesRegex(mod.ScalingError, "not canonical"):
            mod.require_canonical_decimal("1000.0", "x")

    def test_exact_scenario_null(self):
        self.assertTrue(mod.exact_scenario_equal(None, None))
        self.assertFalse(mod.exact_scenario_equal(None, {"name":"x","group":"g","default":True}))

    def _bundle(self, rows):
        return {"environmental_results":{"aggregation_performed":False,"missing_modules_are_zero":False,"indicator_scope":{"code":"GWP-total","indicator_uuid":"u","canonical_unit":"kg CO2 eqv."},"rows":rows}}

    def _row(self):
        return {"indicator_uuid":"u","module":"A1-A3","scenario":None,"value_origin":"DECLARED_IN_SOURCE","calculated":False,"unit_conversion_performed":False,"canonical_unit":"kg CO2 eqv.","value_lexical":"15.5","value_decimal":"15.5","source_location":{"path":"x"}}

    def _selection(self):
        return {"indicator_code":"GWP-total","indicator_uuid":"u","module":"A1-A3","scenario":None,"expected_unit":"kg CO2 eqv."}

    def test_selects_exact_declared_row(self):
        row = mod.select_row(self._bundle([self._row()]), self._selection())
        self.assertEqual(row["value_decimal"], "15.5")

    def test_duplicate_row_rejected(self):
        with self.assertRaisesRegex(mod.ScalingError, "found 2"):
            mod.select_row(self._bundle([self._row(), self._row()]), self._selection())

    def test_calculated_row_rejected(self):
        row=self._row(); row["calculated"]=True
        with self.assertRaisesRegex(mod.ScalingError, "marked calculated"):
            mod.select_row(self._bundle([row]), self._selection())

    def test_source_conversion_row_rejected(self):
        row=self._row(); row["unit_conversion_performed"]=True
        with self.assertRaisesRegex(mod.ScalingError, "unit conversion"):
            mod.select_row(self._bundle([row]), self._selection())

    def test_request_requires_explicit_scenario(self):
        schema=json.loads(mod.REQUEST_SCHEMA.read_text())
        request={"schema_version":"1.0","request_version":"1.6.0","bindings":{k:"0"*64 for k in ["quantity_record_content_sha256","quantity_record_file_sha256","quantity_receipt_sha256","mapping_record_content_sha256","mapping_record_file_sha256","mapping_receipt_sha256","closure_record_content_sha256","closure_record_file_sha256","closure_receipt_sha256","declaration_bundle_content_sha256","declaration_bundle_file_sha256","declaration_bundle_receipt_sha256"]},"selection":{"indicator_code":"GWP-total","indicator_uuid":"u","module":"A1-A3","expected_unit":"kg CO2 eqv."}}
        self.assertTrue(list(mod.Draft202012Validator(schema).iter_errors(request)))


if __name__ == "__main__":
    unittest.main()
