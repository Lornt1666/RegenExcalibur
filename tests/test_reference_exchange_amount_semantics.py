from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from reference import reference_exchange_amount_semantics as semantics
from tests import test_declared_reference_basis as parent


def with_resulting(raw: bytes, value: str, *, twice: bool = False) -> bytes:
    marker = b"<meanAmount>1.0</meanAmount>"
    addition = f"<resultingAmount>{value}</resultingAmount>".encode("utf-8")
    if twice:
        addition += addition
    if marker not in raw:
        raise AssertionError("meanAmount fixture marker missing")
    return raw.replace(marker, marker + addition, 1)


class ReferenceExchangeAmountSemanticsTests(unittest.TestCase):
    def build_parent(self, root: Path, version: str, raw: bytes):
        source, bundle, receipt = parent.rxep_parent(root, version, raw)
        return source, bundle, receipt

    def test_v12_and_v13_resulting_absent_are_accepted(self):
        for version in ("1.2", "1.3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                raw = parent.process_bytes(version)
                source, bundle, receipt = self.build_parent(root, version, raw)
                record = semantics.preflight(bundle, rxep_receipt_path=receipt, source_path=source)
                self.assertEqual(record["verdict"], semantics.VERDICT)
                self.assertEqual(record["amount_semantics"]["reference_exchange_internal_id"], "42")
                self.assertEqual(record["amount_semantics"]["mean_amount"], {"lexical": "1.0", "decimal": "1"})
                self.assertFalse(record["amount_semantics"]["resulting_amount_present"])
                self.assertIsNone(record["amount_semantics"]["resulting_amount"])
                self.assertEqual(record["amount_semantics"]["selection_policy"], semantics.POLICY)
                self.assertTrue(record["basis_selection_permitted"])
                self.assertFalse(record["building_quantity_multiplication_permitted"])
                self.assertFalse(record["calculated"])
                self.assertFalse(record["certified"])

    def test_raw_inspection_preserves_resulting_amount_before_policy_rejection(self):
        raw = with_resulting(parent.process_bytes("1.3"), "1.25")
        evidence = semantics.inspect_process_bytes(raw, "1.3")
        self.assertTrue(evidence["resulting_amount_present"])
        self.assertEqual(evidence["resulting_amount"], {"lexical": "1.25", "decimal": "1.25"})
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "explicit amount-selection semantics"):
            semantics.enforce_policy(evidence)

    def test_finite_resulting_amount_fails_closed_in_full_preflight(self):
        for version in ("1.2", "1.3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                raw = with_resulting(parent.process_bytes(version), "1.0")
                source, bundle, receipt = self.build_parent(root, version, raw)
                with self.assertRaisesRegex(semantics.AmountSemanticsError, "resultingAmount is present"):
                    semantics.preflight(bundle, rxep_receipt_path=receipt, source_path=source)

    def test_nonfinite_resulting_amount_fails_closed(self):
        raw = with_resulting(parent.process_bytes("1.3"), "NaN")
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "must be finite"):
            semantics.inspect_process_bytes(raw, "1.3")

    def test_malformed_resulting_amount_fails_closed(self):
        raw = with_resulting(parent.process_bytes("1.3"), "not-a-number")
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "is not numeric"):
            semantics.inspect_process_bytes(raw, "1.3")

    def test_multiple_resulting_amounts_fail_closed(self):
        raw = with_resulting(parent.process_bytes("1.3"), "1.0", twice=True)
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "multiple resultingAmount"):
            semantics.inspect_process_bytes(raw, "1.3")

    def test_missing_mean_amount_fails_closed(self):
        raw = parent.process_bytes("1.3").replace(b"<meanAmount>1.0</meanAmount>", b"")
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "exactly one meanAmount"):
            semantics.inspect_process_bytes(raw, "1.3")

    def test_multiple_reference_flows_fail_closed(self):
        raw = parent.process_bytes("1.3", reference_ids=("42", "43"))
        with self.assertRaisesRegex(semantics.AmountSemanticsError, "exactly one process reference flow"):
            semantics.inspect_process_bytes(raw, "1.3")

    def test_source_tamper_fails_before_amount_selection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = parent.process_bytes("1.3")
            source, bundle, receipt = self.build_parent(root, "1.3", raw)
            source.write_bytes(source.read_bytes() + b"x")
            with self.assertRaisesRegex(semantics.AmountSemanticsError, "source SHA"):
                semantics.preflight(bundle, rxep_receipt_path=receipt, source_path=source)

    def test_output_and_receipt_remain_non_calculated_and_non_certified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = parent.process_bytes("1.3")
            source, bundle, receipt = self.build_parent(root, "1.3", raw)
            record = semantics.preflight(bundle, rxep_receipt_path=receipt, source_path=source)
            record_bytes = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
            receipt_value = semantics.build_receipt(record, record_bytes)
            for key in (
                "building_quantity_multiplication_permitted",
                "calculated",
                "environmental_values_transformed",
                "unit_conversion_performed",
                "scientific_validation_performed",
                "professional_review_performed",
                "certified",
            ):
                self.assertFalse(receipt_value[key])
            self.assertEqual(receipt_value["amount_semantics"]["resulting_amount"], None)


if __name__ == "__main__":
    unittest.main()
