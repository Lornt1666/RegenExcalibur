#!/usr/bin/env python3
"""ProofGrid v1.3.1 explicit reference-exchange amount semantics gate.

This gate runs before the accepted v1.3 declared-reference-basis extractor.
It binds to the exact RXEP v0.2 parent/source bytes and proves whether the
single quantitative-reference exchange contains only ``meanAmount`` or also a
``resultingAmount``.

Current policy is intentionally narrow:

* ``meanAmount`` must be present and finite;
* ``resultingAmount`` is preserved when present;
* any present ``resultingAmount`` causes fail-closed withholding until a
  separately specified format-semantic policy defines which amount is the
  declaration/reference basis.

The gate performs no environmental calculation, unit conversion, scientific
validation, professional review, or certification.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declared_reference_basis as v13  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Reference Exchange Amount Semantics Gate"
ENGINE_VERSION = "1.3.1"
VERDICT = "REFERENCE_EXCHANGE_AMOUNT_SEMANTICS_RESOLVED_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
SCHEMA_PATH = ROOT / "schemas" / "reference-exchange-amount-semantics.schema.json"
POLICY = "MEAN_AMOUNT_ACCEPTED_ONLY_WHEN_RESULTING_AMOUNT_ABSENT"


class AmountSemanticsError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AmountSemanticsError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def direct_children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(element) if local_name(child.tag) == name]


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in element.iter() if local_name(node.tag) == name]


def element_text(element: ET.Element, label: str) -> str:
    text = (element.text or "").strip()
    require(bool(text), f"{label} is empty")
    return text


def decimal_evidence(element: ET.Element, label: str) -> dict[str, str]:
    lexical = element_text(element, label)
    try:
        decimal = v13.canonical_decimal(lexical, label)
    except Exception as exc:
        raise AmountSemanticsError(str(exc)) from exc
    return {"lexical": lexical, "decimal": decimal}


def inspect_process_bytes(process_raw: bytes, format_version: str) -> dict[str, Any]:
    require(format_version in {"1.2", "1.3"}, f"unsupported format version: {format_version}")
    try:
        root = ET.fromstring(process_raw)
    except ET.ParseError as exc:
        raise AmountSemanticsError(f"invalid process XML: {exc}") from exc

    quantitative = descendants(root, "quantitativeReference")
    require(len(quantitative) == 1, f"expected exactly one process quantitativeReference, got {len(quantitative)}")
    reference_ids = [element_text(node, "referenceToReferenceFlow") for node in descendants(quantitative[0], "referenceToReferenceFlow")]
    require(len(reference_ids) == 1, f"expected exactly one process reference flow, got {len(reference_ids)}")
    reference_id = reference_ids[0]

    matching = [
        node
        for node in descendants(root, "exchange")
        if str(node.attrib.get("dataSetInternalID", "")) == reference_id
    ]
    require(len(matching) == 1, f"reference exchange {reference_id!r} missing or ambiguous: {len(matching)} matches")
    exchange = matching[0]

    mean_nodes = direct_children(exchange, "meanAmount")
    require(len(mean_nodes) == 1, f"reference exchange must contain exactly one meanAmount, got {len(mean_nodes)}")
    mean = decimal_evidence(mean_nodes[0], "reference exchange meanAmount")

    resulting_nodes = direct_children(exchange, "resultingAmount")
    require(len(resulting_nodes) <= 1, f"reference exchange contains multiple resultingAmount values: {len(resulting_nodes)}")
    resulting = decimal_evidence(resulting_nodes[0], "reference exchange resultingAmount") if resulting_nodes else None

    return {
        "format_version": format_version,
        "reference_exchange_internal_id": reference_id,
        "mean_amount": mean,
        "resulting_amount_present": resulting is not None,
        "resulting_amount": resulting,
        "selection_policy": POLICY,
    }


def enforce_policy(semantics: dict[str, Any]) -> None:
    if semantics["resulting_amount_present"]:
        resulting = semantics["resulting_amount"]
        raise AmountSemanticsError(
            "reference exchange resultingAmount is present; explicit amount-selection semantics are required before basis extraction "
            f"(meanAmount={semantics['mean_amount']['lexical']!r}/{semantics['mean_amount']['decimal']}, "
            f"resultingAmount={resulting['lexical']!r}/{resulting['decimal']})"
        )


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise AmountSemanticsError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AmountSemanticsError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def validate_schema(record: dict[str, Any]) -> None:
    schema, _ = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise AmountSemanticsError(f"invalid v1.3.1 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise AmountSemanticsError(f"amount-semantics schema validation failed: {preview}")


def preflight(
    rxep_bundle_path: Path,
    *,
    rxep_receipt_path: Path,
    source_path: Path,
) -> dict[str, Any]:
    bundle, bundle_bytes = load_json(rxep_bundle_path)
    binding_receipt, _ = load_json(rxep_receipt_path)
    try:
        v13.verify_rxep_parent(bundle, bundle_bytes, binding_receipt)
    except Exception as exc:
        raise AmountSemanticsError(f"RXEP parent verification failed: {exc}") from exc

    parent = bundle["parent"]
    format_version = parent["format_version"]
    try:
        process_raw = v13.source_process_bytes(source_path, format_version, parent["source_sha256"])
    except Exception as exc:
        raise AmountSemanticsError(str(exc)) from exc
    require(sha256_bytes(process_raw) == parent["process_xml_sha256"], "RXEP parent/process XML SHA-256 mismatch")

    semantics = inspect_process_bytes(process_raw, format_version)
    enforce_policy(semantics)

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridReferenceExchangeAmountSemantics",
        "verdict": VERDICT,
        "parent": {
            "rxep_verdict": bundle["verdict"],
            "rxep_protocol_version": bundle["protocol_version"],
            "rxep_bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "rxep_binding_receipt_sha256": binding_receipt["receipt_sha256"],
            "source_sha256": parent["source_sha256"],
            "process_xml_sha256": parent["process_xml_sha256"],
            "process_dataset_uuid": parent["process_dataset_uuid"],
            "format_version": format_version,
        },
        "amount_semantics": semantics,
        "basis_selection_permitted": True,
        "building_quantity_multiplication_permitted": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This gate accepts meanAmount as the source exchange amount only when resultingAmount is absent on the exact reference exchange.",
            "A present resultingAmount causes fail-closed withholding until a separately specified semantic policy defines the relationship between the amount fields.",
            "This gate does not authorize building-level multiplication or transform environmental indicator values.",
            "Passing this gate does not establish scientific validity, professional review, provider authority, regulatory approval, or certification.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
            "signature": None,
        },
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    validate_schema(record)
    return record


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "rxep_bundle_content_sha256": record["parent"]["rxep_bundle_content_sha256"],
        "rxep_binding_receipt_sha256": record["parent"]["rxep_binding_receipt_sha256"],
        "source_sha256": record["parent"]["source_sha256"],
        "process_xml_sha256": record["parent"]["process_xml_sha256"],
        "process_dataset_uuid": record["parent"]["process_dataset_uuid"],
        "format_version": record["parent"]["format_version"],
        "amount_semantics": copy.deepcopy(record["amount_semantics"]),
        "basis_selection_permitted": record["basis_selection_permitted"],
        "building_quantity_multiplication_permitted": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.3.1 reference-exchange amount semantics gate")
    parser.add_argument("--rxep-bundle", type=Path, required=True)
    parser.add_argument("--rxep-receipt", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = preflight(args.rxep_bundle, rxep_receipt_path=args.rxep_receipt, source_path=args.source)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "reference-exchange-amount-semantics.json"
        record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        record_path.write_bytes(record_bytes)
        receipt = build_receipt(record, record_bytes)
        (args.output_dir / "reference-exchange-amount-semantics-receipt.json").write_bytes(
            (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {VERDICT}")
    print(f"REFERENCE EXCHANGE: {record['amount_semantics']['reference_exchange_internal_id']}")
    print(f"MEAN AMOUNT: {record['amount_semantics']['mean_amount']['lexical']}")
    print("RESULTING AMOUNT PRESENT: false")
    print("BUILDING QUANTITY MULTIPLICATION PERMITTED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
