#!/usr/bin/env python3
"""ProofGrid v1.3 research probe for the declared ILCD quantitative-reference chain.

The parsing helpers are intentionally generic: they extract exact ILCD identity
links without assuming the pinned wood-panel UUIDs. The research `main()` then
applies fixture-specific assertions to freeze the known-answer chain for the
pinned public InData examples. This separation lets production code reuse the
same structural parser without turning a research fixture identity into a
universal parser rule.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from typing import Any

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
FLOW_NS = "http://lca.jrc.it/ILCD/Flow"
FLOW_PROPERTY_NS = "http://lca.jrc.it/ILCD/FlowProperty"
UNIT_GROUP_NS = "http://lca.jrc.it/ILCD/UnitGroup"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
XML_NS = "http://www.w3.org/XML/1998/namespace"

EXPECTED_V12_COMMIT = "b7233bd2dd5435a6b5973505ffa212cd03d23468"
EXPECTED_V13_COMMIT = "7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa"
EXPECTED_MASTER_COMMIT = "32117b6a70d6c486344247a429449755a2c7eab4"

PROCESS_UUID = "57a4ae65-d305-421e-b21f-a3f0c35b8abe"
FLOW_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
FLOW_PROPERTY_UUID = "93a60a56-a3c8-11da-a746-0800200b9a66"
UNIT_GROUP_UUID = "ad38d542-3fe9-439d-9b95-2f5f7752acaf"

V12_PROCESS = Path("sample_data/processes/57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")
V13_PROCESS = Path("sample_data/processes/EPDv1.3_example_57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")
FLOW_PATH = Path("sample_data/flows/a7432abd-0881-4977-a817-f8aaf627fb91.xml")
FLOW_PROPERTY_PATH = Path("master_data/units/flowproperties/Mass_93a60a56-a3c8-11da-a746-0800200b9a66.xml")
UNIT_GROUP_PATH = Path("master_data/units/unitgroups/Masseneinheit_ad38d542-3fe9-439d-9b95-2f5f7752acaf.xml")


class ResearchError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_decimal(lexical: str, label: str) -> str:
    text = lexical.strip()
    require(bool(text), f"{label} is empty")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ResearchError(f"{label} is not a Decimal: {text!r}") from exc
    require(value.is_finite(), f"{label} must be finite")
    if value == 0:
        return "0"
    normalized = value.normalize()
    rendered = format(normalized, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def verify_repo(repo: Path, expected_commit: str) -> None:
    require((repo / ".git").exists(), f"not a git checkout: {repo}")
    actual = git(repo, "rev-parse", "HEAD")
    require(actual == expected_commit, f"commit mismatch for {repo}: expected {expected_commit}, got {actual}")


def file_evidence(repo: Path, relative: Path) -> dict[str, Any]:
    path = repo / relative
    require(path.is_file(), f"missing pinned file: {relative}")
    return {
        "path": relative.as_posix(),
        "git_blob_sha": git(repo, "hash-object", relative.as_posix()),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def first_text(parent: ET.Element, qname: str, label: str) -> str:
    node = parent.find(qname)
    require(node is not None and node.text is not None and node.text.strip() != "", f"missing {label}")
    return node.text.strip()


def dataset_version(root: ET.Element, namespace: str) -> str | None:
    node = root.find(f"{{{namespace}}}administrativeInformation/{{{namespace}}}publicationAndOwnership/{{{COMMON_NS}}}dataSetVersion")
    return node.text.strip() if node is not None and node.text else None


def common_uuid(root: ET.Element) -> str:
    node = root.find(f".//{{{COMMON_NS}}}UUID")
    require(node is not None and node.text and node.text.strip(), "dataset UUID missing")
    return node.text.strip()


def multilingual_names(root: ET.Element, namespace: str) -> list[dict[str, str | None]]:
    names: list[dict[str, str | None]] = []
    for node in root.findall(f".//{{{namespace}}}baseName"):
        if node.text and node.text.strip():
            names.append({"language": node.attrib.get(f"{{{XML_NS}}}lang"), "value": node.text.strip()})
    if not names:
        for node in root.findall(f".//{{{COMMON_NS}}}name"):
            if node.text and node.text.strip():
                names.append({"language": node.attrib.get(f"{{{XML_NS}}}lang"), "value": node.text.strip()})
    return names


def inspect_process(process_path: Path, expected_epd_version: str) -> dict[str, Any]:
    root = ET.parse(process_path).getroot()
    require(root.tag == f"{{{PROCESS_NS}}}processDataSet", "process root is not Process/processDataSet")
    require(root.attrib.get(f"{{{EPD_2019_NS}}}epd-version") == expected_epd_version, "unexpected ILCD+EPD version")
    process_uuid = common_uuid(root)

    quantitative = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}quantitativeReference")
    require(quantitative is not None, "process quantitativeReference missing")
    refs = [
        (node.text or "").strip()
        for node in quantitative.findall(f"{{{PROCESS_NS}}}referenceToReferenceFlow")
        if (node.text or "").strip()
    ]
    require(len(refs) == 1, f"expected exactly one process reference flow ID, got {refs}")
    internal_id = refs[0]

    exchanges = [
        node
        for node in root.findall(f"{{{PROCESS_NS}}}exchanges/{{{PROCESS_NS}}}exchange")
        if node.attrib.get("dataSetInternalID") == internal_id
    ]
    require(len(exchanges) == 1, f"reference exchange {internal_id} is missing or ambiguous")
    exchange = exchanges[0]
    flow_ref = exchange.find(f"{{{PROCESS_NS}}}referenceToFlowDataSet")
    require(flow_ref is not None, "reference exchange lacks referenceToFlowDataSet")
    product_flow_uuid = flow_ref.attrib.get("refObjectId")
    require(isinstance(product_flow_uuid, str) and bool(product_flow_uuid.strip()), "reference exchange product-flow UUID missing")
    amount_lexical = first_text(exchange, f"{{{PROCESS_NS}}}meanAmount", "process reference exchange meanAmount")

    return {
        "epd_version": expected_epd_version,
        "process_uuid": process_uuid,
        "quantitative_reference_type": quantitative.attrib.get("type"),
        "reference_exchange_internal_id": internal_id,
        "product_flow_uuid": product_flow_uuid.strip(),
        "product_flow_version": flow_ref.attrib.get("version"),
        "exchange_amount": {
            "lexical": amount_lexical,
            "decimal": canonical_decimal(amount_lexical, "process exchange meanAmount"),
        },
    }


def inspect_flow(flow_path: Path) -> dict[str, Any]:
    root = ET.parse(flow_path).getroot()
    require(root.tag == f"{{{FLOW_NS}}}flowDataSet", "flow root is not Flow/flowDataSet")
    flow_uuid = common_uuid(root)

    quantitative = root.find(f"{{{FLOW_NS}}}flowInformation/{{{FLOW_NS}}}quantitativeReference")
    require(quantitative is not None, "flow quantitativeReference missing")
    ref_id = first_text(quantitative, f"{{{FLOW_NS}}}referenceToReferenceFlowProperty", "reference flow-property internal ID")
    matches = [
        node
        for node in root.findall(f"{{{FLOW_NS}}}flowProperties/{{{FLOW_NS}}}flowProperty")
        if node.attrib.get("dataSetInternalID") == ref_id
    ]
    require(len(matches) == 1, f"reference flow property {ref_id} is missing or ambiguous")
    prop = matches[0]
    prop_ref = prop.find(f"{{{FLOW_NS}}}referenceToFlowPropertyDataSet")
    require(prop_ref is not None, "reference flow property lacks referenceToFlowPropertyDataSet")
    flow_property_uuid = prop_ref.attrib.get("refObjectId")
    require(isinstance(flow_property_uuid, str) and bool(flow_property_uuid.strip()), "reference flow-property UUID missing")
    mean_lexical = first_text(prop, f"{{{FLOW_NS}}}meanValue", "reference flow-property meanValue")

    return {
        "flow_uuid": flow_uuid,
        "flow_version": dataset_version(root, FLOW_NS),
        "names": multilingual_names(root, FLOW_NS),
        "reference_flow_property_internal_id": ref_id,
        "flow_property_uuid": flow_property_uuid.strip(),
        "flow_property_version": prop_ref.attrib.get("version"),
        "flow_property_mean": {
            "lexical": mean_lexical,
            "decimal": canonical_decimal(mean_lexical, "reference flow-property meanValue"),
        },
    }


def inspect_flow_property(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(root.tag == f"{{{FLOW_PROPERTY_NS}}}flowPropertyDataSet", "flow-property root mismatch")
    flow_property_uuid = common_uuid(root)
    ref = root.find(
        f"{{{FLOW_PROPERTY_NS}}}flowPropertiesInformation/{{{FLOW_PROPERTY_NS}}}quantitativeReference/"
        f"{{{FLOW_PROPERTY_NS}}}referenceToReferenceUnitGroup"
    )
    require(ref is not None, "flow-property reference unit group missing")
    unit_group_uuid = ref.attrib.get("refObjectId")
    require(isinstance(unit_group_uuid, str) and bool(unit_group_uuid.strip()), "flow-property reference unit-group UUID missing")
    return {
        "flow_property_uuid": flow_property_uuid,
        "flow_property_version": dataset_version(root, FLOW_PROPERTY_NS),
        "names": multilingual_names(root, FLOW_PROPERTY_NS),
        "reference_unit_group_uuid": unit_group_uuid.strip(),
        "reference_unit_group_version": ref.attrib.get("version"),
    }


def inspect_unit_group(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    require(root.tag == f"{{{UNIT_GROUP_NS}}}unitGroupDataSet", "unit-group root mismatch")
    unit_group_uuid = common_uuid(root)
    quantitative = root.find(f"{{{UNIT_GROUP_NS}}}unitGroupInformation/{{{UNIT_GROUP_NS}}}quantitativeReference")
    require(quantitative is not None, "unit-group quantitativeReference missing")
    ref_id = first_text(quantitative, f"{{{UNIT_GROUP_NS}}}referenceToReferenceUnit", "reference unit internal ID")
    units = [
        node
        for node in root.findall(f"{{{UNIT_GROUP_NS}}}units/{{{UNIT_GROUP_NS}}}unit")
        if node.attrib.get("dataSetInternalID") == ref_id
    ]
    require(len(units) == 1, f"reference unit {ref_id} is missing or ambiguous")
    unit = units[0]
    name = first_text(unit, f"{{{UNIT_GROUP_NS}}}name", "reference unit name")
    factor_lexical = first_text(unit, f"{{{UNIT_GROUP_NS}}}meanValue", "reference unit factor")
    return {
        "unit_group_uuid": unit_group_uuid,
        "unit_group_version": dataset_version(root, UNIT_GROUP_NS),
        "reference_unit_internal_id": ref_id,
        "reference_unit_name": name,
        "reference_unit_factor": {
            "lexical": factor_lexical,
            "decimal": canonical_decimal(factor_lexical, "reference unit factor"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12-root", type=Path, required=True)
    parser.add_argument("--v13-root", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    v12 = args.v12_root.resolve()
    v13 = args.v13_root.resolve()
    master = args.master_root.resolve()
    verify_repo(v12, EXPECTED_V12_COMMIT)
    verify_repo(v13, EXPECTED_V13_COMMIT)
    verify_repo(master, EXPECTED_MASTER_COMMIT)

    v12_process_evidence = file_evidence(v12, V12_PROCESS)
    v13_process_evidence = file_evidence(v13, V13_PROCESS)
    v12_flow_evidence = file_evidence(v12, FLOW_PATH)
    v13_flow_evidence = file_evidence(v13, FLOW_PATH)
    flow_property_evidence = file_evidence(master, FLOW_PROPERTY_PATH)
    unit_group_evidence = file_evidence(master, UNIT_GROUP_PATH)

    v12_process = inspect_process(v12 / V12_PROCESS, "1.2")
    v13_process = inspect_process(v13 / V13_PROCESS, "1.3")
    v12_flow = inspect_flow(v12 / FLOW_PATH)
    v13_flow = inspect_flow(v13 / FLOW_PATH)
    flow_property = inspect_flow_property(master / FLOW_PROPERTY_PATH)
    unit_group = inspect_unit_group(master / UNIT_GROUP_PATH)

    # Fixture-specific assertions belong here, not inside the reusable parser.
    require(v12_process["process_uuid"] == v13_process["process_uuid"] == PROCESS_UUID, "pinned process UUID mismatch")
    require(v12_flow["flow_uuid"] == v13_flow["flow_uuid"] == FLOW_UUID, "pinned product-flow UUID mismatch")
    require(flow_property["flow_property_uuid"] == FLOW_PROPERTY_UUID, "pinned flow-property master UUID mismatch")
    require(unit_group["unit_group_uuid"] == UNIT_GROUP_UUID, "pinned unit-group master UUID mismatch")

    for label, process in (("v1.2", v12_process), ("v1.3", v13_process)):
        require(process["reference_exchange_internal_id"] == "42", f"{label} unexpected reference exchange")
        require(process["product_flow_uuid"] == FLOW_UUID, f"{label} process/product-flow UUID mismatch")
        require(process["product_flow_version"] == "00.00.001", f"{label} unexpected product-flow version")
        require(process["exchange_amount"]["decimal"] == "1", f"{label} process exchange amount is not identity 1")
    for label, flow in (("v1.2", v12_flow), ("v1.3", v13_flow)):
        require(flow["reference_flow_property_internal_id"] == "0", f"{label} unexpected flow-property internal ID")
        require(flow["flow_property_uuid"] == FLOW_PROPERTY_UUID, f"{label} flow/flow-property UUID mismatch")
        require(flow["flow_property_version"] == "03.00.000", f"{label} unexpected flow-property version")
        require(flow["flow_property_mean"]["decimal"] == "1", f"{label} flow-property mean is not identity 1")
    require(flow_property["reference_unit_group_uuid"] == UNIT_GROUP_UUID, "pinned flow-property/unit-group UUID mismatch")
    require(unit_group["reference_unit_internal_id"] == "0", "unexpected reference unit internal ID")
    require(unit_group["reference_unit_name"] == "kg", "unexpected reference unit name")
    require(unit_group["reference_unit_factor"]["decimal"] == "1", "reference unit factor is not identity 1")

    report: dict[str, Any] = {
        "verdict": "DECLARED_REFERENCE_BASIS_RESEARCH_VERIFIABLE",
        "research_version": "1.3.0",
        "extractor_accepted": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "upstreams": {
            "v12_commit": EXPECTED_V12_COMMIT,
            "v13_commit": EXPECTED_V13_COMMIT,
            "master_data_commit": EXPECTED_MASTER_COMMIT,
        },
        "file_evidence": {
            "v12_process": v12_process_evidence,
            "v13_process": v13_process_evidence,
            "v12_product_flow": v12_flow_evidence,
            "v13_product_flow": v13_flow_evidence,
            "flow_property_master": flow_property_evidence,
            "unit_group_master": unit_group_evidence,
        },
        "v12": {"process": v12_process, "flow": v12_flow},
        "v13": {"process": v13_process, "flow": v13_flow},
        "flow_property_master": flow_property,
        "unit_group_master": unit_group,
        "initial_known_answer": {
            "bounded_basis_text": "1 kg of the referenced wood-panel product flow",
            "identity_chain": True,
            "basis_components": [
                {"name": "process reference exchange meanAmount", "decimal": "1"},
                {"name": "reference flow-property meanValue", "decimal": "1"},
                {"name": "reference unit factor", "decimal": "1", "unit": "kg"},
            ],
            "scope": "Pinned InData wood-panel v1.2/v1.3 public fixtures only; not a universal EPD basis rule.",
        },
        "limitations": [
            "This research freeze proves the observed quantitative-reference chain for pinned public fixtures only.",
            "No environmental indicator value is divided, multiplied, aggregated, converted, or otherwise transformed by this probe.",
            "A future real/provider reference closure requires independent source-use authority and provenance; this probe does not authorize network substitution by UUID/name.",
            "The known-answer 1 kg basis must not be generalized to arbitrary EPDs.",
        ],
    }
    report["receipt_sha256"] = hashlib.sha256(canonical_json_bytes(report)).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
