from __future__ import annotations

import copy
from datetime import date
from pathlib import Path
import tempfile
import unittest

from reference import environmental_admission_v091 as admission
from tests.test_environmental_admission import AdmissionFixture


def seal(body: dict) -> dict:
    result = copy.deepcopy(body)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = admission.sha256_bytes(admission.canonical_json_bytes(result))
    return result


def v12_receipt(preflight: dict) -> dict:
    body = {
        "claim_token": admission.V12_CLAIM,
        "compatibility_claim": True,
        "compatibility_scope": "ProofGrid v0.9.1 exact-stack unit fixture",
        "certified": False,
        "authority_inference_allowed": False,
        "real_provider_epd_tested": False,
        "package_manifest_sha256": preflight["source"]["package_manifest_sha256"],
        "official_stack": copy.deepcopy(admission.EXPECTED_V12_STACK),
        "official_stack_sha256": admission.EXPECTED_V12_STACK_SHA256,
        "official_profile": copy.deepcopy(admission.EXPECTED_LEGACY_PROFILE),
        "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
        "limitations": ["synthetic unit test; not certification"],
    }
    return seal(body)


class HardenedAdmissionTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        fx = AdmissionFixture(Path(td.name), "1.2", zipped=True)
        pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
        return td, fx, pre

    def test_exact_stack_admits(self):
        td, _fx, pre = self.make()
        try:
            final = admission.finalize(pre, v12_receipt(pre))
            self.assertTrue(final["admitted"])
            self.assertEqual(final["engine"]["version"], "0.9.1")
            self.assertEqual(final["conformance"]["official_stack"], admission.EXPECTED_V12_STACK)
            self.assertEqual(final["conformance"]["official_stack_sha256"], admission.EXPECTED_V12_STACK_SHA256)
        finally:
            td.cleanup()

    def assert_stack_mutation_rejected(self, mutate):
        td, _fx, pre = self.make()
        try:
            conf = v12_receipt(pre)
            mutate(conf)
            conf = seal(conf)
            with self.assertRaises(admission.AdmissionError):
                admission.finalize(pre, conf)
        finally:
            td.cleanup()

    def test_missing_stack_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c.pop("official_stack"))

    def test_forged_validator_coordinate_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["validator"].__setitem__("coordinate", "forged:validator:0"))

    def test_forged_validator_jar_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["validator"].__setitem__("jar_sha256", "1" * 64))

    def test_forged_validator_pom_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["validator"].__setitem__("pom_sha256", "2" * 64))

    def test_forged_profile_coordinate_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["profile"].__setitem__("coordinate", "forged:profile:0"))

    def test_forged_profile_jar_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["profile"].__setitem__("jar_sha256", "3" * 64))

    def test_forged_profile_pom_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["profile"].__setitem__("pom_sha256", "4" * 64))

    def test_forged_generic_include_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["included_profiles"].__setitem__("EPD-1.2-Generic.jar", "5" * 64))

    def test_forged_en15804_include_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_stack"]["included_profiles"].__setitem__("EPD-1.2-EN15804.jar", "6" * 64))

    def test_stack_digest_mismatch_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c.__setitem__("official_stack_sha256", "7" * 64))

    def test_conflicting_legacy_profile_rejected(self):
        self.assert_stack_mutation_rejected(lambda c: c["official_profile"].__setitem__("jar_sha256", "8" * 64))


if __name__ == "__main__":
    unittest.main()
