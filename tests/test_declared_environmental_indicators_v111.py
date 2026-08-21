from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from reference import declared_environmental_indicators_v111 as extractor
from reference import environmental_admission_v091 as admission
from reference import environmental_source_identity_v101 as source_identity
from tests.test_declared_environmental_indicators import build_source, canonical_record as legacy_canonical_record
from tests.test_environmental_source_identity import seal


def hardened_chain(source: Path, media_type: str, version: str) -> tuple[dict, dict, dict, dict]:
    detected = admission.detect_source(source, media_type)
    preflight = seal({
        "verdict": "ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE",
        "state": "AWAITING_CONFORMANCE",
        "certified": False,
        "normalization_permitted": False,
        "rights": {
            "decision": "AUTHORIZED_FOR_DECLARED_IMPORT_ONLY",
            "status": "TEST_ONLY",
            "transformation": "ALLOWED",
            "redistribution": "PROHIBITED",
        },
        "source": {
            "path": source.name,
            "media_type": media_type,
            "declared_format": {"name": "ILCD+EPD", "version": version},
            **detected,
        },
        "routing": admission.route_for(version),
    })
    if version == "1.2":
        conformance = seal({
            "claim_token": admission.V12_CLAIM,
            "compatibility_claim": True,
            "compatibility_scope": "v1.1.1 hardened synthetic parser control",
            "certified": False,
            "authority_inference_allowed": False,
            "real_provider_epd_tested": False,
            "package_manifest_sha256": detected["package_manifest_sha256"],
            "official_stack": copy.deepcopy(admission.EXPECTED_V12_STACK),
            "official_stack_sha256": admission.EXPECTED_V12_STACK_SHA256,
            "official_profile": copy.deepcopy(admission.EXPECTED_LEGACY_PROFILE),
            "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
            "limitations": ["synthetic hardened parser control; not certification"],
        })
    else:
        conformance = seal({
            "verdict": admission.V13_VERDICT,
            "certified": False,
            "format_conformance": {
                "xsd_validation": True,
                "master_data_identity_validation": True,
                "profile_validation_performed": False,
                "profile_status": "AUTHORITATIVE_V1_3_PROFILE_NOT_AVAILABLE_IN_GATE",
            },
            "synthetic_fixture": {
                "sha256": detected["source_sha256"],
                "identity": {"epd_version": "1.3"},
            },
            "limitations": ["synthetic hardened parser control; not certification"],
        })
    final = admission.finalize(preflight, conformance)
    canonical = source_identity.build_record(source, preflight, conformance, final)
    return preflight, conformance, final, canonical


def reseal_canonical(record: dict) -> dict:
    result = copy.deepcopy(record)
    result["integrity"]["content_sha256"] = extractor.ZERO_DIGEST
    result["integrity"]["content_sha256"] = extractor.sha256_bytes(extractor.canonical_json_bytes(result))
    return result


class HardenedDeclaredEnvironmentalIndicatorTests(unittest.TestCase):
    def test_v12_hardened_parent_extracts_declared_values(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            _, _, _, canonical = hardened_chain(source, media, "1.2")
            record = extractor.extract_record(source, canonical)
            self.assertEqual(record["software"]["version"], "1.1.1")
            self.assertEqual(len(record["rows"]), 2)
            self.assertEqual(record["rows"][0]["value_origin"], "DECLARED_IN_SOURCE")
            self.assertFalse(record["rows"][0]["calculated"])
            self.assertFalse(record["rows"][0]["unit_conversion_performed"])
            self.assertFalse(record["certified"])
            self.assertEqual(canonical["conformance"]["official_stack"], admission.EXPECTED_V12_STACK)

    def test_v13_hardened_parent_extracts_without_profile_overclaim(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            _, _, _, canonical = hardened_chain(source, media, "1.3")
            record = extractor.extract_record(source, canonical)
            self.assertEqual(record["software"]["version"], "1.1.1")
            self.assertFalse(canonical["conformance"]["profile_validation_performed"])
            self.assertEqual(len(record["rows"]), 2)

    def test_legacy_v12_canonical_without_exact_stack_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            legacy = legacy_canonical_record(source, media, "1.2")
            with self.assertRaisesRegex(extractor.ExtractionError, "exact v0.9.1"):
                extractor.extract_record(source, legacy)

    def test_forged_v12_stack_in_resealed_canonical_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            _, _, _, canonical = hardened_chain(source, media, "1.2")
            forged = copy.deepcopy(canonical)
            forged["conformance"]["official_stack"]["profile"]["jar_sha256"] = "9" * 64
            forged = reseal_canonical(forged)
            with self.assertRaisesRegex(extractor.ExtractionError, "exact v0.9.1"):
                extractor.extract_record(source, forged)

    def test_forged_stack_digest_in_resealed_canonical_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            _, _, _, canonical = hardened_chain(source, media, "1.2")
            forged = copy.deepcopy(canonical)
            forged["conformance"]["official_stack_sha256"] = "8" * 64
            forged = reseal_canonical(forged)
            with self.assertRaisesRegex(extractor.ExtractionError, "stack digest"):
                extractor.extract_record(source, forged)

    def test_v13_profile_promotion_in_resealed_canonical_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            _, _, _, canonical = hardened_chain(source, media, "1.3")
            promoted = copy.deepcopy(canonical)
            promoted["conformance"]["profile_validation_performed"] = True
            promoted = reseal_canonical(promoted)
            with self.assertRaisesRegex(extractor.ExtractionError, "may not silently"):
                extractor.extract_record(source, promoted)

    def test_hardened_repeat_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            _, _, _, canonical = hardened_chain(source, media, "1.2")
            a = extractor.extract_record(source, canonical)
            b = extractor.extract_record(source, canonical)
            self.assertEqual(extractor.canonical_json_bytes(a), extractor.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"], b["integrity"]["content_sha256"])


if __name__ == "__main__":
    unittest.main()
