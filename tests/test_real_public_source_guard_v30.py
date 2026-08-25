import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from reference import real_public_source_guard_v30 as guard


class RealPublicSourceGuardV30Tests(unittest.TestCase):
    def fixture(self):
        source = b"ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"
        license_bytes = (
            b"MIT License\n\n"
            b"Copyright (c) 2020 RWTH Aachen University - E3D Institute of Energy Efficiency and Sustainable Building\n\n"
            b"Permission is hereby granted, free of charge, to any person obtaining a copy.\n"
        )
        manifest = {
            "schema_version": "1.0",
            "manifest_version": "3.0.0",
            "source_name": "Test Real IFC",
            "source_role": "PUBLIC_OPEN_REAL_IFC_CONTROL",
            "source_is_user_project": False,
            "upstream": {
                "repository": "example/repo",
                "commit": "a" * 40,
                "path": "model.ifc",
                "git_blob_sha1": guard.git_blob_sha1(source),
                "size_bytes": len(source),
                "source_sha256": guard.sha256_bytes(source),
                "raw_url": "https://example.invalid/model.ifc",
            },
            "license": {
                "spdx": "MIT",
                "path": "LICENSE",
                "git_blob_sha1": guard.git_blob_sha1(license_bytes),
                "license_sha256": guard.sha256_bytes(license_bytes),
                "raw_url": "https://example.invalid/LICENSE",
                "copyright": "Copyright (c) 2020 RWTH Aachen University - E3D Institute of Energy Efficiency and Sustainable Building",
            },
            "analysis_authorization": {
                "user_directive_reference": "chat://test/no-blockers",
                "authorized_purpose": "ProofGrid v3.0 authoritative model inventory basis",
                "public_license_required": True,
                "publication_of_user_private_model_authorized": False,
            },
            "source_sha256_state": "FROZEN",
            "notes": ["test"],
        }
        raw = guard.pretty_json_bytes(manifest)
        return manifest, raw, source, license_bytes

    def test_valid_frozen_source_emits_real_authorization(self):
        manifest, raw, source, license_bytes = self.fixture()
        provenance, auth, receipt = guard.verify_source(manifest, raw, source, license_bytes)
        self.assertEqual(provenance["source_sha256"], hashlib.sha256(source).hexdigest())
        self.assertEqual(auth["source_classification"], "USER_AUTHORIZED_REAL_IFC")
        self.assertTrue(auth["user_authorized"])
        self.assertFalse(auth["synthetic"])
        self.assertFalse(auth["reconstructed"])
        self.assertIn(provenance["source_sha256"], auth["authorization_reference"])
        self.assertEqual(receipt["verdict"], guard.VERDICT)
        self.assertFalse(receipt["certified"])

    def test_source_byte_tamper_rejected(self):
        manifest, raw, source, license_bytes = self.fixture()
        with self.assertRaisesRegex(guard.SourceGuardError, "byte size mismatch|SHA-256 mismatch"):
            guard.verify_source(manifest, raw, source + b"\n", license_bytes)

    def test_license_byte_tamper_rejected(self):
        manifest, raw, source, license_bytes = self.fixture()
        with self.assertRaisesRegex(guard.SourceGuardError, "license SHA-256 mismatch"):
            guard.verify_source(manifest, raw, source, license_bytes + b"tamper")

    def test_git_blob_drift_rejected(self):
        manifest, _, source, license_bytes = self.fixture()
        manifest = copy.deepcopy(manifest)
        manifest["upstream"]["git_blob_sha1"] = "0" * 40
        raw = guard.pretty_json_bytes(manifest)
        with self.assertRaisesRegex(guard.SourceGuardError, "Git blob identity mismatch"):
            guard.verify_source(manifest, raw, source, license_bytes)

    def test_unfrozen_manifest_rejected(self):
        manifest, _, source, license_bytes = self.fixture()
        manifest = copy.deepcopy(manifest)
        manifest["source_sha256_state"] = "DISCOVERY_PENDING"
        raw = guard.pretty_json_bytes(manifest)
        with self.assertRaisesRegex(guard.SourceGuardError, "must be frozen"):
            guard.verify_source(manifest, raw, source, license_bytes)

    def test_public_control_cannot_be_user_project(self):
        manifest, _, source, license_bytes = self.fixture()
        manifest = copy.deepcopy(manifest)
        manifest["source_is_user_project"] = True
        raw = guard.pretty_json_bytes(manifest)
        with self.assertRaisesRegex(guard.SourceGuardError, "cannot be represented as the user's project"):
            guard.verify_source(manifest, raw, source, license_bytes)


if __name__ == "__main__":
    unittest.main()
