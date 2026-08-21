#!/usr/bin/env python3
"""ProofGrid v1.1 deterministic declared environmental-indicator extractor.

The first accepted scope is intentionally narrow: EN 15804+A2 EF3.0 GWP-total
only, using the exact indicator/unit/structure identities frozen by the v1.1
research gate. Values are emitted only when they are explicitly present as
EPD/2013 ``amount`` elements under the matching ILCD LCIAResult.

This module does not calculate, aggregate, interpolate, convert, or scientifically
validate environmental values. Missing modules are not zero. LCIAResult
``meanAmount`` is retained only as ignored metadata and is never substituted for
a lifecycle-module declaration.
"""

from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from jsonschema import Draft202012Validator, SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import environmental_admission as admission  # noqa: E402
from reference import environmental_source_identity as source_identity  # noqa: E402

ENGINE_NAME = "RegenExcalibur ProofGrid Declared Environmental Indicator Extractor"
ENGINE_VERSION = "1.1.0"
VERDICT = "DECLARED_ENVIRONMENTAL_INDICATORS_EXTRACTED_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO_DIGEST = "0" * 64

FROZEN_MAP_PATH = ROOT / "conformance" / "indicator-extraction-v11" / "frozen-indicator-map.json"
SCHEMA_PATH = ROOT / "schemas" / "declared-environmental-indicators.schema.json"

EXPECTED_RESEARCH_FREEZE = "2345047d8e3888ccda965754728e939eed61851b28945033355d1ddae682941f"
EXPECTED_EF30_SHA256 = "87941c696b955428d502a28acafedbedfcb1414d0b5e55d38c9d18072d65893e"
GWP_TOTAL_UUID = "6a37f984-a4b3-458a-a20a-64418c145fa2"

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
EPD_2013_NS = "http://www.iai.kit.edu/EPD/2013"
XML_NS = "http://www.w3.org/XML/1998/namespace"


class ExtractionError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExtractionError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"invalid JSON in {path}: {exc}") from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def validate_schema(instance: dict[str, Any]) -> None:
    schema = load_json(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ExtractionError(f"invalid declared-indicator schema: {exc.message}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda err: list(err.path))
    if errors:
        preview = "; ".join(f"{list(err.path)}: {err.message}" for err in errors[:8])
        if len(errors) > 8:
            preview += f"; +{len(errors) - 8} more"
        raise ExtractionError(f"declared-indicator output failed schema validation: {preview}")


def canonical_decimal(lexical: str) -> str:
    try:
        value = Decimal(lexical)
    except (InvalidOperation, ValueError) as exc:
        raise ExtractionError(f"declared environmental amount is not numeric: {lexical!r}") from exc
    if not value.is_finite():
        raise ExtractionError(f"declared environmental amount must be finite: {lexical!r}")
    if value == 0:
        return "0"
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    if result == "-0":
        result = "0"
    return result


def verify_canonical_source_record(record: dict[str, Any]) -> None:
    try:
        source_identity.validate_schema(record)
    except Exception as exc:
        raise ExtractionError(f"canonical source record schema validation failed: {exc}") from exc
    require(record.get("verdict") == source_identity.VERDICT, "wrong canonical source verdict")
    require(record.get("certified") is False, "canonical source record must remain certified=false")
    require(record.get("impact_values_normalized") is False, "v1.0 source identity may not already claim impact-value normalization")
    require(record.get("scientific_validation_performed") is False, "canonical source may not claim scientific validation")
    require(record.get("professional_review_performed") is False, "canonical source may not claim professional review")
    require(
        record.get("rxep_bridge", {}).get("review_state_elevation_permitted") is False,
        "canonical source may not elevate RXEP review state",
    )
    integrity = record.get("integrity", {})
    expected = integrity.get("content_sha256")
    require(isinstance(expected, str) and len(expected) == 64, "canonical source integrity digest missing")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    actual = sha256_bytes(canonical_json_bytes(shadow))
    require(actual == expected, f"canonical source integrity mismatch: expected {expected}, got {actual}")


def load_frozen_map(path: Path = FROZEN_MAP_PATH) -> tuple[dict[str, Any], str]:
    data = load_json(path)
    require(data.get("schema_version") == "1.0", "unsupported frozen indicator map schema")
    require(
        data.get("research_freeze", {}).get("receipt_sha256") == EXPECTED_RESEARCH_FREEZE,
        "frozen map does not bind the accepted v1.1 research freeze",
    )
    require(
        data.get("upstreams", {}).get("ef30_catalogue_sha256") == EXPECTED_EF30_SHA256,
        "frozen map EF3.0 catalogue digest mismatch",
    )
    require(data.get("structure", {}).get("unscoped_mean_amount_extracted") is False, "frozen map may not authorize meanAmount extraction")
    return data, sha256_file(path)


def safe_zip_name(name: str) -> PurePosixPath:
    try:
        return admission.safe_zip_name(name)
    except admission.AdmissionError as exc:
        raise ExtractionError(str(exc)) from exc


def parse_process(raw: bytes, label: str) -> ET.Element:
    try:
        root = admission.safe_xml_root(raw, label)
    except admission.AdmissionError as exc:
        raise ExtractionError(str(exc)) from exc
    require(root.tag == f"{{{PROCESS_NS}}}processDataSet", f"{label} is not an ILCD processDataSet")
    return root


def load_process_bytes(source_path: Path, container: str) -> tuple[bytes, str]:
    source_path = source_path.resolve()
    if container == "XML":
        return source_path.read_bytes(), source_path.name
    require(container == "ZIP", f"unsupported canonical source container: {container}")
    rows: list[tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(source_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                path = safe_zip_name(info.filename)
                name = path.as_posix()
                if name.startswith("ILCD/processes/") and name.lower().endswith(".xml"):
                    rows.append((name, zf.read(info)))
    except zipfile.BadZipFile as exc:
        raise ExtractionError(f"invalid ZIP source: {source_path}") from exc
    require(len(rows) == 1, f"single-record extraction requires exactly one ILCD process dataset; found {len(rows)}")
    return rows[0][1], rows[0][0]


def process_uuid(root: ET.Element) -> str:
    info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    require(info is not None, "processInformation/dataSetInformation missing")
    node = info.find(f"{{{COMMON_NS}}}UUID")
    require(node is not None and bool((node.text or "").strip()), "process dataset UUID missing")
    return (node.text or "").strip()


def scenario_registry(root: ET.Element) -> dict[str, dict[str, Any]]:
    info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    if info is None:
        return {}
    other = info.find(f"{{{COMMON_NS}}}other")
    if other is None:
        return {}
    scenarios = other.find(f"{{{EPD_2013_NS}}}scenarios")
    if scenarios is None:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for node in scenarios.findall(f"{{{EPD_2013_NS}}}scenario"):
        name = (node.attrib.get("name") or "").strip()
        require(bool(name), "declared scenario is missing a name")
        require(name not in result, f"duplicate declared scenario name: {name}")
        default_lexical = (node.attrib.get("default") or "false").lower()
        require(default_lexical in {"true", "false"}, f"invalid scenario default flag for {name}: {default_lexical}")
        result[name] = {
            "name": name,
            "group": (node.attrib.get("group") or "").strip() or None,
            "default": default_lexical == "true",
        }
    return result


def selected_lcia_result(root: ET.Element, indicator_uuid: str) -> tuple[ET.Element, ET.Element, int]:
    results_root = root.find(f"{{{PROCESS_NS}}}LCIAResults")
    require(results_root is not None, "process dataset has no LCIAResults")
    matches: list[tuple[ET.Element, ET.Element, int]] = []
    for ordinal, result in enumerate(results_root.findall(f"{{{PROCESS_NS}}}LCIAResult"), start=1):
        refs = result.findall(f"{{{PROCESS_NS}}}referenceToLCIAMethodDataSet")
        for ref in refs:
            if ref.attrib.get("refObjectId") == indicator_uuid:
                matches.append((result, ref, ordinal))
    require(len(matches) == 1, f"expected exactly one LCIAResult for indicator {indicator_uuid}; found {len(matches)}")
    return matches[0]


def extract_record(
    source_path: Path,
    canonical_source: dict[str, Any],
    *,
    indicator_uuid: str = GWP_TOTAL_UUID,
    frozen_map_path: Path = FROZEN_MAP_PATH,
) -> dict[str, Any]:
    verify_canonical_source_record(canonical_source)
    frozen_map, frozen_map_sha = load_frozen_map(frozen_map_path)
    indicators = frozen_map.get("indicators", {})
    require(indicator_uuid in indicators, f"indicator UUID is not admitted by the frozen v1.1 map: {indicator_uuid}")
    spec = indicators[indicator_uuid]
    require(spec.get("implicit_unit_conversion_permitted") is False, "frozen indicator spec may not permit implicit unit conversion")
    require(spec.get("reference_unit_mean_value_decimal") == "1", "frozen indicator reference unit is not identity conversion")

    source_path = source_path.resolve()
    require(source_path.is_file(), f"source file not found: {source_path}")
    actual_source_sha = sha256_file(source_path)
    expected_source_sha = canonical_source["source"]["sha256"]
    require(actual_source_sha == expected_source_sha, f"source SHA-256 mismatch: expected {expected_source_sha}, got {actual_source_sha}")

    raw, process_label = load_process_bytes(source_path, canonical_source["source"]["container"])
    process_sha = sha256_bytes(raw)
    require(process_sha == canonical_source["identity"]["process_xml_sha256"], "process XML SHA-256 does not match canonical v1.0 source identity")
    root = parse_process(raw, process_label)
    version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
    require(version == canonical_source["source"]["format_version"], "process ILCD+EPD version does not match canonical source identity")
    require(version in {"1.2", "1.3"}, f"unsupported ILCD+EPD version: {version}")
    uuid = process_uuid(root)
    require(uuid == canonical_source["identity"]["process_dataset_uuid"], "process dataset UUID does not match canonical source identity")

    result, indicator_ref, result_ordinal = selected_lcia_result(root, indicator_uuid)
    source_reference_version = (indicator_ref.attrib.get("version") or "").strip() or None
    if source_reference_version is not None:
        require(
            source_reference_version == spec["catalogue_version"],
            f"source indicator version {source_reference_version} does not match frozen catalogue version {spec['catalogue_version']}",
        )

    other = result.find(f"{{{COMMON_NS}}}other")
    require(other is not None, "selected LCIAResult has no common:other declared-value container")
    unit_refs = other.findall(f"{{{EPD_2013_NS}}}referenceToUnitGroupDataSet")
    require(len(unit_refs) == 1, f"selected LCIAResult must contain exactly one EPD unit-group reference; found {len(unit_refs)}")
    declared_unit_group_uuid = unit_refs[0].attrib.get("refObjectId")
    require(
        declared_unit_group_uuid == spec["unit_group_uuid"],
        f"declared unit-group UUID mismatch: expected {spec['unit_group_uuid']}, got {declared_unit_group_uuid}",
    )

    supported_modules = set(frozen_map.get("supported_modules", []))
    scenarios = scenario_registry(root)
    amounts = other.findall(f"{{{EPD_2013_NS}}}amount")
    require(bool(amounts), "selected LCIAResult has no declared EPD module amount values")

    seen: set[tuple[str, str | None]] = set()
    rows: list[dict[str, Any]] = []
    for amount_ordinal, amount in enumerate(amounts, start=1):
        module = (amount.attrib.get("module") or "").strip()
        require(module in supported_modules, f"unsupported or missing lifecycle module: {module!r}")
        scenario_name = (amount.attrib.get("scenario") or "").strip() or None
        scenario: dict[str, Any] | None = None
        if scenario_name is not None:
            require(scenario_name in scenarios, f"module amount references undeclared scenario: {scenario_name}")
            scenario = scenarios[scenario_name]
        key = (module, scenario_name)
        require(key not in seen, f"duplicate/conflicting declared amount identity for module={module}, scenario={scenario_name}")
        seen.add(key)

        lexical = (amount.text or "").strip()
        require(bool(lexical), f"declared amount is empty for module={module}, scenario={scenario_name}")
        decimal_value = canonical_decimal(lexical)
        rows.append(
            {
                "indicator_uuid": indicator_uuid,
                "source_reference_version": source_reference_version,
                "module": module,
                "scenario": scenario,
                "value_lexical": lexical,
                "value_decimal": decimal_value,
                "value_origin": "DECLARED_IN_SOURCE",
                "canonical_unit": spec["canonical_unit"],
                "unit_group_uuid": spec["unit_group_uuid"],
                "reference_unit_internal_id": spec["reference_unit_internal_id"],
                "reference_unit_name": spec["reference_unit_name"],
                "reference_unit_mean_value_decimal": spec["reference_unit_mean_value_decimal"],
                "calculated": False,
                "unit_conversion_performed": False,
                "source_location": {
                    "lcia_result_ordinal": result_ordinal,
                    "amount_ordinal": amount_ordinal,
                    "path": f"processDataSet/LCIAResults/LCIAResult[{result_ordinal}]/other/amount[{amount_ordinal}]",
                },
            }
        )

    mean_node = result.find(f"{{{PROCESS_NS}}}meanAmount")
    mean_lexical = (mean_node.text or "").strip() if mean_node is not None else None
    if mean_lexical == "":
        mean_lexical = None

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredEnvironmentalIndicators",
        "verdict": VERDICT,
        "certified": False,
        "calculated": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "source": {
            "sha256": actual_source_sha,
            "process_xml_sha256": process_sha,
            "process_dataset_uuid": uuid,
            "format_version": version,
            "container": canonical_source["source"]["container"],
        },
        "canonical_source": {
            "record_id": canonical_source["id"],
            "content_sha256": canonical_source["integrity"]["content_sha256"],
            "admission_receipt_sha256": canonical_source["admission"]["receipt_sha256"],
            "verdict": canonical_source["verdict"],
        },
        "frozen_map": {
            "sha256": frozen_map_sha,
            "research_freeze_receipt_sha256": frozen_map["research_freeze"]["receipt_sha256"],
            "catalogue_sha256": frozen_map["upstreams"]["ef30_catalogue_sha256"],
        },
        "indicator_scope": {
            "indicator_uuid": indicator_uuid,
            "code": spec["code"],
            "catalogue": spec["catalogue"],
            "catalogue_version": spec["catalogue_version"],
            "canonical_unit": spec["canonical_unit"],
            "unit_group_uuid": spec["unit_group_uuid"],
        },
        "ignored_unscoped_mean_amount": {
            "extracted": False,
            "lexical_value": mean_lexical,
            "reason": "LCIAResult meanAmount is unscoped by lifecycle module/scenario and is not a v1.1 declared module value.",
        },
        "rows": rows,
        "missing_value_policy": {
            "missing_modules_are_zero": False,
            "aggregation_performed": False,
        },
        "limitations": [
            "v1.1 extracts only values explicitly declared as EPD/2013 amount elements for the exact frozen GWP-total identity.",
            "No missing lifecycle module is converted to zero; absent values remain absent.",
            "No unit conversion or lifecycle-module aggregation is performed.",
            "Declared-value extraction does not establish scientific validity, product representativeness, professional LCA review, programme-operator/BBSR approval, provider authority, code/engineering/architectural approval, regulatory approval, or certification.",
        ],
        "integrity": {
            "content_sha256": ZERO_DIGEST,
            "canonicalization": CANONICALIZATION,
        },
    }
    digest = sha256_bytes(canonical_json_bytes(record))
    record["integrity"]["content_sha256"] = digest
    validate_schema(record)
    return record


def build_receipt(record: dict[str, Any], record_file_bytes: bytes) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "certified": False,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "source_sha256": record["source"]["sha256"],
        "process_xml_sha256": record["source"]["process_xml_sha256"],
        "process_dataset_uuid": record["source"]["process_dataset_uuid"],
        "format_version": record["source"]["format_version"],
        "canonical_source_content_sha256": record["canonical_source"]["content_sha256"],
        "admission_receipt_sha256": record["canonical_source"]["admission_receipt_sha256"],
        "frozen_map_sha256": record["frozen_map"]["sha256"],
        "research_freeze_receipt_sha256": record["frozen_map"]["research_freeze_receipt_sha256"],
        "indicator_uuid": record["indicator_scope"]["indicator_uuid"],
        "indicator_code": record["indicator_scope"]["code"],
        "row_count": len(record["rows"]),
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_file_bytes),
        "calculated": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified_state": "NOT_EVALUATED",
        "limitations": list(record["limitations"]),
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def extract(
    source_path: Path,
    *,
    canonical_source_path: Path,
    output_dir: Path,
    indicator_uuid: str = GWP_TOTAL_UUID,
) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_source = load_json(canonical_source_path)
    record = extract_record(source_path, canonical_source, indicator_uuid=indicator_uuid)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "declared-environmental-indicators.json"
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)
    receipt = build_receipt(record, record_bytes)
    receipt_path = output_dir / "extraction-receipt.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    return record, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofGrid v1.1 admission-bound declared environmental-indicator extractor")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--canonical-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--indicator-uuid", default=GWP_TOTAL_UUID)
    args = parser.parse_args(argv)
    try:
        record, receipt = extract(
            args.source,
            canonical_source_path=args.canonical_source,
            output_dir=args.output_dir,
            indicator_uuid=args.indicator_uuid,
        )
    except (ExtractionError, admission.AdmissionError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(f"RESULT: {receipt['verdict']}")
    print(f"INDICATOR: {record['indicator_scope']['code']} ({record['indicator_scope']['indicator_uuid']})")
    print(f"DECLARED ROWS: {len(record['rows'])}")
    print("CALCULATED: false")
    print("UNIT CONVERSION: false")
    print("SCIENTIFIC VALIDATION: false")
    print("PROFESSIONAL REVIEW: false")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
