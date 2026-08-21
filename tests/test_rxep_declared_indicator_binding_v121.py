from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from reference import declared_environmental_indicators_v111 as declared
from reference import rxep_declared_indicator_binding_v121 as binder
from tests.test_declared_environmental_indicators_v111 import build_source, hardened_chain


def extraction_material(root: Path, version: str):
    source, media = build_source(root, version)
    _, _, _, canonical = hardened_chain(source, media, version)
    record = declared.extract_record(source, canonical)
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    receipt = declared.base.build_receipt(record, record_bytes)
    record_path = root / "declared-environmental-indicators.json"
    receipt_path = root / "extraction-receipt.json"
    record_path.write_bytes(record_bytes)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return source, canonical, record, receipt, record_path, receipt_path


def reseal_receipt(receipt: dict) -> dict:
    result = copy.deepcopy(receipt)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = binder.sha256_bytes(binder.canonical_json_bytes(result))
    return result


class HardenedRXEPDeclaredIndicatorBindingTests(unittest.TestCase):
    def test_v12_hardened_parent_binds_claimed_exact_decimals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, record, receipt, record_path, receipt_path = extraction_material(root, "1.2")
            out = root / "bound"
            bundle, bound_receipt = binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=out)
            self.assertEqual(receipt["engine"]["version"], "1.1.1")
            self.assertEqual(bundle["review_state"], "CLAIMED")
            self.assertFalse(bundle["certified"])
            self.assertFalse(bundle["signed"])
            self.assertEqual(bundle["envelope_count"], len(record["rows"]))
            for envelope, row in zip(bundle["envelopes"], record["rows"]):
                self.assertEqual(envelope["review"], {"state": "CLAIMED", "reviewer": None})
                self.assertIsNone(envelope["integrity"]["signature"])
                self.assertEqual(envelope["methodology"]["version"], "1.1.1")
                self.assertEqual(envelope["measurement"]["value_lexical"], row["value_lexical"])
                self.assertEqual(envelope["measurement"]["value_decimal"], row["value_decimal"])
                self.assertFalse(envelope["measurement"]["calculated"])
                self.assertFalse(envelope["measurement"]["unit_conversion_performed"])
            self.assertEqual(bound_receipt["engine"]["version"], "1.2.1")
            self.assertFalse(bound_receipt["certified"])

    def test_v13_hardened_parent_binds_without_review_elevation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, _, _, record_path, receipt_path = extraction_material(root, "1.3")
            bundle, receipt = binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "bound")
            self.assertEqual(bundle["review_state"], "CLAIMED")
            self.assertTrue(all(e["methodology"]["version"] == "1.1.1" for e in bundle["envelopes"]))
            self.assertFalse(receipt["signed"])

    def test_historical_v110_parent_receipt_is_rejected_even_when_rehashed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, _, receipt, record_path, receipt_path = extraction_material(root, "1.2")
            stale = copy.deepcopy(receipt)
            stale["engine"]["version"] = "1.1.0"
            stale = reseal_receipt(stale)
            receipt_path.write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(binder.BindingError, "requires hardened parent extraction engine 1.1.1"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "should-not-exist")

    def test_automatic_review_elevation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, _, _, record_path, receipt_path = extraction_material(root, "1.2")
            with self.assertRaisesRegex(binder.BindingError, "automatic RXEP review-state elevation is prohibited"):
                binder.bind(
                    record_path,
                    extraction_receipt_path=receipt_path,
                    output_dir=root / "should-not-exist",
                    requested_review_state="REVIEWED",
                )

    def test_repeat_binding_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, _, _, record_path, receipt_path = extraction_material(root, "1.2")
            a_bundle, a_receipt = binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "a")
            b_bundle, b_receipt = binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "b")
            self.assertEqual(binder.canonical_json_bytes(a_bundle), binder.canonical_json_bytes(b_bundle))
            self.assertEqual(binder.canonical_json_bytes(a_receipt), binder.canonical_json_bytes(b_receipt))
            self.assertEqual((root / "a/rxep-v02-declared-indicator-bundle.json").read_bytes(), (root / "b/rxep-v02-declared-indicator-bundle.json").read_bytes())
            self.assertEqual((root / "a/rxep-v02-binding-receipt.json").read_bytes(), (root / "b/rxep-v02-binding-receipt.json").read_bytes())

    def test_parent_certification_promotion_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, _, receipt, record_path, receipt_path = extraction_material(root, "1.2")
            promoted = copy.deepcopy(receipt)
            promoted["certified"] = True
            promoted = reseal_receipt(promoted)
            receipt_path.write_text(json.dumps(promoted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(binder.BindingError):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "should-not-exist")


if __name__ == "__main__":
    unittest.main()
