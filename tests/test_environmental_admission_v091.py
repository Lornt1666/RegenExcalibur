import copy
from datetime import date
from pathlib import Path
import tempfile
import unittest

from reference import environmental_admission as v09
from reference import environmental_admission_v091 as v091
from tests.test_environmental_admission import AdmissionFixture, canonical_receipt


def hardened_v12_conformance(preflight: dict) -> dict:
    body = {
        "claim_token": v09.V12_CLAIM,
        "compatibility_claim": True,
        "compatibility_scope": "v0.9.1 exact-stack unit-test synthetic fixture",
        "certified": False,
        "authority_inference_allowed": False,
        "real_provider_epd_tested": False,
        "package_manifest_sha256": preflight["source"]["package_manifest_sha256"],
        "official_validator": copy.deepcopy(v091.EXPECTED_VALIDATOR),
        "official_profile": copy.deepcopy(v091.EXPECTED_PROFILE),
        "official_stack_fingerprint_sha256": v091.STACK_FINGERPRINT_SHA256,
        "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
        "limitations": ["synthetic unit test; not certification"],
    }
    return canonical_receipt(body)


class HardenedEnvironmentalAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = AdmissionFixture(Path(self.tmp.name), "1.2", zipped=True)
        self.pre = v09.preflight(self.fx.root, as_of=date(2026, 8, 20))

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_stack_is_admitted(self):
        receipt = v091.finalize(self.pre, hardened_v12_conformance(self.pre))
        self.assertTrue(receipt["admitted"])
        self.assertTrue(receipt["normalization_permitted"])
        self.assertFalse(receipt["certified"])
        self.assertEqual(receipt["engine"]["version"], "0.9.1")
        self.assertEqual(
            receipt["conformance"]["official_stack"]["fingerprint_sha256"],
            v091.STACK_FINGERPRINT_SHA256,
        )
        self.assertEqual(
            receipt["evidence_dimensions"]["validator_profile_stack_identity"],
            "VERIFIED_EXACT",
        )

    def _assert_mutation_rejected(self, mutate):
        receipt = hardened_v12_conformance(self.pre)
        mutate(receipt)
        receipt.pop("receipt_sha256", None)
        receipt = canonical_receipt(receipt)
        with self.assertRaises(v09.AdmissionError):
            v091.finalize(self.pre, receipt)

    def test_missing_validator_fingerprint_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d.pop("official_validator"))

    def test_forged_validator_jar_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_validator"].__setitem__("jar_sha256", "0" * 64))

    def test_forged_validator_pom_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_validator"].__setitem__("pom_sha256", "1" * 64))

    def test_forged_profile_coordinate_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_profile"].__setitem__("coordinate", "forged:profile:0"))

    def test_forged_profile_jar_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_profile"].__setitem__("jar_sha256", "9" * 64))

    def test_forged_profile_pom_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_profile"].__setitem__("pom_sha256", "2" * 64))

    def test_forged_generic_include_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_profile"].__setitem__("generic_include_sha256", "3" * 64))

    def test_forged_en15804_include_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d["official_profile"].__setitem__("en15804_include_sha256", "4" * 64))

    def test_forged_stack_digest_is_rejected(self):
        self._assert_mutation_rejected(lambda d: d.__setitem__("official_stack_fingerprint_sha256", "5" * 64))

    def test_legacy_v09_receipt_without_full_stack_is_rejected_by_v091(self):
        legacy = {
            "claim_token": v09.V12_CLAIM,
            "compatibility_claim": True,
            "compatibility_scope": "legacy",
            "certified": False,
            "authority_inference_allowed": False,
            "real_provider_epd_tested": False,
            "package_manifest_sha256": self.pre["source"]["package_manifest_sha256"],
            "official_profile": {
                "coordinate": v091.EXPECTED_PROFILE["coordinate"],
                "jar_sha256": v091.EXPECTED_PROFILE["jar_sha256"],
            },
            "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
            "limitations": ["legacy"],
        }
        with self.assertRaises(v09.AdmissionError):
            v091.finalize(self.pre, canonical_receipt(legacy))


if __name__ == "__main__":
    unittest.main()
