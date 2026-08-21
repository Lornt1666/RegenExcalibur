from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from reference import declared_environmental_indicators as declared
from reference import rxep_declared_indicator_binding as binder
from tests import test_declared_environmental_indicators as v11fixtures


def reseal_record(record: dict) -> dict:
    value = copy.deepcopy(record)
    value["integrity"]["content_sha256"] = declared.ZERO_DIGEST
    value["integrity"]["content_sha256"] = declared.sha256_bytes(declared.canonical_json_bytes(value))
    return value


def reseal_receipt(receipt: dict) -> dict:
    value = copy.deepcopy(receipt)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = declared.sha256_bytes(declared.canonical_json_bytes(value))
    return value


def write_parent(root: Path, version: str = "1.3") -> tuple[Path, Path, dict, dict]:
    source, media = v11fixtures.build_source(root, version)
    canonical = v11fixtures.canonical_record(source, media, version)
    record = declared.extract_record(source, canonical)
    record_path = root / "declared-environmental-indicators.json"
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt = declared.build_receipt(record, record_bytes)
    receipt_path = root / "extraction-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return record_path, receipt_path, record, receipt


def overwrite_parent(record_path: Path, receipt_path: Path, record: dict, receipt: dict | None = None) -> dict:
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    if receipt is None:
        receipt = declared.build_receipt(record, record_bytes)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


class RXEPDeclaredIndicatorBindingTests(unittest.TestCase):
    def test_positive_bundle_is_claimed_unsigned_exact_decimal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root, "1.3")
            bundle = binder.build_bundle(record, record_path.read_bytes(), receipt)
            self.assertEqual(bundle["verdict"], binder.VERDICT)
            self.assertEqual(bundle["protocol_version"], "0.2")
            self.assertEqual(bundle["review_state"], "CLAIMED")
            self.assertFalse(bundle["signed"])
            self.assertFalse(bundle["certified"])
            self.assertEqual(bundle["envelope_count"], len(record["rows"]))
            first = bundle["envelopes"][0]
            self.assertEqual(first["review"], {"state": "CLAIMED", "reviewer": None})
            self.assertIsNone(first["integrity"]["signature"])
            self.assertEqual(first["measurement"]["value_lexical"], record["rows"][0]["value_lexical"])
            self.assertEqual(first["measurement"]["value_decimal"], record["rows"][0]["value_decimal"])
            self.assertFalse(first["measurement"]["calculated"])
            self.assertFalse(first["measurement"]["unit_conversion_performed"])
            self.assertEqual(first["evidence_dimensions"]["scientific_validity"], "NOT_EVALUATED")

    def test_v12_and_v13_are_supported_without_float_conversion(self) -> None:
        for version in ("1.2", "1.3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                record_path, receipt_path, record, receipt = write_parent(root, version)
                bundle = binder.build_bundle(record, record_path.read_bytes(), receipt)
                self.assertEqual(bundle["parent"]["format_version"], version)
                for envelope, row in zip(bundle["envelopes"], record["rows"]):
                    self.assertEqual(envelope["measurement"]["value_decimal"], row["value_decimal"])
                    self.assertNotIn("value", envelope["measurement"])

    def test_repeated_binding_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            a = binder.build_bundle(record, record_path.read_bytes(), receipt)
            b = binder.build_bundle(record, record_path.read_bytes(), receipt)
            self.assertEqual(binder.canonical_json_bytes(a), binder.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"], b["integrity"]["content_sha256"])

    def test_record_integrity_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record["rows"][0]["module"] = "C4"
            overwrite_parent(record_path, receipt_path, record, receipt)
            with self.assertRaisesRegex(binder.BindingError, "integrity mismatch"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_receipt_integrity_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            receipt["row_count"] += 1
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(binder.BindingError, "receipt integrity mismatch"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_record_file_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record_path.write_bytes(record_path.read_bytes() + b"\n")
            with self.assertRaisesRegex(binder.BindingError, "record-file hash mismatch"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_calculation_promotion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record["calculated"] = True
            record = reseal_record(record)
            overwrite_parent(record_path, receipt_path, record)
            with self.assertRaises(binder.BindingError):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_unit_conversion_promotion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record["unit_conversion_performed"] = True
            record = reseal_record(record)
            overwrite_parent(record_path, receipt_path, record)
            with self.assertRaises(binder.BindingError):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_scientific_and_certification_promotion_fails(self) -> None:
        for field in ("scientific_validation_performed", "professional_review_performed", "certified"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                record_path, receipt_path, record, receipt = write_parent(root)
                record[field] = True
                record = reseal_record(record)
                overwrite_parent(record_path, receipt_path, record)
                with self.assertRaises(binder.BindingError):
                    binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_lexical_decimal_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record["rows"][0]["value_decimal"] = "999"
            record = reseal_record(record)
            overwrite_parent(record_path, receipt_path, record)
            with self.assertRaisesRegex(binder.BindingError, "lexical/Decimal mismatch"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_duplicate_row_identity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            record["rows"].append(copy.deepcopy(record["rows"][0]))
            record = reseal_record(record)
            overwrite_parent(record_path, receipt_path, record)
            with self.assertRaisesRegex(binder.BindingError, "duplicate v1.1 row identity"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_receipt_source_binding_mismatch_fails_even_if_resealed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            receipt["source_sha256"] = "0" * 64
            receipt = reseal_receipt(receipt)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(binder.BindingError, "receipt/source hash mismatch"):
                binder.bind(record_path, extraction_receipt_path=receipt_path, output_dir=root / "out")

    def test_automatic_review_elevation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record_path, receipt_path, record, receipt = write_parent(root)
            with self.assertRaisesRegex(binder.BindingError, "review-state elevation"):
                binder.build_bundle(record, record_path.read_bytes(), receipt, requested_review_state="REVIEWED")


if __name__ == "__main__":
    unittest.main()
