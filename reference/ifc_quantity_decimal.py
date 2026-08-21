#!/usr/bin/env python3
"""ProofGrid v1.5.1 exact-decimal IFC declared quantity evidence.

Binds an accepted v1.5 mapping back to the exact hashed IFC STEP source and
preserves the mapped IfcQuantityWeight numeric token as source-authoritative
lexical evidence plus a canonical finite Decimal.

The mapped JSON/parser numeric value is used only as a consistency check. No
environmental calculation, multiplication, aggregation, or unit conversion is
performed.
"""

from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import ifc_declaration_product_map as v15  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Exact IFC Quantity Decimal Extractor"
ENGINE_VERSION = "1.5.1"
VERDICT = "IFC_DECLARED_QUANTITY_EXACT_DECIMAL_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = v15.CANONICALIZATION
SCHEMA_PATH = ROOT / "schemas" / "ifc-quantity-exact-decimal.schema.json"
_NUMBER_RE = re.compile(r"^[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[Ee][+-]?[0-9]+)?$")
_ENTITY_RE = re.compile(r"^#([0-9]+)\s*=\s*([A-Za-z0-9_]+)\s*\((.*)\)\s*;$", re.S)


class QuantityDecimalError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QuantityDecimalError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise QuantityDecimalError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QuantityDecimalError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def verify_mapping(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    require(record.get("verdict") == v15.VERDICT, "v1.5 mapping verdict mismatch")
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), "v1.5 mapping missing integrity")
    expected = integrity.get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, "v1.5 mapping missing content SHA-256")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow)) == expected, "v1.5 mapping content SHA-256 mismatch")

    require(receipt.get("verdict") == v15.VERDICT, "v1.5 mapping receipt verdict mismatch")
    receipt_sha = receipt.get("receipt_sha256")
    require(isinstance(receipt_sha, str) and len(receipt_sha) == 64, "v1.5 mapping receipt missing SHA-256")
    receipt_shadow = copy.deepcopy(receipt)
    receipt_shadow.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(receipt_shadow)) == receipt_sha, "v1.5 mapping receipt digest mismatch")
    require(receipt.get("record_content_sha256") == expected, "v1.5 mapping receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "v1.5 mapping receipt/file mismatch")
    require(receipt.get("ifc_source_sha256") == record.get("ifc", {}).get("source_sha256"), "v1.5 mapping receipt IFC-source mismatch")
    require(receipt.get("product_flow_uuid") == record.get("declaration", {}).get("product_flow_uuid"), "v1.5 mapping receipt product UUID mismatch")
    require(receipt.get("product_flow_version") == record.get("declaration", {}).get("product_flow_version"), "v1.5 mapping receipt product version mismatch")
    require(receipt.get("reference_unit") == record.get("declaration", {}).get("reference_unit"), "v1.5 mapping receipt reference-unit mismatch")

    for key in (
        "fuzzy_matching_performed",
        "automatic_name_mapping_performed",
        "environmental_calculation_performed",
        "building_quantity_multiplication_performed",
        "unit_conversion_performed",
        "scientific_validation_performed",
        "professional_review_performed",
        "certified",
    ):
        require(record.get(key) is False, f"v1.5 mapping {key} promotion rejected")
        if key in receipt:
            require(receipt.get(key) is False, f"v1.5 mapping receipt {key} promotion rejected")


def iter_step_statements(text: str) -> Iterator[str]:
    """Yield STEP statements separated by semicolons outside strings/comments."""
    start = 0
    i = 0
    in_string = False
    in_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_comment:
            if ch == "*" and nxt == "/":
                in_comment = False
                i += 2
                continue
            i += 1
            continue
        if not in_string and ch == "/" and nxt == "*":
            in_comment = True
            i += 2
            continue
        if ch == "'":
            if in_string and nxt == "'":
                i += 2
                continue
            in_string = not in_string
            i += 1
            continue
        if ch == ";" and not in_string:
            statement = text[start : i + 1].strip()
            if statement:
                yield statement
            start = i + 1
        i += 1
    require(not in_string, "unterminated STEP string")
    require(not in_comment, "unterminated STEP comment")
    tail = text[start:].strip()
    require(not tail, "unterminated STEP statement")


def split_step_arguments(inner: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth = 0
    i = 0
    in_string = False
    while i < len(inner):
        ch = inner[i]
        nxt = inner[i + 1] if i + 1 < len(inner) else ""
        if ch == "'":
            if in_string and nxt == "'":
                i += 2
                continue
            in_string = not in_string
            i += 1
            continue
        if not in_string:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                require(depth >= 0, "unbalanced STEP argument parentheses")
            elif ch == "," and depth == 0:
                args.append(inner[start:i].strip())
                start = i + 1
        i += 1
    require(not in_string, "unterminated STEP argument string")
    require(depth == 0, "unbalanced STEP argument parentheses")
    args.append(inner[start:].strip())
    return args


def decode_step_string(token: str, label: str) -> str:
    require(len(token) >= 2 and token.startswith("'") and token.endswith("'"), f"{label} is not a STEP string")
    return token[1:-1].replace("''", "'")


def canonical_decimal(token: str, label: str) -> str:
    require(bool(_NUMBER_RE.fullmatch(token)), f"{label} has unsupported or malformed STEP numeric token: {token!r}")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise QuantityDecimalError(f"{label} is not numeric: {token!r}") from exc
    require(value.is_finite(), f"{label} must be finite")
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    if rendered in {"", "-0", "+0"}:
        rendered = "0"
    return rendered


def locate_quantity_entity(source_raw: bytes, step_id: int, expected_type: str, expected_name: str) -> dict[str, Any]:
    # ISO-10303-21 source is ASCII-oriented; latin-1 is a byte-preserving decode
    # for statement scanning and does not reinterpret raw source bytes.
    text = source_raw.decode("latin-1")
    matches: list[tuple[str, str, list[str]]] = []
    for statement in iter_step_statements(text):
        match = _ENTITY_RE.match(statement)
        if not match:
            continue
        if int(match.group(1)) != step_id:
            continue
        entity_type = match.group(2).upper()
        args = split_step_arguments(match.group(3))
        matches.append((statement, entity_type, args))
    require(len(matches) == 1, f"quantity STEP ID #{step_id} missing or ambiguous: {len(matches)} matching entity definitions")
    statement, entity_type, args = matches[0]
    require(entity_type == expected_type.upper(), f"quantity STEP entity type mismatch: expected {expected_type}, got {entity_type}")
    require(entity_type == "IFCQUANTITYWEIGHT", f"v1.5.1 initial gate supports only IFCQUANTITYWEIGHT, got {entity_type}")
    require(len(args) >= 4, f"{entity_type} has too few attributes: {len(args)}")
    name = decode_step_string(args[0], "quantity Name")
    require(name == expected_name, f"quantity source name mismatch: expected {expected_name!r}, got {name!r}")
    lexical = args[3]
    decimal = canonical_decimal(lexical, "IfcQuantityWeight.WeightValue")
    return {
        "step_id": step_id,
        "entity_type": entity_type,
        "name": name,
        "quantity_lexical": lexical,
        "quantity_decimal": decimal,
        "statement_sha256": sha256_bytes(statement.encode("latin-1")),
    }


def extract(mapping: dict[str, Any], mapping_raw: bytes, mapping_receipt: dict[str, Any], source_raw: bytes) -> dict[str, Any]:
    verify_mapping(mapping, mapping_raw, mapping_receipt)
    ifc = mapping.get("ifc", {})
    quantity = ifc.get("quantity", {})
    source_sha = sha256_bytes(source_raw)
    require(source_sha == ifc.get("source_sha256"), "raw IFC source SHA-256 mismatch")
    require(quantity.get("unit_identity") == "kg", f"initial v1.5.1 quantity gate requires mapped unit identity kg, got {quantity.get('unit_identity')!r}")
    require(quantity.get("numerical_conversion_applied") is False, "mapped quantity already reports numerical conversion")
    step_id = quantity.get("quantity_step_id")
    require(isinstance(step_id, int) and step_id > 0, "mapped quantity STEP ID missing")
    expected_type = quantity.get("ifc_quantity_type")
    expected_name = quantity.get("name")
    require(isinstance(expected_type, str) and expected_type, "mapped quantity IFC type missing")
    require(isinstance(expected_name, str) and expected_name, "mapped quantity name missing")

    source_evidence = locate_quantity_entity(source_raw, step_id, expected_type, expected_name)
    mapped_value = quantity.get("value")
    require(isinstance(mapped_value, (int, float)) and not isinstance(mapped_value, bool), "mapped parser quantity must be numeric")
    try:
        mapped_decimal = Decimal(str(mapped_value))
    except InvalidOperation as exc:
        raise QuantityDecimalError("mapped parser quantity is not Decimal-compatible") from exc
    require(mapped_decimal.is_finite(), "mapped parser quantity must be finite")
    require(mapped_decimal == Decimal(source_evidence["quantity_decimal"]), "mapped parser quantity disagrees with source-authoritative Decimal")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridIFCDeclaredQuantityExactDecimal",
        "verdict": VERDICT,
        "ifc_source": {
            "sha256": source_sha,
            "schema": ifc.get("schema"),
        },
        "mapping_evidence": {
            "mapping_id": mapping.get("mapping_id"),
            "mapping_content_sha256": mapping["integrity"]["content_sha256"],
            "mapping_file_sha256": sha256_bytes(mapping_raw),
            "mapping_receipt_sha256": mapping_receipt["receipt_sha256"],
            "product_flow_uuid": mapping.get("declaration", {}).get("product_flow_uuid"),
            "product_flow_version": mapping.get("declaration", {}).get("product_flow_version"),
        },
        "ifc_identity": {
            "element_step_id": ifc.get("element", {}).get("step_id"),
            "element_global_id": ifc.get("element", {}).get("global_id"),
            "material_association_step_id": ifc.get("material", {}).get("association_step_id"),
            "material_step_id": ifc.get("material", {}).get("material_step_id"),
            "quantity_step_id": step_id,
            "quantity_entity_type": source_evidence["entity_type"],
            "quantity_name": source_evidence["name"],
            "quantity_statement_sha256": source_evidence["statement_sha256"],
        },
        "quantity": {
            "quantity_lexical": source_evidence["quantity_lexical"],
            "quantity_decimal": source_evidence["quantity_decimal"],
            "mapped_parser_numeric_string": str(mapped_value),
            "mapped_parser_consistent_with_source": True,
            "unit_identity": "kg",
            "source_token_is_authority": True,
            "parser_numeric_value_is_authority": False,
        },
        "calculation_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "The exact STEP numeric token is the quantity evidence authority; the IfcOpenShell/JSON numeric value is used only as a consistency check.",
            "This initial gate supports only the exact mapped IfcQuantityWeight/kg identity path; non-identity units require a separate conversion gate.",
            "No environmental result is scaled or multiplied by this quantity.",
            "Passing this gate does not establish scientific validity, professional review, engineering approval, provider authority, regulatory approval, or certification.",
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


def validate_schema(record: dict[str, Any]) -> None:
    schema, _ = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise QuantityDecimalError(f"invalid v1.5.1 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise QuantityDecimalError(f"IFC quantity exact-decimal schema validation failed: {preview}")


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "ifc_source_sha256": record["ifc_source"]["sha256"],
        "mapping_evidence": copy.deepcopy(record["mapping_evidence"]),
        "ifc_identity": copy.deepcopy(record["ifc_identity"]),
        "quantity": copy.deepcopy(record["quantity"]),
        "calculation_performed": False,
        "environmental_calculation_performed": False,
        "building_quantity_multiplication_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.5.1 exact-decimal IFC quantity evidence")
    parser.add_argument("--ifc-source", type=Path, required=True)
    parser.add_argument("--mapping-record", type=Path, required=True)
    parser.add_argument("--mapping-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mapping, mapping_raw = load_json(args.mapping_record)
        mapping_receipt, _ = load_json(args.mapping_receipt)
        source_raw = args.ifc_source.read_bytes()
        record = extract(mapping, mapping_raw, mapping_receipt, source_raw)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "ifc-declared-quantity-exact-decimal.json"
        record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        record_path.write_bytes(record_bytes)
        receipt = build_receipt(record, record_bytes)
        (args.output_dir / "ifc-declared-quantity-exact-decimal-receipt.json").write_bytes(
            (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"SOURCE TOKEN: {record['quantity']['quantity_lexical']}")
    print(f"CANONICAL DECIMAL: {record['quantity']['quantity_decimal']}")
    print("SOURCE TOKEN IS AUTHORITY: true")
    print("CALCULATION PERFORMED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
