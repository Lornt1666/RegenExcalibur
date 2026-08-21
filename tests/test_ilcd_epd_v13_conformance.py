import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from reference import ilcd_epd_v13_conformance as v07

XMLSCHEMA_AVAILABLE = importlib.util.find_spec("xmlschema") is not None


class ILCDEPDV13ConformanceUnitTests(unittest.TestCase):
    def init_repo(self, root: Path) -> str:
        subprocess.run(["git", "init", str(root)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "proofgrid@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "ProofGrid Test"], check=True)
        (root / "LICENSE").write_text("Apache License\nVersion 2.0\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()

    def test_checkout_commit_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.init_repo(root)
            with self.assertRaises(v07.ConformanceError):
                v07.verify_checkout(root, "0" * 40, "Apache-2.0")

    def test_git_blob_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "schemas").mkdir(parents=True)
            (root / "schemas" / "test.xsd").write_text("<schema/>", encoding="utf-8")
            self.init_repo(root)
            with self.assertRaises(v07.ConformanceError):
                v07.verify_git_blob(root, "schemas/test.xsd", "0" * 40)

    def test_master_data_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "master.xml"
            path.write_text(
                '<sourceDataSet xmlns:common="http://lca.jrc.it/ILCD/Common"><common:UUID>11111111-1111-1111-1111-111111111111</common:UUID></sourceDataSet>',
                encoding="utf-8",
            )
            with self.assertRaises(v07.ConformanceError):
                v07.verify_master_identity(
                    root,
                    {"path": "master.xml", "uuid": "22222222-2222-2222-2222-222222222222"},
                )

    def test_synthetic_derivative_changes_identity_and_preserves_v13(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.xml"
            output = root / "synthetic.xml"
            source.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<processDataSet xmlns="http://lca.jrc.it/ILCD/Process" '
                'xmlns:common="http://lca.jrc.it/ILCD/Common" '
                'xmlns:epd2="http://www.indata.network/EPD/2019" '
                'version="1.1" epd2:epd-version="1.3">'
                '<processInformation><dataSetInformation>'
                '<common:UUID>11111111-1111-1111-1111-111111111111</common:UUID>'
                '<name><baseName xml:lang="en">Original</baseName><baseName xml:lang="de">Original DE</baseName></name>'
                '</dataSetInformation></processInformation>'
                '</processDataSet>',
                encoding="utf-8",
            )
            fixture = {
                "uuid": "7f94a337-6ae6-4e34-8658-17d48d7f3d36",
                "english_name": "ProofGrid Synthetic",
                "german_name": "ProofGrid Synthetisch",
            }
            v07.build_synthetic_fixture(source, output, fixture)
            identity = v07.parse_dataset_identity(output)
            self.assertEqual(identity["uuid"], fixture["uuid"])
            self.assertEqual(identity["epd_version"], "1.3")
            self.assertTrue(any(row["value"] == "ProofGrid Synthetic" for row in identity["names"]))

    @unittest.skipUnless(XMLSCHEMA_AVAILABLE, "xmlschema v0.7 dependency not installed")
    def test_false_v13_profile_claim_fails_before_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({"format": {}, "master_data": {}, "profile_policy": {"profile_validation_performed": True}}),
                encoding="utf-8",
            )
            original = v07.MANIFEST_PATH
            try:
                v07.MANIFEST_PATH = manifest
                with self.assertRaises(v07.ConformanceError):
                    v07.validate_v13(root / "format", root / "master", root / "out")
            finally:
                v07.MANIFEST_PATH = original

    @unittest.skipUnless(XMLSCHEMA_AVAILABLE, "xmlschema v0.7 dependency not installed")
    def test_sandbox_blocks_unpinned_remote_schema_resolution(self):
        import xmlschema

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xsd = root / "remote-import.xsd"
            xsd.write_text(
                '<?xml version="1.0"?>\n'
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:r="urn:remote">'
                '<xs:import namespace="urn:remote" schemaLocation="https://example.invalid/unpinned.xsd"/>'
                '<xs:element name="root" type="r:RemoteType"/>'
                '</xs:schema>',
                encoding="utf-8",
            )
            with self.assertRaises(Exception):
                xmlschema.XMLSchema(str(xsd), allow="sandbox", defuse="always", base_url=str(root))


if __name__ == "__main__":
    unittest.main()
