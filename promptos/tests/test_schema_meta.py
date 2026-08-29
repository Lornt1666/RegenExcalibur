"""Regression: every schema file must be valid Draft 2020-12 meta-schema.

This test exists because CI failed on PR #121 when byok-control-plane.schema.json
was not a valid meta-schema: the 'Validate schemas and compiled package' step
calls Draft202012Validator.check_schema on every *.json in schemas/.

This regression test mirrors that exact check so a broken schema fails the unit
test step (not only the later 'Validate schemas' step) and reports WHICH schema
is broken.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore
    SchemaError = Exception  # type: ignore


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "src" / "regen_promptos" / "schemas"


class SchemaMetaValidityTests(unittest.TestCase):
    def test_every_schema_is_valid_draft_2020_12(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        files = sorted(SCHEMA_DIR.glob("*.json"))
        self.assertTrue(files, "no schema files found")
        for path in files:
            with self.subTest(schema=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                try:
                    Draft202012Validator.check_schema(schema)
                except SchemaError as exc:
                    self.fail(
                        f"{path.name} is not a valid Draft 2020-12 meta-schema: {exc}"
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    self.fail(
                        f"{path.name} raised {type(exc).__name__} during meta-validation: {exc}"
                    )


if __name__ == "main__":
    unittest.main()
