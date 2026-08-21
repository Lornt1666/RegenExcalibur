#!/usr/bin/env python3
"""Research-only probe for ILCD+EPD declared environmental indicator structure.

This tool records observed structure from immutable public InData samples. It does
not implement accepted indicator extraction and must not be used to claim
scientific validity, professional review, provider authority, or certification.

The probe intentionally makes no assumption that an environmental indicator is
stored beneath a node called ``exchange`` or ``module``. Exact catalogue UUID
occurrences are located anywhere in the process document and their ancestry and
bounded structural neighbourhood are retained for evidence-driven parser design.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

GWP_TOTAL_UUID = "6a37f984-a4b3-458a-a20a-64418c145fa2"
V12_COMMIT = "b7233bd2dd5435a6b5973505ffa212cd03d23468"
V13_COMMIT = "7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa"
CATALOGUE = Path("doc/identifiers/EN15804+A2_EF3.0_indicators.csv")
SIGNAL_TOKENS = (
    "lcia",
    "result",
    "indicator",
    "impact",
    "module",
    "scenario",
    "amount",
    "value",
    "unit",
    "exchange",
    "reference",
    "other",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def namespace(tag: str) -> str | None:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else None


def text(node: ET.Element) -> str | None:
    value = (node.text or "").strip()
    return value or None


def normalized_attributes(node: ET.Element) -> dict[str, str]:
    return {local(key): value for key, value in sorted(node.attrib.items())}


def path_for(node: ET.Element, parent: dict[ET.Element, ET.Element]) -> str:
    parts: list[str] = []
    current: ET.Element | None = node
    while current is not None:
        parts.append(local(current.tag))
        current = parent.get(current)
    return "/".join(reversed(parts))


def has_exact_uuid(node: ET.Element, uuid: str) -> bool:
    return uuid in node.attrib.values() or text(node) == uuid


def node_snapshot(node: ET.Element, parent: dict[ET.Element, ET.Element]) -> dict[str, Any]:
    return {
        "path": path_for(node, parent),
        "name": local(node.tag),
        "namespace": namespace(node.tag),
        "text": text(node),
        "attributes": normalized_attributes(node),
    }


def is_signal(node: ET.Element) -> bool:
    name = local(node.tag).lower()
    if any(token in name for token in SIGNAL_TOKENS):
        return True
    for key in node.attrib:
        key_name = local(key).lower()
        if any(token in key_name for token in SIGNAL_TOKENS):
            return True
    return False


def ancestor_chain(node: ET.Element, parent: dict[ET.Element, ET.Element]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    current: ET.Element | None = node
    while current is not None:
        chain.append(node_snapshot(current, parent))
        current = parent.get(current)
    chain.reverse()
    return chain


def relevant_descendants(node: ET.Element, parent: dict[ET.Element, ET.Element], *, limit: int = 80) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for descendant in node.iter():
        if descendant is node:
            continue
        if is_signal(descendant) or has_exact_uuid(descendant, GWP_TOTAL_UUID):
            rows.append(node_snapshot(descendant, parent))
            if len(rows) >= limit:
                break
    return rows


def ancestry_neighbourhood(node: ET.Element, parent: dict[ET.Element, ET.Element]) -> list[dict[str, Any]]:
    """Record each ancestor plus relevant direct children/descendants.

    This gives enough context to discover a meaningful result container without
    requiring a pre-selected element name such as ``exchange`` or ``LCIAResult``.
    """

    rows: list[dict[str, Any]] = []
    current: ET.Element | None = node
    depth = 0
    while current is not None:
        direct_children = [
            node_snapshot(child, parent)
            for child in list(current)
            if is_signal(child) or has_exact_uuid(child, GWP_TOTAL_UUID)
        ]
        rows.append(
            {
                "depth_from_occurrence": depth,
                "self": node_snapshot(current, parent),
                "relevant_direct_children": direct_children[:40],
                "relevant_descendants": relevant_descendants(current, parent, limit=80),
            }
        )
        current = parent.get(current)
        depth += 1
    return rows


def inspect_samples(repo: Path, expected_version: str) -> dict[str, Any]:
    process_root = repo / "sample_data" / "processes"
    occurrences: list[dict[str, Any]] = []
    global_signals: list[dict[str, Any]] = []
    inspected_files = 0

    for xml in sorted(process_root.glob("*.xml")):
        try:
            root = ET.parse(xml).getroot()
        except ET.ParseError:
            continue

        declared_version = next(
            (value for key, value in root.attrib.items() if key.endswith("}epd-version")),
            None,
        )
        if declared_version and declared_version != expected_version:
            continue
        inspected_files += 1
        parent = {child: ancestor for ancestor in root.iter() for child in ancestor}
        relative = str(xml.relative_to(repo))
        file_sha = sha256_file(xml)

        for node in root.iter():
            if is_signal(node):
                global_signals.append(
                    {
                        "file": relative,
                        "file_sha256": file_sha,
                        **node_snapshot(node, parent),
                    }
                )
            if not has_exact_uuid(node, GWP_TOTAL_UUID):
                continue
            occurrences.append(
                {
                    "file": relative,
                    "file_sha256": file_sha,
                    "declared_epd_version": declared_version,
                    "occurrence": node_snapshot(node, parent),
                    "ancestor_chain": ancestor_chain(node, parent),
                    "ancestry_neighbourhood": ancestry_neighbourhood(node, parent),
                }
            )

    return {
        "expected_version": expected_version,
        "inspected_process_file_count": inspected_files,
        "gwp_total_occurrence_count": len(occurrences),
        "gwp_total_occurrences": occurrences,
        "structural_signal_count": len(global_signals),
        "structural_signals": global_signals,
    }


def catalogue_identity(v13: Path) -> dict[str, Any]:
    path = v13 / CATALOGUE
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    matches = [row for row in rows if row.get("UUID") == GWP_TOTAL_UUID]
    if len(matches) != 1:
        raise ValueError(f"expected one GWP-total catalogue row, found {len(matches)}")
    row = matches[0]
    if row["Name (en)"] != "Global Warming Potential - total (GWP-total)":
        raise ValueError("unexpected GWP-total catalogue name")
    if row["Unit (en)"] != "kg CO2 eqv.":
        raise ValueError("unexpected GWP-total catalogue unit")
    if row["UnitGroup UUID"] != "1ebf3012-d0db-4de2-aefd-ef30cedb0be1":
        raise ValueError("unexpected GWP-total unit-group UUID")
    return {
        "path": str(CATALOGUE),
        "sha256": sha256_file(path),
        "gwp_total": {
            "uuid": row["UUID"],
            "version": row["Version"],
            "name_en": row["Name (en)"],
            "unit_en": row["Unit (en)"],
            "unit_group_uuid": row["UnitGroup UUID"],
        },
    }


def build_receipt(v12: Path, v13: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "verdict": "DECLARED_INDICATOR_STRUCTURE_RESEARCH_VERIFIABLE",
        "scope": "Research-only structural discovery. No environmental indicator extraction acceptance claim.",
        "upstreams": {
            "v12_commit": V12_COMMIT,
            "v13_commit": V13_COMMIT,
        },
        "catalogue": catalogue_identity(v13),
        "v12": inspect_samples(v12, "1.2"),
        "v13": inspect_samples(v13, "1.3"),
        "observations": [
            "GWP-total is located by exact catalogue UUID, not by a human-readable label.",
            "No element-name assumption is made for the result container; exact occurrence ancestry and structural neighbourhood are retained.",
            "Literal module elements and exchange ancestors are not required by the research gate because prior probes disproved those assumptions for the pinned samples.",
            "The research receipt is evidence for parser design only and does not authorize environmental-value extraction.",
        ],
        "extractor_accepted": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    # Writeable research quality gate: the exact catalogue UUID must occur at
    # least once in each pinned version. No stronger structural interpretation
    # is accepted until the retained ancestry evidence has been inspected.
    if report["v12"]["gwp_total_occurrence_count"] < 1:
        raise ValueError("no exact GWP-total UUID occurrence found in pinned v1.2 samples")
    if report["v13"]["gwp_total_occurrence_count"] < 1:
        raise ValueError("no exact GWP-total UUID occurrence found in pinned v1.3 samples")
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    report["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12-root", type=Path, required=True)
    parser.add_argument("--v13-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_receipt(args.v12_root.resolve(), args.v13_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "verdict": report["verdict"],
                "catalogue_sha256": report["catalogue"]["sha256"],
                "v12_gwp_total_occurrence_count": report["v12"]["gwp_total_occurrence_count"],
                "v13_gwp_total_occurrence_count": report["v13"]["gwp_total_occurrence_count"],
                "v12_structural_signal_count": report["v12"]["structural_signal_count"],
                "v13_structural_signal_count": report["v13"]["structural_signal_count"],
                "receipt_sha256": report["receipt_sha256"],
                "extractor_accepted": report["extractor_accepted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
