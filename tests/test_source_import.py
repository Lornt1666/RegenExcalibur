import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evidence" / "examples" / "source-import-v06"
AS_OF = date(2026, 8, 20)


class SourceImportV06Tests(unittest.TestCase):
    def prepare(self, root: Path) -> Path:
        package = root / "package"
        shutil.copytree(FIXTURE, package)
        return package

    def load_manifest(self, package: Path) -> dict:
        return json.loads((package / "import-manifest.json").read_text(encoding="utf-8"))

    def write_manifest(self, package: Path, manifest: dict) -> None:
        (package / "import-manifest.json").write_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )

    def run_import(self, package: Path, output: Path, *, export_source: bool = False):
        from reference.source_import import import_package

        return import_package(package, output_dir=output, as_of=AS_OF, export_source=export_source)

    def assert_import_error(self, package: Path, output: Path, *, export_source: bool = False):
        from reference.source_import import SourceImportError

        with self.assertRaises(SourceImportError):
            self.run_import(package, output, export_source=export_source)

    def test_synthetic_authorized_import_known_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            output = root / "output"
            receipt = self.run_import(package, output)
            self.assertEqual(receipt["verdict"], "AUTHORIZED_SOURCE_IMPORT_VERIFIABLE")
            self.assertFalse(receipt["certified"])
            self.assertEqual(receipt["rights"]["decision"], "AUTHORIZED_FOR_DECLARED_IMPORT_ONLY")
            self.assertEqual(receipt["rights"]["status"], "TEST_ONLY")
            self.assertEqual(receipt["source"]["redistribution_status"], "RESTRICTED")
            self.assertFalse(receipt["source"]["raw_export"]["exported"])
            self.assertEqual(receipt["normalized_record"]["id"], "RX-IMPORTED-SYNTH-CONCRETE-A1A3")
            self.assertEqual(len(receipt["normalized_record"]["canonical_sha256"]), 64)
            registry = json.loads((output / "normalized-registry.json").read_text(encoding="utf-8"))
            record = registry[0]
            self.assertEqual(record["material"]["id"], "synthetic-import-concrete")
            self.assertEqual(record["declared_unit"], "kg")
            self.assertEqual(record["reference_quantity"], 1.0)
            self.assertEqual(record["indicator"], {"name": "GWP-total", "value": 0.15, "unit": "kgCO2e"})
            self.assertEqual(record["system_boundary"]["modules"], ["A1", "A2", "A3"])
            self.assertEqual(record["source"]["redistribution_status"], "RESTRICTED")
            self.assertTrue(record["synthetic"])
            self.assertIn("FORMAT_NOT_CLAIMED_ILCD_EPD_COMPLIANT", record["data_quality_flags"])
            self.assertTrue((output / "import-receipt.json").is_file())

    def test_unknown_authorization_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["status"] = "UNKNOWN"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_public_access_only_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["status"] = "PUBLIC_ACCESS_ONLY"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_test_only_non_synthetic_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["acquisition"]["synthetic"] = False
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_explicit_authorization_missing_approval_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["status"] = "EXPLICITLY_AUTHORIZED"
            manifest["authorization"]["approval_reference"] = None
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_expired_authorization_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["status"] = "EXPLICITLY_AUTHORIZED"
            manifest["authorization"]["approval_reference"] = "SYNTHETIC-AUTH-REF"
            manifest["authorization"]["valid_until"] = "2026-08-19"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_storage_prohibited_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["storage"] = "PROHIBITED"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_transformation_prohibited_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["transformation"] = "PROHIBITED"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_commercial_tool_without_permission_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["authorization"]["status"] = "EXPLICITLY_AUTHORIZED"
            manifest["authorization"]["approval_reference"] = "SYNTHETIC-AUTH-REF"
            manifest["acquisition"]["method"] = "USER_SUPPLIED"
            manifest["acquisition"]["intended_use"] = "COMMERCIAL_TOOL"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_terms_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            terms = package / "terms" / "synthetic-authorization.txt"
            terms.write_text(terms.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            self.assert_import_error(package, root / "output")

    def test_source_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            source = package / "source" / "synthetic-declaration.xml"
            source.write_text(source.read_text(encoding="utf-8") + "<!-- tampered -->\n", encoding="utf-8")
            self.assert_import_error(package, root / "output")

    def test_source_path_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["source"]["path"] = "../outside.xml"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_unsupported_parser_profile_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            manifest = self.load_manifest(package)
            manifest["parser"]["profile"] = "unapproved-profile"
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_normalized_record_schema_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            source = package / "source" / "synthetic-declaration.xml"
            content = source.read_text(encoding="utf-8").replace('referenceQuantity="1"', 'referenceQuantity="-1"')
            source.write_text(content, encoding="utf-8", newline="\n")
            manifest = self.load_manifest(package)
            manifest["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            self.write_manifest(package, manifest)
            self.assert_import_error(package, root / "output")

    def test_raw_source_export_without_redistribution_permission_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.prepare(root)
            self.assert_import_error(package, root / "output", export_source=True)


if __name__ == "__main__":
    unittest.main()
