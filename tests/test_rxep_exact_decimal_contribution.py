import copy
import importlib.util
import json
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "reference" / "rxep_calculated_contribution.py"
spec = importlib.util.spec_from_file_location("rxep_calculated_contribution", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class RXEPV17Tests(unittest.TestCase):
    def legacy_envelope(self):
        return {
            "id":"legacy",
            "subject":{"id":"x","type":"test"},
            "claim":{"type":"legacy","statement":"legacy numeric envelope remains valid"},
            "measurement":{"value":1.25,"unit":"kgCO2e"},
            "methodology":{"name":"legacy","version":"0.1"},
            "sources":[{"path":"x","sha256":"0"*64}],
            "software":{"name":"test","version":"1"},
            "jurisdiction":"test",
            "review":{"state":"CALCULATED","reviewer":None},
            "limitations":[],
            "integrity":{"content_sha256":"0"*64,"signature":None},
        }

    def exact_envelope(self):
        e=self.legacy_envelope()
        e.update({"aggregation_performed":False,"scientific_validation_performed":False,"professional_review_performed":False,"certified":False})
        e["measurement"].update({
            "value":15559.4796771637,
            "value_decimal":"15559.479677163699",
            "decimal_value_is_authority":True,
            "numeric_value_is_authority":False,
        })
        return e

    def test_legacy_numeric_envelope_stays_schema_valid(self):
        mod.validate_rxep(self.legacy_envelope())

    def test_exact_decimal_authority_schema_valid(self):
        mod.validate_rxep(self.exact_envelope())

    def test_decimal_authority_flag_required(self):
        e=self.exact_envelope(); e["measurement"]["decimal_value_is_authority"]=False
        with self.assertRaisesRegex(mod.RXEPContributionError,"schema validation"):
            mod.validate_rxep(e)

    def test_numeric_authority_rejected_when_decimal_present(self):
        e=self.exact_envelope(); e["measurement"]["numeric_value_is_authority"]=True
        with self.assertRaisesRegex(mod.RXEPContributionError,"schema validation"):
            mod.validate_rxep(e)

    def test_review_promotion_rejected(self):
        e=self.exact_envelope(); e["review"]["state"]="INDEPENDENTLY_VERIFIED"
        with self.assertRaisesRegex(mod.RXEPContributionError,"CALCULATED"):
            mod.verify_profile(e)

    def test_reviewer_invention_rejected(self):
        e=self.exact_envelope(); e["review"]["reviewer"]="Synthetic Reviewer"
        with self.assertRaisesRegex(mod.RXEPContributionError,"invent a reviewer"):
            mod.verify_profile(e)

    def test_certification_promotion_rejected(self):
        e=self.exact_envelope(); e["certified"]=True
        with self.assertRaisesRegex(mod.RXEPContributionError,"certification"):
            mod.verify_profile(e)

    def test_scientific_promotion_rejected(self):
        e=self.exact_envelope(); e["scientific_validation_performed"]=True
        with self.assertRaisesRegex(mod.RXEPContributionError,"scientific"):
            mod.verify_profile(e)

    def test_aggregation_promotion_rejected(self):
        e=self.exact_envelope(); e["aggregation_performed"]=True
        with self.assertRaisesRegex(mod.RXEPContributionError,"aggregation"):
            mod.verify_profile(e)

    def test_exact_value_mismatch_rejected(self):
        e=self.exact_envelope(); e["measurement"]["value_decimal"]="15559.479677163698"
        with self.assertRaisesRegex(mod.RXEPContributionError,"Decimal measurement mismatch"):
            mod.verify_profile(e)


if __name__ == "__main__":
    unittest.main()
