import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from reference import environmental_admission as admission


PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
EPD2_NS = "http://www.indata.network/EPD/2019"


def process_xml(version: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<processDataSet xmlns="{PROCESS_NS}" xmlns:epd2="{EPD2_NS}" version="1.1" epd2:epd-version="{version}">'
        '<processInformation><dataSetInformation/></processInformation>'
        '</processDataSet>\n'
    ).encode("utf-8")


def canonical_receipt(body: dict) -> dict:
    result = copy.deepcopy(body)
    result["receipt_sha256"] = admission.sha256_bytes(admission.canonical_json_bytes(result))
    return result


class AdmissionFixture:
    def __init__(self, root: Path, version: str, *, zipped: bool):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        terms = root / "terms.txt"
        terms.write_text("Synthetic internal-test authority for ProofGrid v0.9.\n", encoding="utf-8")

        if zipped:
            source = root / "source.zip"
            with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_STORED) as zf:
                info = zipfile.ZipInfo("ILCD/processes/synthetic.xml")
                info.date_time = (1980, 1, 1, 0, 0, 0)
                info.external_attr = 0o100644 << 16
                zf.writestr(info, process_xml(version))
            media_type = "application/zip"
        else:
            source = root / "source.xml"
            source.write_bytes(process_xml(version))
            media_type = "application/xml"

        self.source = source
        self.terms = terms
        self.manifest_path = root / "import-manifest.json"
        self.manifest = {
            "schema_version": "1.0",
            "import_id": f"RX-V09-{version.replace('.', '')}",
            "manifest_version": "1.0",
            "provider": {
                "name": "RegenExcalibur synthetic admission fixture",
                "program": "ProofGrid v0.9 tests",
                "source_locator": "local:test-fixture",
            },
            "acquisition": {
                "method": "TEST_FIXTURE",
                "synthetic": True,
                "intended_use": "INTERNAL_TEST",
            },
            "authorization": {
                "status": "TEST_ONLY",
                "commercial_use": "PROHIBITED",
                "storage": "ALLOWED",
                "transformation": "ALLOWED",
                "redistribution": "PROHIBITED",
                "terms_reference": "ProofGrid v0.9 synthetic test authority",
                "terms_snapshot": {
                    "path": terms.name,
                    "sha256": admission.sha256_file(terms),
                },
                "approval_reference": None,
                "valid_until": None,
            },
            "source": {
                "path": source.name,
                "sha256": admission.sha256_file(source),
                "media_type": media_type,
                "declared_format": {"name": "ILCD+EPD", "version": version},
            },
            "parser": {
                "name": admission.ROUTER_NAME,
                "version": admission.ROUTER_VERSION,
                "profile": admission.ROUTER_PROFILE,
            },
            "normalized_record_id": f"RX-ADMISSION-{version}",
        }
        self.write_manifest()

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def v12_conformance(preflight: dict, *, errors: int = 0, certified: bool = False, manifest_override: str | None = None) -> dict:
    body = {
        "claim_token": admission.V12_CLAIM,
        "compatibility_claim": True,
        "compatibility_scope": "unit-test bounded synthetic fixture",
        "certified": certified,
        "authority_inference_allowed": False,
        "real_provider_epd_tested": False,
        "package_manifest_sha256": manifest_override or preflight["source"]["package_manifest_sha256"],
        "official_profile": {
            "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
            "jar_sha256": "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
        },
        "positive_control": {
            "error_count": errors,
            "warning_count": 26,
            "is_positive": errors == 0,
        },
        "limitations": ["synthetic unit test; not certification"],
    }
    return canonical_receipt(body)


def v13_conformance(preflight: dict, *, profile_performed: bool = False, certified: bool = False, source_override: str | None = None) -> dict:
    body = {
        "engine": {"name": "v0.7-test", "version": "0.7.0"},
        "verdict": admission.V13_VERDICT,
        "certified": certified,
        "format_conformance": {
            "xsd_validation": True,
            "master_data_identity_validation": True,
            "profile_validation_performed": profile_performed,
            "profile_status": "AUTHORITATIVE_V1_3_PROFILE_NOT_AVAILABLE_IN_GATE",
        },
        "synthetic_fixture": {
            "sha256": source_override or preflight["source"]["source_sha256"],
            "identity": {"epd_version": "1.3"},
        },
        "limitations": ["synthetic unit test; not certification"],
    }
    return canonical_receipt(body)


class EnvironmentalAdmissionTests(unittest.TestCase):
    def test_v12_preflight_routes_only_after_authority_and_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            receipt = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            self.assertEqual(receipt["state"], "AWAITING_CONFORMANCE")
            self.assertFalse(receipt["normalization_permitted"])
            self.assertEqual(receipt["routing"]["route"], admission.V12_ROUTE)
            self.assertTrue(receipt["routing"]["profile_validation_required"])
            self.assertEqual(receipt["source"]["detected_version"], "1.2")
            self.assertIsNotNone(receipt["source"]["package_manifest_sha256"])

    def test_v13_preflight_never_routes_into_v12_profile(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.3", zipped=False)
            receipt = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            self.assertEqual(receipt["routing"]["route"], admission.V13_ROUTE)
            self.assertFalse(receipt["routing"]["profile_validation_applicable"])
            self.assertFalse(receipt["routing"]["profile_validation_required"])

    def test_missing_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(admission.AdmissionError):
                admission.preflight(Path(td), as_of=date(2026, 8, 20))

    def test_unknown_rights_fail_before_detection(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            fx.manifest["authorization"]["status"] = "UNKNOWN"
            fx.write_manifest()
            with self.assertRaisesRegex(admission.AdmissionError, "does not authorize"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_transformation_prohibited_fails_before_detection(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            fx.manifest["authorization"]["transformation"] = "PROHIBITED"
            fx.write_manifest()
            with self.assertRaisesRegex(admission.AdmissionError, "transformation"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_expired_authority_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            fx.manifest["authorization"]["valid_until"] = "2026-08-19"
            fx.write_manifest()
            with self.assertRaisesRegex(admission.AdmissionError, "expired"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_source_hash_mismatch_fails_before_parse(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            fx.source.write_bytes(fx.source.read_bytes() + b"tamper")
            with self.assertRaisesRegex(admission.AdmissionError, "source-content hash mismatch"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_declared_detected_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            fx.manifest["source"]["declared_format"]["version"] = "1.3"
            fx.write_manifest()
            with self.assertRaisesRegex(admission.AdmissionError, "declared/detected version mismatch"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_unsupported_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "9.9", zipped=False)
            with self.assertRaisesRegex(admission.AdmissionError, "unsupported ILCD\+EPD version"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_ambiguous_zip_versions_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            with zipfile.ZipFile(fx.source, "a", compression=zipfile.ZIP_STORED) as zf:
                zf.writestr("ILCD/processes/other.xml", process_xml("1.3"))
            fx.manifest["source"]["sha256"] = admission.sha256_file(fx.source)
            fx.write_manifest()
            with self.assertRaisesRegex(admission.AdmissionError, "ambiguous ILCD\+EPD versions"):
                admission.preflight(fx.root, as_of=date(2026, 8, 20))

    def test_v12_finalize_admits_only_bound_zero_error_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            final = admission.finalize(pre, v12_conformance(pre))
            self.assertTrue(final["admitted"])
            self.assertTrue(final["normalization_permitted"])
            self.assertFalse(final["certified"])
            self.assertEqual(final["source"]["detected_version"], "1.2")

    def test_v12_profile_error_blocks_admission(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            with self.assertRaisesRegex(admission.AdmissionError, "not positive"):
                admission.finalize(pre, v12_conformance(pre, errors=1))

    def test_v12_binding_mismatch_blocks_admission(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            with self.assertRaisesRegex(admission.AdmissionError, "not bound"):
                admission.finalize(pre, v12_conformance(pre, manifest_override="0" * 64))

    def test_v13_finalize_admits_without_profile_claim(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.3", zipped=False)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            final = admission.finalize(pre, v13_conformance(pre))
            self.assertTrue(final["admitted"])
            self.assertFalse(final["conformance"]["profile_validation_performed"])
            self.assertEqual(final["routing"]["route"], admission.V13_ROUTE)

    def test_v13_receipt_cannot_silently_claim_profile_validation(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.3", zipped=False)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            with self.assertRaisesRegex(admission.AdmissionError, "must not silently"):
                admission.finalize(pre, v13_conformance(pre, profile_performed=True))

    def test_v13_source_binding_mismatch_blocks_admission(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.3", zipped=False)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            with self.assertRaisesRegex(admission.AdmissionError, "not bound"):
                admission.finalize(pre, v13_conformance(pre, source_override="f" * 64))

    def test_certified_true_cannot_be_promoted_through_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            with self.assertRaisesRegex(admission.AdmissionError, "certified=false"):
                admission.finalize(pre, v12_conformance(pre, certified=True))

    def test_tampered_preflight_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = AdmissionFixture(Path(td), "1.2", zipped=True)
            pre = admission.preflight(fx.root, as_of=date(2026, 8, 20))
            conformance = v12_conformance(pre)
            pre["source"]["detected_version"] = "1.3"
            with self.assertRaisesRegex(admission.AdmissionError, "preflight receipt digest mismatch"):
                admission.finalize(pre, conformance)


if __name__ == "__main__":
    unittest.main()
