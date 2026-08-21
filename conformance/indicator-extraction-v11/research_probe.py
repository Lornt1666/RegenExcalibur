#!/usr/bin/env python3
"""Research-only probe for ILCD+EPD declared environmental indicator structure.

This tool records observed structure from immutable public InData samples. It does
not implement accepted indicator extraction and must not be used to claim
scientific validity, professional review, provider authority, or certification.
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
INTERESTING_NAMES = {
    "referenceToFlowDataSet",
    "meanAmount",
    "resultingAmount",
    "amount",
    "module",
    "scenario",
    "referenceToVariable",
    "exchange",
}


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


def interesting_signal(node: ET.Element) -> bool:
    name = local(node.tag)
    if name in INTERESTING_NAMES:
        return True
    for key in node.attrib:
        key_name = local(key).lower()
        if any(token in key_name for token in ("module", "scenario", "amount", "value", "unit")):
            return True
    return False


def node_snapshot(node: ET.Element, parent: dict[ET.Element, ET.Element]) -> dict[str, Any]:
    return {
        "path": path_for(node, parent),
        "name": local(node.tag),
        "namespace": namespace(node.tag),
        "text": text(node),
        "attributes": normalized_attributes(node),
    }


def inspect_samples(repo: Path, expected_version: str) -> dict[str, Any]:
    process_root = repo / "sample_data" / "processes"
    files: list[dict[str, Any]] = []
    exact_gwp_exchange_count = 0
    global_module_or_scenario_signals: list[dict[str, Any]] = []

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

        parent = {child: node for node in root.iter() for child in node}
        file_row: dict[str, Any] = {
            "path": str(xml.relative_to(repo)),
            "sha256": sha256_file(xml),
            "declared_epd_version": declared_version,
            "gwp_total_exchanges": [],
        }

        for node in root.iter():
            name = local(node.tag).lower()
            attr_names = [local(key).lower() for key in node.attrib]
            if (
                "module" in name
                or "scenario" in name
                or any("module" in key or "scenario" in key for key in attr_names)
            ):
                global_module_or_scenario_signals.append(
                    {
                        "file": str(xml.relative_to(repo)),
                        **node_snapshot(node, parent),
                    }
                )

        for exchange in (node for node in root.iter() if local(node.tag) == "exchange"):
            descendants = list(exchange.iter())
            if not any(has_exact_uuid(node, GWP_TOTAL_UUID) for node in descendants):
                continue

            exact_gwp_exchange_count += 1
            signals = [node_snapshot(node, parent) for node in descendants if interesting_signal(node) or has_exact_uuid(node, GWP_TOTAL_UUID)]
            file_row["gwp_total_exchanges"].append(
                {
                    "exchange": node_snapshot(exchange, parent),
                    "signals": signals,
                }
            )

        if file_row["gwp_total_exchanges"]:
            files.append(file_row)

    return {
        "expected_version": expected_version,
        "gwp_total_exchange_count": exact_gwp_exchange_count,
        "files_with_gwp_total": files,
        "module_or_scenario_signal_count": len(global_module_or_scenario_signals),
        "module_or_scenario_signals": global_module_or_scenario_signals,
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
            "Literal XML elements named module are not assumed; module/scenario semantics are discovered from observed elements and attributes.",
            "The enclosing exchange and relevant descendants are retained so a later parser can be designed from evidence rather than guessed paths.",
        ],
        "extractor_accepted": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    if report["v12"]["gwp_total_exchange_count"] < 1:
        raise ValueError("no exact GWP-total exchange found in pinned v1.2 samples")
    if report["v13"]["gwp_total_exchange_count"] < 1:
        raise ValueError("no exact GWP-total exchange found in pinned v1.3 samples")
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
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "catalogue_sha256": report["catalogue"]["sha256"],
        "v12_gwp_total_exchange_count": report["v12"]["gwp_total_exchange_count"],
        "v13_gwp_total_exchange_count": report["v13"]["gwp_total_exchange_count"],
        "v12_module_or_scenario_signal_count": report["v12"]["module_or_scenario_signal_count"],
        "v13_module_or_scenario_signal_count": report["v13"]["module_or_scenario_signal_count"],
        "receipt_sha256": report["receipt_sha256"],
        "extractor_accepted": report["extractor_accepted"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
