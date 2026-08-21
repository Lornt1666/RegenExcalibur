from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from reference import environmental_admission_v091 as admission
from reference import environmental_source_identity_v101 as canonical

PROCESS_NS = admission.PROCESS_NS
COMMON_NS = canonical.COMMON_NS
EPD_NS = admission.EPD_2019_NS
XML_NS = canonical.XML_NS


def seal(body: dict) -> dict:
    result = copy.deepcopy(body)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = admission.sha256_bytes(admission.canonical_json_bytes(result))
    return result


def process_xml(version: str, uuid: str | None, *, name: str = "ProofGrid synthetic declaration") -> bytes:
    uuid_xml = f"<common:UUID>{uuid}</common:UUID>" if uuid is not None else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<processDataSet xmlns="{PROCESS_NS}" xmlns:common="{COMMON_NS}" xmlns:epd2="{EPD_NS}" epd2:epd-version="{version}" version="1.1">
  <processInformation>
    <dataSetInformation>
      {uuid_xml}
      <name><baseName xml:lang="en">{name}</baseName></name>
    </dataSetInformation>
  </processInformation>
  <administrativeInformation>
    <publicationAndOwnership><common:dataSetVersion>00.00.001</common:dataSetVersion></publicationAndOwnership>
  </administrativeInformation>
</processDataSet>
'''.encode("utf-8")


def _write_deterministic_zip_entry(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build_source(root: Path, version: str, *, uuid: str | None = "11111111-2222-3333-4444-555555555555", extra_process_version: str | None = None) -> tuple[Path, str]:
    if version == "1.3" and extra_process_version is None:
        path = root / "source.xml"
        path.write_bytes(process_xml(version, uuid))
        return path, "application/xml"

    path = root / "source.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        _write_deterministic_zip_entry(zf, "ILCD/processes/one.xml", process_xml(version, uuid))
        if extra_process_version is not None:
            _write_deterministic_zip_entry(
                zf,
                "ILCD/processes/two.xml",
                process_xml(extra_process_version, "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            )
    return path, "application/zip"


def chain(source: Path, media_type: str, version: str) -> tuple[dict, dict, dict]:
    detected = admission.detect_source(source, media_type)
    route = admission.route_for(version)
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
        "routing": route,
    })
    if version == "1.2":
        conformance = seal({
            "claim_token": admission.V12_CLAIM,
            "compatibility_claim": True,
            "certified": False,
            "authority_inference_allowed": False,
            "package_manifest_sha256": detected["package_manifest_sha256"],
            "official_stack": copy.deepcopy(admission.EXPECTED_V12_STACK),
            "official_stack_sha256": admission.EXPECTED_V12_STACK_SHA256,
            "official_profile": copy.deepcopy(admission.EXPECTED_LEGACY_PROFILE),
            "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
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
        })
    final = admission.finalize(preflight, conformance)
    return preflight, conformance, final


class EnvironmentalSourceIdentityTests(unittest.TestCase):
    def test_v12_admitted_package_normalizes_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.2")
            pre, conf, final = chain(source, media, "1.2")
            record = canonical.build_record(source, pre, conf, final)
            self.assertEqual(record["source"]["format_version"], "1.2")
            self.assertEqual(record["routing"]["route"], admission.V12_ROUTE)
            self.assertTrue(record["conformance"]["profile_validation_performed"])
            self.assertEqual(record["conformance"]["official_stack"], admission.EXPECTED_V12_STACK)
            self.assertFalse(record["impact_values_normalized"])
            self.assertFalse(record["scientific_validation_performed"])
            self.assertFalse(record["professional_review_performed"])
            self.assertFalse(record["certified"])
            self.assertFalse(record["rxep_bridge"]["review_state_elevation_permitted"])

    def test_v13_admitted_xml_normalizes_without_profile_overclaim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            pre, conf, final = chain(source, media, "1.3")
            record = canonical.build_record(source, pre, conf, final)
            self.assertEqual(record["source"]["format_version"], "1.3")
            self.assertEqual(record["routing"]["route"], admission.V13_ROUTE)
            self.assertFalse(record["conformance"]["profile_validation_performed"])
            self.assertEqual(record["identity"]["process_dataset_uuid"], "11111111-2222-3333-4444-555555555555")
            self.assertEqual(record["identity"]["names"][0]["value"], "ProofGrid synthetic declaration")

    def test_repeated_normalization_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            pre, conf, final = chain(source, media, "1.3")
            a = canonical.build_record(source, pre, conf, final)
            b = canonical.build_record(source, pre, conf, final)
            self.assertEqual(canonical.canonical_json_bytes(a), canonical.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"], b["integrity"]["content_sha256"])

    def test_v12_forged_stack_fails_before_canonicalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            pre, conf, final = chain(source, media, "1.2")
            forged = copy.deepcopy(conf)
            forged["official_stack"]["profile"]["jar_sha256"] = "9" * 64
            forged = seal(forged)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, forged, final)

    def test_admission_receipt_digest_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            pre, conf, final = chain(source, media, "1.3")
            final["rights"]["status"] = "EXPLICITLY_AUTHORIZED"
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, final)

    def test_certification_promotion_fails_even_if_resealed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            pre, conf, final = chain(source, media, "1.3")
            promoted = copy.deepcopy(final)
            promoted["certified"] = True
            promoted = seal(promoted)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, promoted)

    def test_normalization_permission_revocation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            pre, conf, final = chain(source, media, "1.3")
            denied = copy.deepcopy(final)
            denied["normalization_permitted"] = False
            denied = seal(denied)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, denied)

    def test_source_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            pre, conf, final = chain(source, media, "1.3")
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, final)

    def test_v12_package_manifest_binding_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2")
            pre, conf, final = chain(source, media, "1.2")
            tampered = copy.deepcopy(final)
            tampered["source"]["package_manifest_sha256"] = "0" * 64
            tampered = seal(tampered)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, tampered)

    def test_route_swap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            pre, conf, final = chain(source, media, "1.3")
            swapped = copy.deepcopy(final)
            swapped["routing"] = admission.route_for("1.2")
            swapped = seal(swapped)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, conf, swapped)

    def test_missing_process_uuid_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", uuid=None)
            pre, conf, final = chain(source, media, "1.3")
            with self.assertRaisesRegex(canonical.CanonicalizationError, "UUID"):
                canonical.build_record(source, pre, conf, final)

    def test_multiple_process_datasets_fail_single_record_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.2", extra_process_version="1.2")
            pre, conf, final = chain(source, media, "1.2")
            with self.assertRaisesRegex(canonical.CanonicalizationError, "exactly one"):
                canonical.build_record(source, pre, conf, final)

    def test_mixed_process_versions_fail_before_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.2", extra_process_version="1.3")
            with self.assertRaises(admission.AdmissionError):
                admission.detect_source(source, media)

    def test_conformance_binding_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, media = build_source(Path(td), "1.3")
            pre, conf, final = chain(source, media, "1.3")
            other_conf = copy.deepcopy(conf)
            other_conf["format_conformance"]["profile_status"] = "TAMPERED"
            other_conf = seal(other_conf)
            with self.assertRaises(canonical.CanonicalizationError):
                canonical.build_record(source, pre, other_conf, final)


if __name__ == "__main__":
    unittest.main()
