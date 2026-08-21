import copy
from datetime import date
from pathlib import Path
import tempfile
import unittest

from reference import environmental_admission_v091 as admission
from tests.test_environmental_admission import AdmissionFixture, canonical_receipt, v13_conformance


def v12_conformance(preflight: dict, *, errors: int = 0) -> dict:
    body = {
        "claim_token": admission.V12_CLAIM,
        "compatibility_claim": True,
        "compatibility_scope": "v0.9.1 unit-test bounded synthetic fixture",
        "certified": False,
        "authority_inference_allowed": False,
        "real_provider_epd_tested": False,
        "package_manifest_sha256": preflight["source"]["package_manifest_sha256"],
        "official_validator": copy.deepcopy(admission.V12_OFFICIAL_VALIDATOR),
        "official_profile": copy.deepcopy(admission.V12_OFFICIAL_PROFILE),
        "positive_control": {
            "error_count": errors,
            "warning_count": 26,
            "is_positive": errors == 0,
        },
        "limitations": ["synthetic unit test; not certification"],
    }
    return canonical_receipt(body)


def recanonicalize(receipt: dict) -> dict:
    body = copy.deepcopy(receipt)
    body.pop("receipt_sha256", None)
    return canonical_receipt(body)


class EnvironmentalAdmissionV091Tests(unittest.TestCase):
    def test_exact_stack_admits_bound_zero_error_v12(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            final = admission.finalize(pre, v12_conformance(pre))
            self.assertTrue(final["admitted"])
            self.assertEqual(final["engine"]["version"], "0.9.1")
            self.assertEqual(final["conformance"]["official_validator"], admission.V12_OFFICIAL_VALIDATOR)
            self.assertEqual(final["conformance"]["official_profile"], admission.V12_OFFICIAL_PROFILE)

    def test_old_incomplete_v09_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf.pop("official_validator")
            conf["official_profile"] = {
                "coordinate": admission.V12_OFFICIAL_PROFILE["coordinate"],
                "jar_sha256": admission.V12_OFFICIAL_PROFILE["jar_sha256"],
            }
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "official validator stack"):
                admission.finalize(pre, conf)

    def test_forged_validator_coordinate_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_validator"]["coordinate"] = "forged:validator:0"
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "official validator stack"):
                admission.finalize(pre, conf)

    def test_forged_validator_jar_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_validator"]["jar_sha256"] = "9" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "official validator stack"):
                admission.finalize(pre, conf)

    def test_forged_validator_pom_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_validator"]["pom_sha256"] = "8" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "official validator stack"):
                admission.finalize(pre, conf)

    def test_forged_profile_jar_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_profile"]["jar_sha256"] = "7" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "ÖKOBAUDAT profile stack"):
                admission.finalize(pre, conf)

    def test_forged_profile_pom_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_profile"]["pom_sha256"] = "6" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "ÖKOBAUDAT profile stack"):
                admission.finalize(pre, conf)

    def test_forged_generic_include_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_profile"]["generic_include_sha256"] = "5" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "ÖKOBAUDAT profile stack"):
                admission.finalize(pre, conf)

    def test_forged_en15804_include_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conf = v12_conformance(pre)
            conf["official_profile"]["en15804_include_sha256"] = "4" * 64
            conf = recanonicalize(conf)
            with self.assertRaisesRegex(admission.AdmissionError, "ÖKOBAUDAT profile stack"):
                admission.finalize(pre, conf)

    def test_v13_route_remains_separate(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.3", zipped=False)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            final = admission.finalize(pre, v13_conformance(pre))
            self.assertEqual(final["routing"]["route"], admission.V13_ROUTE)
            self.assertFalse(final["conformance"]["profile_validation_performed"])


if __name__ == "__main__":
    unittest.main()
