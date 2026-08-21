#!/usr/bin/env python3
"""ProofGrid v1.3 declared quantitative-reference basis extractor.

The extractor consumes an accepted RXEP v0.2 declared-indicator bundle, the
exact admitted source bytes, and an explicitly staged reference closure. It
resolves the process reference-flow -> product-flow -> reference flow-property
-> reference unit-group -> reference unit chain using exact internal IDs,
UUIDs, versions, hashes, and Decimal strings.

The initial accepted scope is deliberately narrow: the pinned InData public
wood-panel v1.2/v1.3 fixtures whose three scaling components are exact identity
values (1, 1, 1 kg). No environmental indicator value is transformed.
"""

from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import zipfile

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import rxep_declared_indicator_binding as rxep  # noqa: E402
from reference import environmental_admission as admission  # noqa: E402
from conformance.reference_basis_v13 import research_probe  # type: ignore  # noqa: E402

# Importing from a hyphenated directory is not possible as a Python package.
# The fallback loader below is used in normal execution.

ENGINE_NAME = "RegenExcalibur ProofGrid Declared Reference Basis Extractor"
ENGINE_VERSION = "1.3.0"
VERDICT = "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
RESEARCH_RECEIPT_SHA256 = "e118ccd9d8eec14008c589cd44e3640e74a640fd1cc3231c4526e644abe2ab40"
SCHEMA_PATH = ROOT / "schemas" / "declared-reference-basis.schema.json"


class BasisError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BasisError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise BasisError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BasisError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def canonical_decimal(lexical: str, label: str) -> str:
    text = lexical.strip()
    require(bool(text), f"{label} is empty")
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise BasisError(f"{label} is not numeric: {text!r}") from exc
    require(number.is_finite(), f"{label} must be finite")
    if number == 0:
        return "0"
    rendered = format(number.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def verify_canonical_receipt(receipt: dict[str, Any], label: str) -> str:
    expected = receipt.get("receipt_sha256")
    require(isinstance(expected, str) and len(expected) == 64, f"{label} receipt_sha256 missing")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"{label} receipt digest mismatch: expected {expected}, got {actual}")
    return actual


def verify_rxep_parent(bundle: dict[str, Any], bundle_bytes: bytes, receipt: dict[str, Any]) -> None:
    try:
        rxep.validate_bundle(bundle)
    except Exception as exc:
        raise BasisError(f"RXEP v0.2 bundle schema validation failed: {exc}") from exc

    require(bundle.get("verdict") == rxep.VERDICT, "wrong RXEP v0.2 parent verdict")
    require(bundle.get("protocol_version") == "0.2", "wrong RXEP parent protocol version")
    require(bundle.get("review_state") == "CLAIMED", "RXEP parent must remain CLAIMED")
    require(bundle.get("signed") is False, "RXEP parent must remain unsigned")
    require(bundle.get("certified") is False, "RXEP parent must remain certified=false")

    expected = bundle.get("integrity", {}).get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, "RXEP bundle integrity digest missing")
    shadow = copy.deepcopy(bundle)
    shadow["integrity"]["content_sha256"] = rxep.ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"RXEP bundle integrity mismatch: expected {expected}, got {actual}")

    verify_canonical_receipt(receipt, "RXEP binding")
    require(receipt.get("verdict") == rxep.VERDICT, "wrong RXEP binding receipt verdict")
    require(receipt.get("protocol_version") == "0.2", "wrong RXEP binding receipt protocol")
    require(receipt.get("review_state") == "CLAIMED", "RXEP binding receipt must remain CLAIMED")
    require(receipt.get("signed") is False, "RXEP binding receipt must remain unsigned")
    require(receipt.get("certified") is False, "RXEP binding receipt must remain certified=false")
    require(receipt.get("bundle_content_sha256") == expected, "RXEP receipt/bundle content mismatch")
    require(receipt.get("bundle_file_sha256") == sha256_bytes(bundle_bytes), "RXEP receipt/bundle file mismatch")
    require(receipt.get("source_sha256") == bundle["parent"]["source_sha256"], "RXEP receipt/source mismatch")
    require(receipt.get("process_dataset_uuid") == bundle["parent"]["process_dataset_uuid"], "RXEP receipt/process UUID mismatch")
    require(receipt.get("format_version") == bundle["parent"]["format_version"], "RXEP receipt/format mismatch")

    for envelope in bundle.get("envelopes", []):
        require(envelope.get("review") == {"state": "CLAIMED", "reviewer": None}, "RXEP envelope review state promotion detected")
        require(envelope.get("integrity", {}).get("signature") is None, "RXEP envelope signature must remain null")
        measurement = envelope.get("measurement", {})
        require(measurement.get("calculated") is False, "RXEP parent may not contain calculated=true")
        require(measurement.get("unit_conversion_performed") is False, "RXEP parent may not contain unit conversion")
        dims = envelope.get("evidence_dimensions", {})
        require(dims.get("scientific_validity") == "NOT_EVALUATED", "scientific validity promotion detected")
        require(dims.get("professional_review") == "NOT_EVALUATED", "professional review promotion detected")
        require(dims.get("certification") == "NOT_EVALUATED", "certification promotion detected")


def verify_research_receipt(research: dict[str, Any]) -> None:
    verify_canonical_receipt(research, "v1.3 research")
    require(research.get("receipt_sha256") == RESEARCH_RECEIPT_SHA256, "unexpected v1.3 research-freeze receipt")
    require(research.get("verdict") == "DECLARED_REFERENCE_BASIS_RESEARCH_VERIFIABLE", "wrong research verdict")
    require(research.get("extractor_accepted") is False, "research receipt must remain research-only")
    require(research.get("calculated") is False, "research receipt may not claim calculation")
    require(research.get("environmental_values_transformed") is False, "research receipt may not transform environmental values")
    require(research.get("unit_conversion_performed") is False, "research receipt may not claim unit conversion")
    require(research.get("scientific_validation_performed") is False, "research receipt may not claim scientific validation")
    require(research.get("professional_review_performed") is False, "research receipt may not claim professional review")
    require(research.get("certified") is False, "research receipt must remain certified=false")


def source_process_bytes(source_path: Path, format_version: str, expected_source_sha: str) -> bytes:
    require(sha256_file(source_path) == expected_source_sha, "admitted source SHA-256 mismatch")
    if format_version == "1.3":
        raw = source_path.read_bytes()
        require(sha256_bytes(raw) == expected_source_sha, "v1.3 source byte mismatch")
        return raw
    require(format_version == "1.2", f"unsupported format version: {format_version}")
    require(zipfile.is_zipfile(source_path), "v1.2 parent source must be a ZIP")
    with zipfile.ZipFile(source_path, "r") as zf:
        candidates: list[bytes] = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            safe = admission.safe_zip_name(info.filename).as_posix()
            if safe.startswith("ILCD/processes/") and safe.lower().endswith(".xml"):
                candidates.append(zf.read(info))
        require(len(candidates) == 1, f"v1.2 source must contain exactly one process dataset, got {len(candidates)}")
        return candidates[0]


def validate_schema(record: dict[str, Any]) -> None:
    schema, _ = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise BasisError(f"invalid v1.3 schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        preview = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:8])
        raise BasisError(f"declared reference-basis schema validation failed: {preview}")


def load_probe_module():
    import importlib.util

    path = ROOT / "conformance" / "reference-basis-v13" / "research_probe.py"
    spec = importlib.util.spec_from_file_location("proofgrid_v13_research_probe", path)
    require(spec is not None and spec.loader is not None, "unable to load v1.3 research probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract(
    rxep_bundle_path: Path,
    *,
    rxep_receipt_path: Path,
    source_path: Path,
    product_flow_path: Path,
    flow_property_master_path: Path,
    unit_group_master_path: Path,
    research_receipt_path: Path,
) -> dict[str, Any]:
    bundle, bundle_bytes = load_json(rxep_bundle_path)
    binding_receipt, _ = load_json(rxep_receipt_path)
    research, _ = load_json(research_receipt_path)
    verify_rxep_parent(bundle, bundle_bytes, binding_receipt)
    verify_research_receipt(research)

    parent = bundle["parent"]
    format_version = parent["format_version"]
    process_raw = source_process_bytes(source_path, format_version, parent["source_sha256"])
    require(sha256_bytes(process_raw) == parent["process_xml_sha256"], "RXEP parent/process XML SHA-256 mismatch")

    expected_process_evidence = research["file_evidence"]["v12_process" if format_version == "1.2" else "v13_process"]
    require(sha256_bytes(process_raw) == expected_process_evidence["sha256"], "process bytes do not match frozen research source")

    expected_flow_evidence = research["file_evidence"]["v12_product_flow" if format_version == "1.2" else "v13_product_flow"]
    require(sha256_file(product_flow_path) == expected_flow_evidence["sha256"], "product-flow reference-closure hash mismatch")
    require(sha256_file(flow_property_master_path) == research["file_evidence"]["flow_property_master"]["sha256"], "flow-property master hash mismatch")
    require(sha256_file(unit_group_master_path) == research["file_evidence"]["unit_group_master"]["sha256"], "unit-group master hash mismatch")

    probe = load_probe_module()
    with tempfile.TemporaryDirectory(prefix="proofgrid-v13-") as tmp:
        process_tmp = Path(tmp) / "process.xml"
        process_tmp.write_bytes(process_raw)
        process = probe.inspect_process(process_tmp, format_version)
    flow = probe.inspect_flow(product_flow_path)
    flow_property = probe.inspect_flow_property(flow_property_master_path)
    unit_group = probe.inspect_unit_group(unit_group_master_path)

    require(process["process_uuid"] == parent["process_dataset_uuid"], "process UUID differs from RXEP parent")
    require(process["product_flow_uuid"] == flow["flow_uuid"], "process/product-flow UUID chain mismatch")
    require(process["product_flow_version"] == flow["flow_version"], "process/product-flow version chain mismatch")
    require(flow["flow_property_uuid"] == flow_property["flow_property_uuid"], "flow/flow-property UUID chain mismatch")
    require(flow["flow_property_version"] == flow_property["flow_property_version"], "flow/flow-property version chain mismatch")
    require(flow_property["reference_unit_group_uuid"] == unit_group["unit_group_uuid"], "flow-property/unit-group UUID chain mismatch")

    process_amount = process["exchange_amount"]["decimal"]
    property_mean = flow["flow_property_mean"]["decimal"]
    unit_factor = unit_group["reference_unit_factor"]["decimal"]
    # Initial v1.3 scope accepts identity chains only. Broader scaling/conversion
    # requires a separate calculation/conversion gate.
    require(process_amount == "1", "initial v1.3 scope requires process reference amount exactly 1")
    require(property_mean == "1", "initial v1.3 scope requires reference flow-property mean exactly 1")
    require(unit_factor == "1", "non-identity unit factor requires a separate explicit conversion gate")

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredReferenceBasis",
        "verdict": VERDICT,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "parent": {
            "rxep_verdict": bundle["verdict"],
            "rxep_protocol_version": bundle["protocol_version"],
            "rxep_bundle_content_sha256": bundle["integrity"]["content_sha256"],
            "rxep_bundle_file_sha256": sha256_bytes(bundle_bytes),
            "rxep_binding_receipt_sha256": binding_receipt["receipt_sha256"],
            "source_sha256": parent["source_sha256"],
            "process_xml_sha256": parent["process_xml_sha256"],
            "process_dataset_uuid": parent["process_dataset_uuid"],
            "format_version": format_version,
        },
        "process_reference": {
            "quantitative_reference_type": process["quantitative_reference_type"],
            "reference_exchange_internal_id": process["reference_exchange_internal_id"],
            "product_flow_uuid": process["product_flow_uuid"],
            "product_flow_version": process["product_flow_version"],
            "exchange_amount_lexical": process["exchange_amount"]["lexical"],
            "exchange_amount_decimal": process_amount,
        },
        "product_flow": {
            "uuid": flow["flow_uuid"],
            "version": flow["flow_version"],
            "names": flow["names"],
            "sha256": sha256_file(product_flow_path),
            "reference_flow_property_internal_id": flow["reference_flow_property_internal_id"],
        },
        "flow_property": {
            "uuid": flow_property["flow_property_uuid"],
            "version": flow_property["flow_property_version"],
            "names": flow_property["names"],
            "flow_mean_lexical": flow["flow_property_mean"]["lexical"],
            "flow_mean_decimal": property_mean,
            "master_sha256": sha256_file(flow_property_master_path),
            "reference_unit_group_uuid": flow_property["reference_unit_group_uuid"],
        },
        "reference_unit": {
            "unit_group_uuid": unit_group["unit_group_uuid"],
            "unit_group_version": unit_group["unit_group_version"],
            "unit_group_master_sha256": sha256_file(unit_group_master_path),
            "reference_unit_internal_id": unit_group["reference_unit_internal_id"],
            "name": unit_group["reference_unit_name"],
            "factor_lexical": unit_group["reference_unit_factor"]["lexical"],
            "factor_decimal": unit_factor,
        },
        "declared_reference_basis": {
            "basis_status": "IDENTITY_CHAIN_VERIFIED",
            "quantity_decimal": "1",
            "unit": unit_group["reference_unit_name"],
            "product_flow_uuid": flow["flow_uuid"],
            "identity_chain": True,
            "statement": f"The pinned declaration reference chain resolves to 1 {unit_group['reference_unit_name']} of the referenced product flow {flow['flow_uuid']}.",
        },
        "reference_closure": {
            "research_receipt_sha256": research["receipt_sha256"],
            "resolution_policy": "EXPLICIT_PINNED_REFERENCE_CLOSURE_ONLY_NO_NETWORK_OR_FUZZY_LOOKUP",
            "files": [
                {"role": "PRODUCT_FLOW", "sha256": sha256_file(product_flow_path)},
                {"role": "FLOW_PROPERTY_MASTER", "sha256": sha256_file(flow_property_master_path)},
                {"role": "UNIT_GROUP_MASTER", "sha256": sha256_file(unit_group_master_path)},
            ],
        },
        "limitations": [
            "This record proves the declared reference-basis identity chain for the exact pinned source/reference closure only; it is not a universal EPD rule.",
            "No environmental indicator value is divided, multiplied, aggregated, converted, or otherwise transformed by v1.3.",
            "The initial extractor accepts identity scaling only; any non-identity factor requires a separately specified calculation/conversion gate.",
            "Reference-closure provenance does not establish scientific validity, professional LCA review, provider authority, regulatory approval, or certification.",
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
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "rxep_binding_receipt_sha256": record["parent"]["rxep_binding_receipt_sha256"],
        "rxep_bundle_content_sha256": record["parent"]["rxep_bundle_content_sha256"],
        "source_sha256": record["parent"]["source_sha256"],
        "process_dataset_uuid": record["parent"]["process_dataset_uuid"],
        "format_version": record["parent"]["format_version"],
        "research_receipt_sha256": record["reference_closure"]["research_receipt_sha256"],
        "declared_reference_basis": record["declared_reference_basis"],
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.3 declared reference-basis extractor")
    parser.add_argument("--rxep-bundle", type=Path, required=True)
    parser.add_argument("--rxep-receipt", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--product-flow", type=Path, required=True)
    parser.add_argument("--flow-property-master", type=Path, required=True)
    parser.add_argument("--unit-group-master", type=Path, required=True)
    parser.add_argument("--research-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = extract(
            args.rxep_bundle,
            rxep_receipt_path=args.rxep_receipt,
            source_path=args.source,
            product_flow_path=args.product_flow,
            flow_property_master_path=args.flow_property_master,
            unit_group_master_path=args.unit_group_master,
            research_receipt_path=args.research_receipt,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.output_dir / "declared-reference-basis.json"
        record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        record_path.write_bytes(record_bytes)
        receipt = build_receipt(record, record_bytes)
        (args.output_dir / "declared-reference-basis-receipt.json").write_bytes(
            (json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {VERDICT}")
    print(f"REFERENCE BASIS: {record['declared_reference_basis']['quantity_decimal']} {record['declared_reference_basis']['unit']}")
    print("ENVIRONMENTAL VALUES TRANSFORMED: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
