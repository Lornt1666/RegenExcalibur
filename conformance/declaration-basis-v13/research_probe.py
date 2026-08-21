#!/usr/bin/env python3
"""Research-only resolver for the ILCD+EPD declaration/reference basis graph.

The probe resolves cross-dataset references by UUID parsed from pinned XML
content. It deliberately preserves both process-reference exchange meanAmount
and resultingAmount and does not select either as the declaration basis.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

COMMON_NS = "http://lca.jrc.it/ILCD/Common"
EPD_2019_NS = "http://www.indata.network/EPD/2019"

V12_COMMIT = "b7233bd2dd5435a6b5973505ffa212cd03d23468"
V13_COMMIT = "7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa"
MASTER_COMMIT = "32117b6a70d6c486344247a429449755a2c7eab4"

V12_PROCESS = Path("sample_data/processes/57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")
V13_PROCESS = Path("sample_data/processes/EPDv1.3_example_57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml")


class ResearchError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetCandidate:
    source: str
    root: Path
    path: Path
    uuid: str
    kind: str
    sha256: str

    def relative_path(self) -> str:
        return self.path.relative_to(self.root).as_posix()

    def receipt_row(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.relative_path(),
            "uuid": self.uuid,
            "kind": self.kind,
            "sha256": self.sha256,
        }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchError(message)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    value = (node.text or "").strip()
    return value or None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_decimal(lexical: str | None, label: str) -> dict[str, str] | None:
    if lexical is None:
        return None
    try:
        value = Decimal(lexical)
    except (InvalidOperation, ValueError) as exc:
        raise ResearchError(f"{label} is not numeric: {lexical!r}") from exc
    require(value.is_finite(), f"{label} must be finite: {lexical!r}")
    if value == 0:
        canonical = "0"
    else:
        canonical = format(value, "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
        if canonical == "-0":
            canonical = "0"
    return {"lexical": lexical, "decimal": canonical}


def first_uuid(root: ET.Element) -> str | None:
    for node in root.iter():
        if local(node.tag) == "UUID" and text(node):
            return text(node)
    return None


def dataset_kind(root: ET.Element) -> str:
    return local(root.tag)


def build_index(roots: list[tuple[str, Path]]) -> dict[str, list[DatasetCandidate]]:
    index: dict[str, list[DatasetCandidate]] = {}
    for source, root_path in roots:
        for path in sorted(root_path.rglob("*.xml")):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            uuid = first_uuid(root)
            if not uuid:
                continue
            row = DatasetCandidate(
                source=source,
                root=root_path,
                path=path,
                uuid=uuid,
                kind=dataset_kind(root),
                sha256=sha256_file(path),
            )
            index.setdefault(uuid, []).append(row)
    return index


def resolve_uuid(
    index: dict[str, list[DatasetCandidate]],
    uuid: str,
    *,
    preferred_source: str,
    expected_kinds: set[str] | None = None,
) -> tuple[DatasetCandidate, dict[str, Any]]:
    candidates = list(index.get(uuid, []))
    if expected_kinds is not None:
        candidates = [row for row in candidates if row.kind in expected_kinds]
    require(bool(candidates), f"referenced dataset UUID was not resolved: {uuid}")

    distinct_hashes = sorted({row.sha256 for row in candidates})
    require(
        len(distinct_hashes) == 1,
        f"referenced UUID resolves to non-identical dataset bytes: {uuid}; hashes={distinct_hashes}",
    )

    preferred = [row for row in candidates if row.source == preferred_source]
    master = [row for row in candidates if row.source == "master"]
    if preferred:
        selected = sorted(preferred, key=lambda row: row.relative_path())[0]
        policy = "PREFERRED_VERSION_SOURCE_IDENTICAL_BYTES"
    elif master:
        selected = sorted(master, key=lambda row: row.relative_path())[0]
        policy = "PINNED_MASTER_SOURCE_IDENTICAL_BYTES"
    else:
        selected = sorted(candidates, key=lambda row: (row.source, row.relative_path()))[0]
        policy = "IDENTICAL_BYTES_DETERMINISTIC_FALLBACK"

    return selected, {
        "uuid": uuid,
        "candidate_count": len(candidates),
        "distinct_byte_hash_count": len(distinct_hashes),
        "all_candidates_identical": True,
        "selection_policy": policy,
        "selected": selected.receipt_row(),
        "candidates": [row.receipt_row() for row in sorted(candidates, key=lambda row: (row.source, row.relative_path()))],
    }


def child_by_local(parent: ET.Element, name: str) -> ET.Element | None:
    for child in list(parent):
        if local(child.tag) == name:
            return child
    return None


def children_by_local(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if local(child.tag) == name]


def descendants_by_local(parent: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in parent.iter() if local(node.tag) == name]


def multilingual_texts(node: ET.Element | None) -> list[dict[str, str | None]]:
    if node is None:
        return []
    rows: list[dict[str, str | None]] = []
    for child in node.iter():
        value = text(child)
        if value is None:
            continue
        if local(child.tag) in {"baseName", "shortDescription", "name"}:
            lang = child.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
            rows.append({"name": local(child.tag), "language": lang, "value": value})
    return rows


def parse_process_reference(process_path: Path, expected_version: str) -> dict[str, Any]:
    root = ET.parse(process_path).getroot()
    uuid = first_uuid(root)
    require(bool(uuid), f"process UUID missing: {process_path}")
    version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
    require(version == expected_version, f"unexpected process epd-version: expected {expected_version}, got {version}")

    process_information = next((node for node in root.iter() if local(node.tag) == "processInformation"), None)
    require(process_information is not None, "processInformation missing")
    quantitative = child_by_local(process_information, "quantitativeReference")
    require(quantitative is not None, "process quantitativeReference missing")
    ref_nodes = children_by_local(quantitative, "referenceToReferenceFlow")
    ref_ids = [text(node) for node in ref_nodes if text(node)]
    require(len(ref_ids) == 1, f"research control requires exactly one reference-flow internal ID; found {ref_ids}")
    ref_id = ref_ids[0]

    exchanges = next((node for node in root.iter() if local(node.tag) == "exchanges"), None)
    require(exchanges is not None, "process exchanges missing")
    matches = [
        node
        for node in children_by_local(exchanges, "exchange")
        if node.attrib.get("dataSetInternalID") == ref_id
    ]
    require(len(matches) == 1, f"reference exchange internal ID {ref_id} resolved to {len(matches)} exchanges")
    exchange = matches[0]
    flow_ref = child_by_local(exchange, "referenceToFlowDataSet")
    require(flow_ref is not None, "reference exchange has no referenceToFlowDataSet")
    flow_uuid = flow_ref.attrib.get("refObjectId")
    require(bool(flow_uuid), "referenceToFlowDataSet has no refObjectId")

    mean = canonical_decimal(text(child_by_local(exchange, "meanAmount")), "process reference exchange meanAmount")
    resulting = canonical_decimal(text(child_by_local(exchange, "resultingAmount")), "process reference exchange resultingAmount")
    require(mean is not None, "process reference exchange meanAmount missing")

    return {
        "process": {
            "path": process_path.as_posix(),
            "sha256": sha256_file(process_path),
            "uuid": uuid,
            "epd_version": version,
        },
        "quantitative_reference": {
            "type": quantitative.attrib.get("type"),
            "reference_flow_internal_ids": ref_ids,
        },
        "reference_exchange": {
            "internal_id": ref_id,
            "mean_amount": mean,
            "resulting_amount": resulting,
            "reference_to_flow_dataset": {
                "uuid": flow_uuid,
                "version": flow_ref.attrib.get("version"),
                "uri": flow_ref.attrib.get("uri"),
                "descriptions": multilingual_texts(flow_ref),
            },
        },
    }


def parse_flow_reference(flow_path: Path) -> dict[str, Any]:
    root = ET.parse(flow_path).getroot()
    require(local(root.tag) == "flowDataSet", f"resolved reference is not a flowDataSet: {flow_path}")
    uuid = first_uuid(root)
    require(bool(uuid), "flow dataset UUID missing")

    flow_information = next((node for node in root.iter() if local(node.tag) == "flowInformation"), None)
    require(flow_information is not None, "flowInformation missing")
    quantitative = child_by_local(flow_information, "quantitativeReference")
    require(quantitative is not None, "flow quantitativeReference missing")
    ref_nodes = children_by_local(quantitative, "referenceToReferenceFlowProperty")
    ref_ids = [text(node) for node in ref_nodes if text(node)]
    require(len(ref_ids) == 1, f"flow research control requires one reference flow-property ID; found {ref_ids}")
    ref_id = ref_ids[0]

    flow_properties = next((node for node in root.iter() if local(node.tag) == "flowProperties"), None)
    require(flow_properties is not None, "flowProperties missing")
    matches = [
        node
        for node in children_by_local(flow_properties, "flowProperty")
        if node.attrib.get("dataSetInternalID") == ref_id
    ]
    require(len(matches) == 1, f"reference flow-property internal ID {ref_id} resolved to {len(matches)} flowProperty entries")
    relation = matches[0]
    property_ref = child_by_local(relation, "referenceToFlowPropertyDataSet")
    require(property_ref is not None, "reference flowProperty has no referenceToFlowPropertyDataSet")
    property_uuid = property_ref.attrib.get("refObjectId")
    require(bool(property_uuid), "referenceToFlowPropertyDataSet has no refObjectId")

    material_signals: list[dict[str, Any]] = []
    for node in root.iter():
        lname = local(node.tag)
        if lname in {"materialProperties", "materialProperty"}:
            material_signals.append(
                {
                    "element": lname,
                    "attributes": {local(key): value for key, value in sorted(node.attrib.items())},
                    "text": text(node),
                    "children": [
                        {
                            "element": local(child.tag),
                            "attributes": {local(key): value for key, value in sorted(child.attrib.items())},
                            "text": text(child),
                        }
                        for child in list(node)
                    ],
                }
            )

    return {
        "flow": {
            "path": flow_path.as_posix(),
            "sha256": sha256_file(flow_path),
            "uuid": uuid,
            "names": multilingual_texts(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "quantitative_reference": {
            "type": quantitative.attrib.get("type"),
            "reference_flow_property_internal_ids": ref_ids,
        },
        "reference_flow_property_relation": {
            "internal_id": ref_id,
            "mean_value": canonical_decimal(text(child_by_local(relation, "meanValue")), "flow-property relation meanValue"),
            "reference_to_flow_property_dataset": {
                "uuid": property_uuid,
                "version": property_ref.attrib.get("version"),
                "uri": property_ref.attrib.get("uri"),
                "descriptions": multilingual_texts(property_ref),
            },
        },
        "material_property_signals": material_signals,
    }


def parse_flow_property(flow_property_path: Path) -> dict[str, Any]:
    root = ET.parse(flow_property_path).getroot()
    require(local(root.tag) == "flowPropertyDataSet", f"resolved reference is not a flowPropertyDataSet: {flow_property_path}")
    uuid = first_uuid(root)
    require(bool(uuid), "flow-property UUID missing")

    unit_refs = [
        node
        for node in root.iter()
        if "UnitGroup" in local(node.tag) and bool(node.attrib.get("refObjectId"))
    ]
    unique = sorted({node.attrib["refObjectId"] for node in unit_refs})
    require(len(unique) == 1, f"flow-property unit-group reference is unresolved/ambiguous: {unique}")
    unit_uuid = unique[0]
    selected = next(node for node in unit_refs if node.attrib.get("refObjectId") == unit_uuid)

    return {
        "flow_property": {
            "path": flow_property_path.as_posix(),
            "sha256": sha256_file(flow_property_path),
            "uuid": uuid,
            "names": multilingual_texts(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "reference_to_unit_group": {
            "element": local(selected.tag),
            "uuid": unit_uuid,
            "version": selected.attrib.get("version"),
            "uri": selected.attrib.get("uri"),
            "descriptions": multilingual_texts(selected),
        },
    }


def parse_unit_group(unit_group_path: Path) -> dict[str, Any]:
    root = ET.parse(unit_group_path).getroot()
    require(local(root.tag) == "unitGroupDataSet", f"resolved reference is not a unitGroupDataSet: {unit_group_path}")
    uuid = first_uuid(root)
    require(bool(uuid), "unit-group UUID missing")

    quantitative = next((node for node in root.iter() if local(node.tag) == "quantitativeReference"), None)
    require(quantitative is not None, "unit-group quantitativeReference missing")
    reference_node = child_by_local(quantitative, "referenceToReferenceUnit")
    require(reference_node is not None and text(reference_node), "unit-group referenceToReferenceUnit missing")
    reference_id = text(reference_node)

    units_parent = next((node for node in root.iter() if local(node.tag) == "units"), None)
    require(units_parent is not None, "unit-group units collection missing")
    matches = [
        node
        for node in children_by_local(units_parent, "unit")
        if node.attrib.get("dataSetInternalID") == reference_id
    ]
    require(len(matches) == 1, f"reference unit internal ID {reference_id} resolved to {len(matches)} units")
    unit = matches[0]
    name = text(child_by_local(unit, "name"))
    mean = canonical_decimal(text(child_by_local(unit, "meanValue")), "unit reference meanValue")
    require(bool(name), "reference unit name missing")
    require(mean is not None, "reference unit meanValue missing")

    return {
        "unit_group": {
            "path": unit_group_path.as_posix(),
            "sha256": sha256_file(unit_group_path),
            "uuid": uuid,
            "names": multilingual_texts(next((node for node in root.iter() if local(node.tag) == "dataSetInformation"), None)),
        },
        "reference_unit": {
            "internal_id": reference_id,
            "name": name,
            "conversion_factor": mean,
        },
    }


def research_one(
    process_path: Path,
    expected_version: str,
    preferred_source: str,
    index: dict[str, list[DatasetCandidate]],
) -> dict[str, Any]:
    process = parse_process_reference(process_path, expected_version)
    flow_uuid = process["reference_exchange"]["reference_to_flow_dataset"]["uuid"]
    flow_candidate, flow_resolution = resolve_uuid(
        index,
        flow_uuid,
        preferred_source=preferred_source,
        expected_kinds={"flowDataSet"},
    )
    flow = parse_flow_reference(flow_candidate.path)

    property_uuid = flow["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"]
    property_candidate, property_resolution = resolve_uuid(
        index,
        property_uuid,
        preferred_source=preferred_source,
        expected_kinds={"flowPropertyDataSet"},
    )
    flow_property = parse_flow_property(property_candidate.path)

    unit_uuid = flow_property["reference_to_unit_group"]["uuid"]
    unit_candidate, unit_resolution = resolve_uuid(
        index,
        unit_uuid,
        preferred_source=preferred_source,
        expected_kinds={"unitGroupDataSet"},
    )
    unit_group = parse_unit_group(unit_candidate.path)

    return {
        "process_reference": process,
        "flow_resolution": flow_resolution,
        "flow_reference": flow,
        "flow_property_resolution": property_resolution,
        "flow_property_reference": flow_property,
        "unit_group_resolution": unit_resolution,
        "unit_group_reference": unit_group,
        "declaration_basis_selected": False,
        "building_quantity_multiplication_permitted": False,
        "unit_conversion_performed": False,
    }


def build_receipt(v12_root: Path, v13_root: Path, master_root: Path) -> dict[str, Any]:
    index = build_index([
        ("v12", v12_root),
        ("v13", v13_root),
        ("master", master_root),
    ])
    v12 = research_one(v12_root / V12_PROCESS, "1.2", "v12", index)
    v13 = research_one(v13_root / V13_PROCESS, "1.3", "v13", index)

    comparison = {
        "process_reference_flow_uuid_matches": (
            v12["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"]
            == v13["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"]
        ),
        "flow_property_uuid_matches": (
            v12["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"]
            == v13["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"]
        ),
        "unit_group_uuid_matches": (
            v12["flow_property_reference"]["reference_to_unit_group"]["uuid"]
            == v13["flow_property_reference"]["reference_to_unit_group"]["uuid"]
        ),
        "reference_exchange_mean_amount_matches": (
            v12["process_reference"]["reference_exchange"]["mean_amount"]
            == v13["process_reference"]["reference_exchange"]["mean_amount"]
        ),
        "reference_exchange_resulting_amount_matches": (
            v12["process_reference"]["reference_exchange"]["resulting_amount"]
            == v13["process_reference"]["reference_exchange"]["resulting_amount"]
        ),
        "reference_unit_matches": (
            v12["unit_group_reference"]["reference_unit"]
            == v13["unit_group_reference"]["reference_unit"]
        ),
    }

    report: dict[str, Any] = {
        "verdict": "DECLARATION_BASIS_STRUCTURE_RESEARCH_VERIFIABLE",
        "research_version": "1.3.0",
        "scope": "Research-only UUID-resolved declaration/reference basis graph. No declaration basis is selected and no building-level multiplication is permitted.",
        "upstreams": {
            "v12_commit": V12_COMMIT,
            "v13_commit": V13_COMMIT,
            "master_data_commit": MASTER_COMMIT,
        },
        "dataset_index": {
            "unique_uuid_count": len(index),
            "candidate_count": sum(len(rows) for rows in index.values()),
        },
        "v12": v12,
        "v13": v13,
        "comparison": comparison,
        "declaration_basis_selected": False,
        "basis_extractor_accepted": False,
        "building_quantity_multiplication_permitted": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "The receipt resolves source reference identities and dimensions but does not choose meanAmount or resultingAmount as the declaration basis.",
            "Material-property signals are retained separately and are not treated as the declared reference quantity.",
            "The environmental-result unit is not treated as the product/reference unit.",
            "No building quantity multiplication, LCA conclusion, professional review, regulatory approval, or certification is produced.",
        ],
    }
    raw = canonical_json_bytes(report)
    report["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12-root", type=Path, required=True)
    parser.add_argument("--v13-root", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_receipt(
        args.v12_root.resolve(),
        args.v13_root.resolve(),
        args.master_root.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "v12_reference_flow_uuid": report["v12"]["process_reference"]["reference_exchange"]["reference_to_flow_dataset"]["uuid"],
        "v12_flow_property_uuid": report["v12"]["flow_reference"]["reference_flow_property_relation"]["reference_to_flow_property_dataset"]["uuid"],
        "v12_unit_group_uuid": report["v12"]["flow_property_reference"]["reference_to_unit_group"]["uuid"],
        "v12_reference_unit": report["v12"]["unit_group_reference"]["reference_unit"],
        "v12_mean_amount": report["v12"]["process_reference"]["reference_exchange"]["mean_amount"],
        "v12_resulting_amount": report["v12"]["process_reference"]["reference_exchange"]["resulting_amount"],
        "comparison": report["comparison"],
        "declaration_basis_selected": report["declaration_basis_selected"],
        "receipt_sha256": report["receipt_sha256"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
