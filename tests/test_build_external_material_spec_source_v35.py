import argparse
import hashlib
import tempfile
import unittest
from pathlib import Path

from reference import build_external_material_spec_source_v35 as builder


class BuildExternalMaterialSpecSourceV35Tests(unittest.TestCase):
    def args(self, root: Path, *, decision, binding_method, strength_class=None, source_text=True):
        content = root / "message.txt"
        content.write_bytes(b"DigitalHub authoritative reply\n")
        quoted = root / "quoted.txt"
        if source_text:
            quoted.write_bytes(b"Concrete class source statement\n")
        return argparse.Namespace(
            content_file=content,
            source_text_file=quoted if source_text else None,
            output=root / "out.json",
            channel="EMAIL_REPLY",
            source_locator="gmail:test",
            message_id="test-message",
            thread_id="test-thread",
            attachment_name=None,
            media_type="text/plain",
            received_at="2026-08-26T00:00:00Z",
            author_name="Project Author",
            author_email="author@example.invalid",
            author_organization="DigitalHub project authority",
            relation_to_digitalhub="Documented test authority",
            authority_basis="PROJECT_AUTHOR",
            decision=decision,
            binding_method=binding_method,
            strength_class=strength_class,
        )

    def test_build_candidate_bound_strength_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.args(
                root,
                decision="AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND",
                binding_method="AUTHOR_EXPLICIT_CONFIRMATION",
                strength_class="C25/30",
            )
            record = builder.build(args)
            self.assertTrue(record["candidate"]["candidate_bound"])
            self.assertEqual(record["material_semantics"]["concrete_strength_class"], "C25/30")
            self.assertEqual(record["acquisition"]["content_sha256"], hashlib.sha256(args.content_file.read_bytes()).hexdigest())

    def test_build_candidate_bound_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.args(
                root,
                decision="AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED",
                binding_method="AUTHOR_EXPLICIT_CONFIRMATION",
            )
            record = builder.build(args)
            self.assertTrue(record["candidate"]["candidate_bound"])
            self.assertIsNone(record["material_semantics"]["concrete_strength_class"])
            self.assertTrue(record["material_semantics"]["explicit_absence_statement"])

    def test_unbound_absence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.args(
                root,
                decision="AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED",
                binding_method="UNBOUND",
            )
            with self.assertRaises(ValueError):
                builder.build(args)

    def test_bound_strength_requires_exact_source_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.args(
                root,
                decision="AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND",
                binding_method="AUTHOR_EXPLICIT_CONFIRMATION",
                strength_class="C25/30",
                source_text=False,
            )
            with self.assertRaises(ValueError):
                builder.build(args)


if __name__ == "__main__":
    unittest.main()
