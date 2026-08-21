from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from reference import declared_environmental_indicators_v111 as extractor
from reference import environmental_admission_v091 as admission
from reference import environmental_source_identity_v101 as source_identity

PROCESS_NS = extractor.PROCESS_NS
COMMON_NS = extractor.COMMON_NS
EPD_2019_NS = extractor.EPD_2019_NS
EPD_2013_NS = extractor.EPD_2013_NS
GWP = extractor.GWP_TOTAL_UUID
UNIT_GROUP = "1ebf3012-d0db-4de2-aefd-ef30cedb0be1"
PROCESS_UUID = "11111111-2222-3333-4444-555555555555"


def seal(body: dict) -> dict:
    result = copy.deepcopy(body)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = admission.sha256_bytes(admission.canonical_json_bytes(result))
    return result


def process_xml(version: str) -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<processDataSet xmlns="{PROCESS_NS}" xmlns:common="{COMMON_NS}" xmlns:epd2="{EPD_2019_NS}" xmlns:epd="{EPD_2013_NS}" epd2:epd-version="{version}" version="1.1">
  <processInformation>
    <dataSetInformation>
      <common:UUID>{PROCESS_UUID}</common:UUID>
      <name><baseName xml:lang="en">ProofGrid v1.1.1 synthetic declared indicator fixture</baseName></name>
      <common:other>
        <epd:scenarios>
          <epd:scenario epd:name="Transport to Gdansk" epd:group="Transport" epd:default="true" />
        </epd:scenarios>
      </common:other>
    </dataSetInformation>
  </processInformation>
  <administrativeInformation>
    <publicationAndOwnership><common:dataSetVersion>00.00.001</common:dataSetVersion></publicationAndOwnership>
  </administrativeInformation>
  <LCIAResults>
    <LCIAResult>
      <referenceToLCIAMethodDataSet refObjectId="{GWP}" type="LCIA method data set" uri="../lciamethods/{GWP}" version="04.00.016" />
      <meanAmount>999.25</meanAmount>
      <common:other>
        <epd:amount epd:module="A1-A3">15.559479677163699</epd:amount>
        <epd:amount epd:module="A4" epd:scenario="Transport to Gdansk">10.403452605105544</epd:amount>
        <epd:referenceToUnitGroupDataSet refObjectId="{UNIT_GROUP}" type="unit group data set" uri="../unitgroups/{UNIT_GROUP}" />
      </common:other>
    </LCIAResult>
  </LCIAResults>
</processDataSet>
'''.encode("utf-8")


def write_zip_entry(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build_source(root: Path, version: str) -> tuple[Path, str]:
    raw = process_xml(version)
    if version == "1.3":
        path = root / "source.xml"
        path.write_bytes(raw)
        return path, "application/xml"
    path = root / "source.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        write_zip_entry(zf, "ILCD/processes/process.xml", raw)
    return path, "application/zip"


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
            self.assertFalse(canonical["conformance"]["profile_validation_performed"])
            self.assertEqual(len(record["rows"]), 2)

    def test_legacy_shaped_v12_canonical_without_exact_stack_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            _, _, _, canonical = hardened_chain(source, media, "1.2")
            legacy = copy.deepcopy(canonical)
            legacy["conformance"].pop("official_stack", None)
            legacy["conformance"].pop("official_stack_sha256", None)
            legacy = reseal_canonical(legacy)
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
