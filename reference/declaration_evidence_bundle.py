#!/usr/bin/env python3
"""ProofGrid v1.4 source-bound declaration evidence composition gate.

Binds already-accepted evidence dimensions for one exact declaration:

* hardened v1.1.1 declared environmental indicator evidence;
* v1.3 declared reference-basis evidence;
* v1.3.1 reference-exchange amount-semantics evidence.

This module performs no environmental calculation, multiplication, aggregation,
scenario selection, missing-value zeroing, or unit conversion.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "declaration-evidence-bundle.schema.json"

ENGINE_NAME = "RegenExcalibur ProofGrid Declaration Evidence Binder"
ENGINE_VERSION = "1.4.0"
VERDICT = "DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
V13_ACCEPTED_HEAD = "77931d81ae9857eb33b3cecaf8f9180f0c2b7e4a"
AMOUNT_POLICY = "MEAN_AMOUNT_ACCEPTED_ONLY_WHEN_RESULTING_AMOUNT_ABSENT"

EXPECTED_V12_STACK = {
    "validator": {
        "coordinate": "com.okworx.ilcd.validation:ilcd-validation:2.12.2",
        "jar_sha256": "55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b",
        "pom_sha256": "16430562fe6ebb6da3e4afea4a8c6cce98d822d61f59eb33e0b5dc98a4eb1fc1",
    },
    "profile": {
        "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
        "jar_sha256": "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e",
        "pom_sha256": "0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a",
    },
    "included_profiles": {
        "EPD-1.2-Generic.jar": "31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25",
        "EPD-1.2-EN15804.jar": "a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147",
    },
}
EXPECTED_V12_STACK_SHA256 = "dc06197b5b7cff763a53023f7adafea2423ddd4c9ec22c36215c776d8b301df6"


class BundleError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise BundleError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def verify_record_integrity(record: dict[str, Any], *, label: str) -> str:
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), f"{label} missing integrity object")
    expected = integrity.get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, f"{label} missing content SHA-256")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"{label} content SHA-256 mismatch")
    return expected


def verify_receipt(receipt: dict[str, Any], *, label: str, verdict: str) -> str:
    require(receipt.get("verdict") == verdict, f"{label} verdict mismatch")
    expected = receipt.get("receipt_sha256")
    require(isinstance(expected, str) and len(expected) == 64, f"{label} missing receipt SHA-256")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"{label} receipt digest mismatch")
    require(receipt.get("certified") is False, f"{label} certification promotion rejected")
    return expected


def verify_canonical_source(record: dict[str, Any], *, indicator_record: dict[str, Any]) -> None:
    require(record.get("verdict") == "ADMITTED_ENVIRONMENTAL_SOURCE_IDENTITY_VERIFIABLE", "canonical-source verdict mismatch")
    require(record.get("certified") is False, "canonical-source certification promotion rejected")
    require(record.get("scientific_validation_performed") is False, "canonical-source scientific-validation promotion rejected")
    require(record.get("professional_review_performed") is False, "canonical-source professional-review promotion rejected")
    digest = verify_record_integrity(record, label="canonical source")
    pointer = indicator_record.get("canonical_source")
    require(isinstance(pointer, dict), "declared-indicator record missing canonical-source pointer")
    require(pointer.get("content_sha256") == digest, "declared-indicator/canonical-source digest mismatch")
    require(pointer.get("record_id") == record.get("id"), "declared-indicator/canonical-source record-id mismatch")
    require(pointer.get("verdict") == record.get("verdict"), "declared-indicator/canonical-source verdict mismatch")

    version = record.get("source", {}).get("format_version")
    conformance = record.get("conformance", {})
    if version == "1.2":
        require(conformance.get("profile_validation_performed") is True, "v1.2 canonical source requires profile validation")
        require(conformance.get("official_stack") == EXPECTED_V12_STACK, "v1.2 official validator/profile stack mismatch")
        require(conformance.get("official_stack_sha256") == EXPECTED_V12_STACK_SHA256, "v1.2 official stack digest mismatch")
        require(conformance.get("claim_token") == "OEKOBAUDAT_V12_PROFILE_380_SYNTHETIC_AUTHORITY_SAFE_COMPATIBLE", "v1.2 profile claim mismatch")
        require(conformance.get("error_count") == 0, "v1.2 profile contains validation errors")
    elif version == "1.3":
        require(conformance.get("profile_validation_performed") is False, "v1.3 profile overclaim rejected")
        require(conformance.get("verdict") == "ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT", "v1.3 conformance verdict mismatch")
        require(conformance.get("xsd_validation") is True, "v1.3 XSD validation missing")
        require(conformance.get("master_data_identity_validation") is True, "v1.3 master-data validation missing")
    else:
        raise BundleError(f"unsupported canonical-source format version: {version!r}")


def verify_indicator(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    require(record.get("verdict") == "DECLARED_ENVIRONMENTAL_INDICATORS_EXTRACTED_VERIFIABLE", "declared-indicator verdict mismatch")
    require(record.get("certified") is False, "declared-indicator certification promotion rejected")
    require(record.get("calculated") is False, "declared-indicator calculated promotion rejected")
    require(record.get("unit_conversion_performed") is False, "declared-indicator conversion promotion rejected")
    require(record.get("professional_review_performed") is False, "declared-indicator professional-review promotion rejected")
    content = verify_record_integrity(record, label="declared indicators")
    verify_receipt(receipt, label="declared-indicator receipt", verdict="DECLARED_ENVIRONMENTAL_INDICATORS_EXTRACTED_VERIFIABLE")
    require(receipt.get("record_content_sha256") == content, "declared-indicator receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "declared-indicator receipt/file mismatch")
    source = record.get("source", {})
    require(receipt.get("source_sha256") == source.get("sha256"), "declared-indicator source binding mismatch")
    require(receipt.get("process_xml_sha256") == source.get("process_xml_sha256"), "declared-indicator process-XML binding mismatch")
    require(receipt.get("process_dataset_uuid") == source.get("process_dataset_uuid"), "declared-indicator process UUID binding mismatch")
    require(receipt.get("format_version") == source.get("format_version"), "declared-indicator format binding mismatch")
    rows = record.get("rows")
    require(isinstance(rows, list) and len(rows) > 0, "declared-indicator rows missing")
    env_unit = record.get("indicator_scope", {}).get("canonical_unit")
    require(isinstance(env_unit, str) and env_unit, "declared environmental-result unit missing")
    for index, row in enumerate(rows):
        require(row.get("canonical_unit") == env_unit, f"declared row {index} unit differs from indicator scope")
        require(row.get("value_origin") == "DECLARED_IN_SOURCE", f"declared row {index} origin mismatch")
        require(row.get("calculated") is False, f"declared row {index} calculated promotion rejected")
        require(row.get("unit_conversion_performed") is False, f"declared row {index} conversion promotion rejected")


def verify_basis(record: dict[str, Any], raw: bytes, receipt: dict[str, Any]) -> None:
    require(record.get("verdict") == "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE", "reference-basis verdict mismatch")
    require(record.get("certified") is False, "reference-basis certification promotion rejected")
    require(record.get("calculated") is False, "reference-basis calculated promotion rejected")
    require(record.get("environmental_values_transformed") is False, "reference-basis environmental transformation rejected")
    require(record.get("unit_conversion_performed") is False, "reference-basis conversion promotion rejected")
    content = verify_record_integrity(record, label="reference basis")
    verify_receipt(receipt, label="reference-basis receipt", verdict="DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE")
    require(receipt.get("record_content_sha256") == content, "reference-basis receipt/content mismatch")
    require(receipt.get("record_file_sha256") == sha256_bytes(raw), "reference-basis receipt/file mismatch")
    parent = record.get("parent", {})
    require(receipt.get("source_sha256") == parent.get("source_sha256"), "reference-basis source binding mismatch")
    require(receipt.get("process_dataset_uuid") == parent.get("process_dataset_uuid"), "reference-basis process UUID binding mismatch")
    require(receipt.get("format_version") == parent.get("format_version"), "reference-basis format binding mismatch")
    basis = record.get("declared_reference_basis", {})
    require(basis.get("basis_status") == "IDENTITY_CHAIN_VERIFIED", "reference-basis identity chain not verified")
    require(basis.get("identity_chain") is True, "reference-basis identity flag missing")


def verify_semantics(evidence: dict[str, Any], raw: bytes, integration: dict[str, Any], *, format_version: str, basis_record: dict[str, Any]) -> None:
    verify_receipt(integration, label="amount-semantics integration receipt", verdict="REFERENCE_EXCHANGE_AMOUNT_SEMANTICS_RESOLVED_VERIFIABLE")
    require(integration.get("accepted_parent_v13_head") == V13_ACCEPTED_HEAD, "amount-semantics accepted-parent head mismatch")
    require(integration.get("selection_policy") == AMOUNT_POLICY, "amount-semantics integration policy mismatch")
    require(integration.get("controlled_resulting_amount_rejected") is True, "amount-semantics negative-control proof missing")
    require(integration.get("building_quantity_multiplication_permitted") is False, "amount-semantics multiplication promotion rejected")
    for key in ("calculated", "environmental_values_transformed", "unit_conversion_performed", "scientific_validation_performed", "professional_review_performed", "certified"):
        require(integration.get(key) is False, f"amount-semantics {key} promotion rejected")

    expected_file_key = "v12_evidence_file_sha256" if format_version == "1.2" else "v13_evidence_file_sha256"
    require(integration.get(expected_file_key) == sha256_bytes(raw), "amount-semantics evidence-file hash mismatch")
    expected_absent_key = "resulting_amount_absent_in_pinned_v12" if format_version == "1.2" else "resulting_amount_absent_in_pinned_v13"
    require(integration.get(expected_absent_key) is True, "amount-semantics pinned absence proof missing")

    process_ref = basis_record.get("process_reference", {})
    require(evidence.get("format_version") == format_version, "amount-semantics format mismatch")
    require(evidence.get("reference_exchange_internal_id") == process_ref.get("reference_exchange_internal_id"), "amount-semantics reference-exchange mismatch")
    require(evidence.get("mean_amount", {}).get("lexical") == process_ref.get("exchange_amount_lexical"), "amount-semantics mean lexical mismatch")
    require(evidence.get("mean_amount", {}).get("decimal") == process_ref.get("exchange_amount_decimal"), "amount-semantics mean Decimal mismatch")
    require(evidence.get("resulting_amount_present") is False, "unresolved resultingAmount rejected")
    require(evidence.get("resulting_amount") is None, "unresolved resultingAmount evidence rejected")
    require(evidence.get("selection_policy") == AMOUNT_POLICY, "amount-semantics evidence policy mismatch")


def bind(
    canonical_source: dict[str, Any],
    *,
    indicator_record: dict[str, Any],
    indicator_raw: bytes,
    indicator_receipt: dict[str, Any],
    basis_record: dict[str, Any],
    basis_raw: bytes,
    basis_receipt: dict[str, Any],
    semantics_evidence: dict[str, Any],
    semantics_raw: bytes,
    semantics_integration_receipt: dict[str, Any],
) -> dict[str, Any]:
    verify_indicator(indicator_record, indicator_raw, indicator_receipt)
    verify_canonical_source(canonical_source, indicator_record=indicator_record)
    verify_basis(basis_record, basis_raw, basis_receipt)

    indicator_source = indicator_record["source"]
    basis_parent = basis_record["parent"]
    canonical_identity = canonical_source["identity"]
    canonical_source_meta = canonical_source["source"]

    require(indicator_source["sha256"] == basis_parent["source_sha256"] == canonical_source_meta["sha256"], "parent source SHA-256 mismatch")
    require(indicator_source["process_xml_sha256"] == basis_parent["process_xml_sha256"] == canonical_identity["process_xml_sha256"], "parent process XML SHA-256 mismatch")
    require(indicator_source["process_dataset_uuid"] == basis_parent["process_dataset_uuid"] == canonical_identity["process_dataset_uuid"], "parent process UUID mismatch")
    require(indicator_source["format_version"] == basis_parent["format_version"] == canonical_source_meta["format_version"], "parent format-version mismatch")
    format_version = indicator_source["format_version"]

    verify_semantics(
        semantics_evidence,
        semantics_raw,
        semantics_integration_receipt,
        format_version=format_version,
        basis_record=basis_record,
    )

    environmental_unit = indicator_record["indicator_scope"]["canonical_unit"]
    product_unit = basis_record["declared_reference_basis"]["unit"]
    require(environmental_unit != product_unit, "environmental-result unit and product reference unit must remain distinct dimensions")
    require(basis_record["declared_reference_basis"]["quantity_decimal"] == semantics_evidence["mean_amount"]["decimal"], "reference-basis quantity/meanAmount mismatch")
    require(basis_record["process_reference"]["reference_exchange_internal_id"] == semantics_evidence["reference_exchange_internal_id"], "reference-basis/amount-semantics exchange mismatch")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclarationEvidenceBundle",
        "verdict": VERDICT,
        "source_identity": {
            "source_sha256": indicator_source["sha256"],
            "process_xml_sha256": indicator_source["process_xml_sha256"],
            "process_dataset_uuid": indicator_source["process_dataset_uuid"],
            "format_version": format_version,
            "canonical_source_content_sha256": canonical_source["integrity"]["content_sha256"],
        },
        "parent_evidence": {
            "declared_indicators": {
                "record_content_sha256": indicator_record["integrity"]["content_sha256"],
                "record_file_sha256": sha256_bytes(indicator_raw),
                "receipt_sha256": indicator_receipt["receipt_sha256"],
            },
            "declared_reference_basis": {
                "record_content_sha256": basis_record["integrity"]["content_sha256"],
                "record_file_sha256": sha256_bytes(basis_raw),
                "receipt_sha256": basis_receipt["receipt_sha256"],
            },
            "amount_semantics": {
                "evidence_file_sha256": sha256_bytes(semantics_raw),
                "integration_receipt_sha256": semantics_integration_receipt["receipt_sha256"],
                "accepted_parent_v13_head": semantics_integration_receipt["accepted_parent_v13_head"],
            },
        },
        "environmental_results": {
            "indicator_scope": copy.deepcopy(indicator_record["indicator_scope"]),
            "rows": copy.deepcopy(indicator_record["rows"]),
            "row_count": len(indicator_record["rows"]),
            "value_origin": "DECLARED_IN_SOURCE",
            "aggregation_performed": False,
            "missing_modules_are_zero": False,
        },
        "declared_reference_basis": copy.deepcopy(basis_record["declared_reference_basis"]),
        "amount_semantics": copy.deepcopy(semantics_evidence),
        "dimension_separation": {
            "environmental_result_unit": environmental_unit,
            "product_reference_unit": product_unit,
            "same_dimension": False,
            "unit_interchange_permitted": False,
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "This bundle binds independently accepted evidence dimensions to one exact source/process identity; it does not calculate an environmental impact.",
            "Environmental-result units and product/reference-basis units remain distinct dimensions and are not converted or divided by v1.4.",
            "No lifecycle-module aggregation, scenario selection, missing-value zeroing, building/material quantity multiplication, or unit conversion is performed.",
            "Evidence binding does not establish scientific validity, professional LCA review, provider/programme-operator authority, regulatory approval, building applicability, or certification.",
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
        raise BundleError(f"invalid v1.4 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise BundleError(f"declaration evidence bundle schema validation failed: {preview}")


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "source_identity": copy.deepcopy(record["source_identity"]),
        "parent_evidence": copy.deepcopy(record["parent_evidence"]),
        "row_count": record["environmental_results"]["row_count"],
        "declared_reference_basis": copy.deepcopy(record["declared_reference_basis"]),
        "dimension_separation": copy.deepcopy(record["dimension_separation"]),
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.4 declaration evidence binder")
    parser.add_argument("--canonical-source", type=Path, required=True)
    parser.add_argument("--indicator-record", type=Path, required=True)
    parser.add_argument("--indicator-receipt", type=Path, required=True)
    parser.add_argument("--basis-record", type=Path, required=True)
    parser.add_argument("--basis-receipt", type=Path, required=True)
    parser.add_argument("--semantics-evidence", type=Path, required=True)
    parser.add_argument("--semantics-integration-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        canonical_source, _ = load_json(args.canonical_source)
        indicator_record, indicator_raw = load_json(args.indicator_record)
        indicator_receipt, _ = load_json(args.indicator_receipt)
        basis_record, basis_raw = load_json(args.basis_record)
        basis_receipt, _ = load_json(args.basis_receipt)
        semantics_evidence, semantics_raw = load_json(args.semantics_evidence)
        semantics_receipt, _ = load_json(args.semantics_integration_receipt)
        record = bind(
            canonical_source,
            indicator_record=indicator_record,
            indicator_raw=indicator_raw,
            indicator_receipt=indicator_receipt,
            basis_record=basis_record,
            basis_raw=basis_raw,
            basis_receipt=basis_receipt,
            semantics_evidence=semantics_evidence,
            semantics_raw=semantics_raw,
            semantics_integration_receipt=semantics_receipt,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "declaration-evidence-bundle.json"
        record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        record_path.write_bytes(record_bytes)
        receipt = build_receipt(record, record_bytes)
        (args.output_dir / "declaration-evidence-bundle-receipt.json").write_bytes(
            (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {VERDICT}")
    print(f"FORMAT: {record['source_identity']['format_version']}")
    print(f"ROWS: {record['environmental_results']['row_count']}")
    print(f"REFERENCE BASIS: {record['declared_reference_basis']['quantity_decimal']} {record['declared_reference_basis']['unit']}")
    print("BUILDING QUANTITY MULTIPLICATION PERFORMED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
