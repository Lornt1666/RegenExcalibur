#!/usr/bin/env python3
"""ProofGrid v3.2 binding suitability decision for one real IFC/source pair.

Consumes independently reproduced candidate-neighborhood evidence, an exact
whole-IFC literal strength-class source scan, and accepted v3.1 real
ÖKOBAUDAT source-admission evidence. It never guesses concrete grade.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ENGINE_NAME = "RegenExcalibur ProofGrid Real Model Environmental Source Suitability Decision"
ENGINE_VERSION = "3.2.0"
VERDICT = "REAL_MODEL_ENVIRONMENTAL_SOURCE_SUITABILITY_REVIEW_VERIFIABLE"
DECISION = "SUITABILITY_UNRESOLVED_MISSING_SOURCE_SEMANTICS"
ZERO = "0" * 64
CANON = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"

EXPECTED = {
    "ifc_source_sha256": "19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb",
    "candidate_step_id": 9730,
    "candidate_global_id": "3BmeJtEDj3AQO77Os2w7Ny",
    "material_relationship_step_id": 271324,
    "material_step_id": 9711,
    "material_name": "Ortbeton - bewehrt",
    "net_volume_step_id": 9737,
    "net_volume_lexical": "0.365000000000004",
    "candidate_probe_content_sha256": "341047be2d07ecb70f0a82a34b19992fe78ee3e0ae24cd90172f2f789556682c",
    "candidate_probe_file_sha256": "a3b48f0083b1c9b1382fe1d9386b01d3e2c171222f33cfef6c133fb44429d869",
    "model_scan_content_sha256": "665c520984077730417aeac9513e04eb2f95f87259a1a45f3c0a631c24a115a0",
    "model_scan_file_sha256": "edd9af95b1ab22a8002b8e9f9ab8c9f0854719ded372fa7667b015c289c68684",
    "v31_record_content_sha256": "b8518809e54d20438362f0accc0c2e64684fb20a8110d9d821251557e97a0135",
    "v31_record_file_sha256": "d32cc006b92157853d82e762d5064f81d17833494368cf463eb92f3102b10f2f",
    "v31_receipt_sha256": "3e00fd5a26b2aefb13b8abdca9bbb2d4b52edf6b5ada75c83bfb814ed8ca83b0",
    "v31_receipt_file_sha256": "d19ab62b32afd9df2a0d2d6ccfc1fc9aab1bf6272ad02253495306c747d29d34",
    "v31_comparison_sha256": "c79c211811fe8440d0477ce9eeada16bddb6e378588a5a81ffd2d68aa52fdb07",
    "v31_comparison_file_sha256": "21f40088d4950e7f53adb36e453b1f7647685adce1f853c21337b2a352c4cfdf",
    "environmental_uuid": "8347f9a7-f4ec-4a36-a266-a0281f5fd16d",
    "environmental_version": "00.02.000",
    "environmental_process_sha256": "18951c19002314adb6213d05783f8075553102a1bc57e22950d941a4804e445d",
    "environmental_reference_quantity": "1",
    "environmental_reference_unit": "m3",
    "environmental_gwp_value_decimal": "181",
}


class SuitabilityError(ValueError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SuitabilityError(msg)


def cbytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pbytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    require(isinstance(obj, dict), f"expected JSON object: {path}")
    return obj, raw


def verify_integrity_without_field(record: dict[str, Any], label: str, expected: str) -> None:
    integ = record.get("integrity")
    require(isinstance(integ, dict), f"{label} missing integrity")
    require(integ.get("content_sha256") == expected, f"{label} accepted content SHA mismatch")
    shadow = copy.deepcopy(record)
    shadow.pop("integrity", None)
    require(sha(cbytes(shadow)) == expected, f"{label} canonical content digest mismatch")


def verify_integrity_zeroed(record: dict[str, Any], label: str, expected: str) -> None:
    integ = record.get("integrity")
    require(isinstance(integ, dict), f"{label} missing integrity")
    require(integ.get("content_sha256") == expected, f"{label} accepted content SHA mismatch")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO
    require(sha(cbytes(shadow)) == expected, f"{label} canonical content digest mismatch")


def verify_receipt_digest(receipt: dict[str, Any], field: str, expected: str, label: str) -> None:
    require(receipt.get(field) == expected, f"{label} accepted digest mismatch")
    shadow = copy.deepcopy(receipt)
    shadow.pop(field, None)
    require(sha(cbytes(shadow)) == expected, f"{label} canonical digest mismatch")


def verify_probe(probe: dict[str, Any], raw: bytes) -> None:
    require(sha(raw) == EXPECTED["candidate_probe_file_sha256"], "candidate probe file identity mismatch")
    verify_integrity_without_field(probe, "candidate probe", EXPECTED["candidate_probe_content_sha256"])
    require(probe.get("verdict") == "REAL_MODEL_ENVIRONMENTAL_SOURCE_SUITABILITY_EVIDENCE_PROBE_VERIFIABLE", "wrong candidate probe verdict")
    candidate = probe.get("candidate", {})
    require(candidate.get("step_id") == EXPECTED["candidate_step_id"], "candidate STEP ID drift")
    require(candidate.get("global_id") == EXPECTED["candidate_global_id"], "candidate GlobalId drift")
    mats = candidate.get("material_associations", [])
    require(any(
        m.get("relationship_step_id") == EXPECTED["material_relationship_step_id"]
        and m.get("relating_material_step_id") == EXPECTED["material_step_id"]
        and m.get("material_attributes", {}).get("Name") == EXPECTED["material_name"]
        for m in mats
    ), "candidate material association drift")
    q = candidate.get("net_volume", {})
    require(q.get("quantity_step_id") == EXPECTED["net_volume_step_id"], "candidate NetVolume STEP drift")
    require(q.get("quantity_lexical") == EXPECTED["net_volume_lexical"], "candidate NetVolume lexical drift")
    require(q.get("source_token_is_authority") is True and q.get("parser_numeric_value_is_authority") is False, "candidate quantity authority drift")
    require(q.get("unit_type") == "VOLUMEUNIT" and q.get("unit_name") == "CUBIC_METRE" and q.get("unit_prefix") is None, "candidate volume unit drift")
    strength = probe.get("strength_class_evidence", {})
    require(strength.get("c25_30_present") is False and strength.get("c30_37_present") is False, "candidate strength-class evidence changed")
    require(strength.get("literal_strength_class_matches") == {"C25/30": [], "C30/37": []}, "candidate literal strength matches changed")
    require(strength.get("strength_class_inference_from_stb_or_material_name_allowed") is False, "candidate strength inference promotion rejected")
    auth = probe.get("authority_boundaries", {})
    require(auth.get("environmental_mapping_performed") is False and auth.get("impact_calculation_performed") is False, "candidate probe mapping/calculation promotion rejected")


def verify_scan(scan: dict[str, Any], raw: bytes) -> None:
    require(sha(raw) == EXPECTED["model_scan_file_sha256"], "model-wide scan file identity mismatch")
    verify_integrity_without_field(scan, "model-wide source scan", EXPECTED["model_scan_content_sha256"])
    require(scan.get("verdict") == "REAL_IFC_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_VERIFIABLE", "wrong model-wide scan verdict")
    source = scan.get("source", {})
    require(source.get("sha256") == EXPECTED["ifc_source_sha256"], "model-wide scan IFC SHA mismatch")
    require(source.get("file_bytes") == 9022255, "model-wide scan IFC byte size mismatch")
    require(scan.get("source_occurrence_count") == 0 and scan.get("occurrences") == [], "literal concrete-strength tokens unexpectedly present")
    require(scan.get("literal_strength_classes") == [], "model-wide strength-class list must be empty")
    require(scan.get("target_classes") == {"C25/30_present": False, "C30/37_present": False}, "model-wide target strength-class state changed")
    method = scan.get("method", {})
    require(method.get("scope") == "ENTIRE_NATIVE_IFC_UTF8_SOURCE_TEXT", "model-wide scan scope mismatch")
    require(method.get("helper_api_inference_used") is False and method.get("inference_from_stb_or_material_names") is False and method.get("fuzzy_matching") is False, "model-wide inference promotion rejected")


def verify_v31(record: dict[str, Any], record_raw: bytes, receipt: dict[str, Any], receipt_raw: bytes, comparison: dict[str, Any], comparison_raw: bytes) -> None:
    require(sha(record_raw) == EXPECTED["v31_record_file_sha256"], "v3.1 record file identity mismatch")
    verify_integrity_zeroed(record, "v3.1 admission", EXPECTED["v31_record_content_sha256"])
    require(record.get("verdict") == "REAL_ENVIRONMENTAL_SOURCE_ADMISSION_VERIFIABLE", "wrong v3.1 admission verdict")
    source = record.get("source", {})
    require(source.get("dataset_uuid") == EXPECTED["environmental_uuid"] and source.get("dataset_version") == EXPECTED["environmental_version"], "v3.1 environmental identity mismatch")
    require(source.get("target_process_sha256") == EXPECTED["environmental_process_sha256"], "v3.1 target process drift")
    adm = record.get("admission", {})
    require(adm.get("admitted_for_normalization") is True and adm.get("mapping_eligible") is False and adm.get("impact_calculation_allowed_by_this_record") is False, "v3.1 admission boundary drift")
    require(adm.get("source_internal_naming_discrepancy_present") is True, "v3.1 source naming discrepancy unexpectedly absent")
    ref = record.get("dataset_identity", {}).get("declared_reference", {})
    require(ref.get("quantity_decimal") == EXPECTED["environmental_reference_quantity"] and ref.get("declared_unit_from_process_description") == EXPECTED["environmental_reference_unit"], "v3.1 declared reference drift")
    require(ref.get("source_internal_name_differs_from_process_title") is True, "v3.1 reference-flow/title discrepancy changed")
    indicator = record.get("dataset_identity", {}).get("indicator_control", {})
    require(indicator.get("value_decimal") == EXPECTED["environmental_gwp_value_decimal"] and indicator.get("module") == "A1-A3" and indicator.get("scenario") is None, "v3.1 indicator control drift")

    require(sha(receipt_raw) == EXPECTED["v31_receipt_file_sha256"], "v3.1 receipt file identity mismatch")
    verify_receipt_digest(receipt, "receipt_sha256", EXPECTED["v31_receipt_sha256"], "v3.1 receipt")
    require(receipt.get("record_content_sha256") == EXPECTED["v31_record_content_sha256"], "v3.1 receipt/record binding mismatch")

    require(sha(comparison_raw) == EXPECTED["v31_comparison_file_sha256"], "v3.1 comparison file identity mismatch")
    verify_receipt_digest(comparison, "comparison_receipt_sha256", EXPECTED["v31_comparison_sha256"], "v3.1 comparison")
    require(comparison.get("byte_identical") is True and comparison.get("independent_runner_count") == 2, "v3.1 independent reproduction missing")
    require(comparison.get("mapping_eligible") is False and comparison.get("certified") is False, "v3.1 comparison authority promotion rejected")


def validate_decision(record: dict[str, Any]) -> None:
    require(record.get("verdict") == VERDICT, "wrong v3.2 decision verdict")
    require(record.get("decision") == DECISION, "wrong v3.2 suitability decision")
    unit = record.get("reference_basis_compatibility", {})
    require(unit.get("ifc_quantity_unit") == "m3" and unit.get("environmental_reference_unit") == "m3", "reference unit mismatch")
    require(unit.get("unit_compatible_without_conversion") is True and unit.get("unit_conversion_performed") is False, "reference-unit authority mismatch")
    reasons = record.get("decision_reasons", [])
    require(reasons == [
        "IFC_CANDIDATE_STRENGTH_CLASS_NOT_ENCODED",
        "MODEL_WIDE_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_ZERO",
        "ENVIRONMENTAL_SOURCE_INTERNAL_C25_30_VS_C30_37_NAMING_DISCREPANCY",
        "EXPLICIT_MATERIAL_SPECIFICATION_EVIDENCE_REQUIRED_BEFORE_MAPPING",
    ], "decision reason set mismatch")
    auth = record.get("authority_boundaries", {})
    for key in (
        "mapping_authorized", "environmental_mapping_performed", "impact_calculation_permitted",
        "impact_calculation_performed", "scientific_suitability_confirmed",
        "professional_review_performed", "regulator_acceptance_implied", "certified",
    ):
        require(auth.get(key) is False, f"authority promotion rejected: {key}")
    require(record.get("missing_semantics_are_zero") is False, "missing semantics cannot become zero")
    require(record.get("fuzzy_or_name_only_equivalence_allowed") is False, "fuzzy/name-only mapping promotion rejected")


def build(probe: dict[str, Any], probe_raw: bytes, scan: dict[str, Any], scan_raw: bytes, v31: dict[str, Any], v31_raw: bytes, v31_receipt: dict[str, Any], v31_receipt_raw: bytes, v31_comparison: dict[str, Any], v31_comparison_raw: bytes) -> dict[str, Any]:
    verify_probe(probe, probe_raw)
    verify_scan(scan, scan_raw)
    verify_v31(v31, v31_raw, v31_receipt, v31_receipt_raw, v31_comparison, v31_comparison_raw)
    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridRealModelEnvironmentalSourceSuitabilityDecision",
        "verdict": VERDICT,
        "decision": DECISION,
        "candidate": {
            "ifc_source_sha256": EXPECTED["ifc_source_sha256"],
            "step_id": EXPECTED["candidate_step_id"],
            "global_id": EXPECTED["candidate_global_id"],
            "material_relationship_step_id": EXPECTED["material_relationship_step_id"],
            "material_step_id": EXPECTED["material_step_id"],
            "material_name": EXPECTED["material_name"],
            "net_volume_step_id": EXPECTED["net_volume_step_id"],
            "net_volume_decimal": EXPECTED["net_volume_lexical"],
            "net_volume_unit": "m3",
        },
        "environmental_source": {
            "provider": "ÖKOBAUDAT",
            "dataset_uuid": EXPECTED["environmental_uuid"],
            "dataset_version": EXPECTED["environmental_version"],
            "process_sha256": EXPECTED["environmental_process_sha256"],
            "reference_quantity_decimal": EXPECTED["environmental_reference_quantity"],
            "reference_unit": EXPECTED["environmental_reference_unit"],
            "gwp_total_a1_a3_decimal": EXPECTED["environmental_gwp_value_decimal"],
            "process_title_class": "C25/30",
            "reference_flow_short_description_class": "C30/37",
            "source_internal_naming_discrepancy_present": True,
        },
        "reference_basis_compatibility": {
            "ifc_quantity_unit": "m3",
            "environmental_reference_unit": "m3",
            "unit_compatible_without_conversion": True,
            "unit_conversion_performed": False,
            "quantity_scaling_arithmetic_performed": False,
        },
        "semantic_evidence": {
            "candidate_c25_30_present": False,
            "candidate_c30_37_present": False,
            "entire_ifc_literal_strength_class_occurrence_count": 0,
            "entire_ifc_literal_strength_classes": [],
            "strength_class_inferred_from_stb_or_ortbeton": False,
        },
        "decision_reasons": [
            "IFC_CANDIDATE_STRENGTH_CLASS_NOT_ENCODED",
            "MODEL_WIDE_LITERAL_CONCRETE_STRENGTH_CLASS_SCAN_ZERO",
            "ENVIRONMENTAL_SOURCE_INTERNAL_C25_30_VS_C30_37_NAMING_DISCREPANCY",
            "EXPLICIT_MATERIAL_SPECIFICATION_EVIDENCE_REQUIRED_BEFORE_MAPPING",
        ],
        "parent_evidence": {
            "candidate_probe_content_sha256": EXPECTED["candidate_probe_content_sha256"],
            "candidate_probe_file_sha256": EXPECTED["candidate_probe_file_sha256"],
            "model_scan_content_sha256": EXPECTED["model_scan_content_sha256"],
            "model_scan_file_sha256": EXPECTED["model_scan_file_sha256"],
            "v31_admission_content_sha256": EXPECTED["v31_record_content_sha256"],
            "v31_admission_receipt_sha256": EXPECTED["v31_receipt_sha256"],
            "v31_independent_comparison_receipt_sha256": EXPECTED["v31_comparison_sha256"],
        },
        "authority_boundaries": {
            "mapping_authorized": False,
            "environmental_mapping_performed": False,
            "impact_calculation_permitted": False,
            "impact_calculation_performed": False,
            "scientific_suitability_confirmed": False,
            "professional_review_performed": False,
            "regulator_acceptance_implied": False,
            "certified": False,
        },
        "missing_semantics_are_zero": False,
        "fuzzy_or_name_only_equivalence_allowed": False,
        "next_evidence_requirement": {
            "type": "AUTHORITATIVE_MATERIAL_SPECIFICATION_OR_EXACT_SOURCE_ARTIFACT",
            "must_bind_candidate": True,
            "must_resolve_concrete_product_or_strength_class": True,
            "mapping_may_resume_only_after_reviewed_evidence": True,
        },
        "integrity": {
            "content_sha256": ZERO,
            "canonicalization": CANON,
            "signature": None,
        },
    }
    record["integrity"]["content_sha256"] = sha(cbytes(record))
    validate_decision(record)
    return record


def make_receipt(record: dict[str, Any], raw: bytes) -> dict[str, Any]:
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "decision": DECISION,
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha(raw),
        "ifc_source_sha256": EXPECTED["ifc_source_sha256"],
        "candidate_step_id": EXPECTED["candidate_step_id"],
        "candidate_global_id": EXPECTED["candidate_global_id"],
        "candidate_probe_content_sha256": EXPECTED["candidate_probe_content_sha256"],
        "model_scan_content_sha256": EXPECTED["model_scan_content_sha256"],
        "v31_admission_content_sha256": EXPECTED["v31_record_content_sha256"],
        "entire_ifc_literal_strength_class_occurrence_count": 0,
        "unit_compatible_without_conversion": True,
        "mapping_authorized": False,
        "impact_calculation_performed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha(cbytes(receipt))
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate-probe", type=Path, required=True)
    p.add_argument("--model-scan", type=Path, required=True)
    p.add_argument("--v31-record", type=Path, required=True)
    p.add_argument("--v31-receipt", type=Path, required=True)
    p.add_argument("--v31-comparison", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        probe, probe_raw = load(a.candidate_probe)
        scan, scan_raw = load(a.model_scan)
        v31, v31_raw = load(a.v31_record)
        v31r, v31r_raw = load(a.v31_receipt)
        v31c, v31c_raw = load(a.v31_comparison)
        record = build(probe, probe_raw, scan, scan_raw, v31, v31_raw, v31r, v31r_raw, v31c, v31c_raw)
        a.output_dir.mkdir(parents=True, exist_ok=True)
        raw = pbytes(record)
        (a.output_dir / "real-model-environmental-source-suitability-decision.json").write_bytes(raw)
        receipt = make_receipt(record, raw)
        (a.output_dir / "real-model-environmental-source-suitability-decision-receipt.json").write_bytes(pbytes(receipt))
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"DECISION: {DECISION}")
    print("MAPPING_AUTHORIZED=false")
    print("IMPACT_CALCULATION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
