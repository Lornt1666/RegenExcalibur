#!/usr/bin/env python3
"""Freeze exact GWP-total unit-group reference semantics for ProofGrid v1.1.

Research only. The output proves the identity of the pinned unit-group reference
unit and that its conversion factor is exactly one. It does not validate any
scientific result or authorize environmental-value extraction by itself.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

MASTER_COMMIT = "32117b6a70d6c486344247a429449755a2c7eab4"
GWP_UNIT_GROUP_UUID = "1ebf3012-d0db-4de2-aefd-ef30cedb0be1"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
UNIT_NS = "http://lca.jrc.it/ILCD/UnitGroup"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_decimal(value: str) -> str:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid unit conversion factor: {value}") from exc
    if not number.is_finite():
        raise ValueError("unit conversion factor must be finite")
    return format(number, "f")


def build_receipt(master_root: Path) -> dict:
    candidates = sorted(
        (master_root / "master_data" / "units" / "unitgroups").glob(
            f"*{GWP_UNIT_GROUP_UUID}.xml"
        )
    )
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one pinned GWP unit-group file, found {len(candidates)}"
        )
    path = candidates[0]
    root = ET.parse(path).getroot()
    uuid = root.findtext(
        f"{{{UNIT_NS}}}unitGroupInformation/{{{UNIT_NS}}}dataSetInformation/{{{COMMON_NS}}}UUID"
    )
    if uuid != GWP_UNIT_GROUP_UUID:
        raise ValueError(f"unit-group UUID mismatch: {uuid}")
    reference_id = root.findtext(
        f"{{{UNIT_NS}}}unitGroupInformation/{{{UNIT_NS}}}quantitativeReference/{{{UNIT_NS}}}referenceToReferenceUnit"
    )
    if reference_id is None:
        raise ValueError("unit group has no referenceToReferenceUnit")
    units = root.find(f"{{{UNIT_NS}}}units")
    if units is None:
        raise ValueError("unit group has no units collection")
    matches = [
        unit for unit in units.findall(f"{{{UNIT_NS}}}unit")
        if unit.attrib.get("dataSetInternalID") == reference_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"reference unit ID {reference_id} resolved to {len(matches)} units"
        )
    unit = matches[0]
    name = unit.findtext(f"{{{UNIT_NS}}}name")
    mean_lexical = unit.findtext(f"{{{UNIT_NS}}}meanValue")
    if not name or mean_lexical is None:
        raise ValueError("reference unit lacks name or meanValue")
    mean_canonical = canonical_decimal(mean_lexical.strip())
    if Decimal(mean_canonical) != Decimal("1"):
        raise ValueError(
            f"reference unit meanValue is not identity conversion: {mean_canonical}"
        )

    report = {
        "verdict": "INDICATOR_UNIT_REFERENCE_RESEARCH_VERIFIABLE",
        "scope": "Pinned unit-group identity research only; no extraction, scientific-validation, or certification claim.",
        "master_data": {
            "commit": MASTER_COMMIT,
            "path": str(path.relative_to(master_root).as_posix()),
            "sha256": sha256_file(path),
        },
        "unit_group": {
            "uuid": GWP_UNIT_GROUP_UUID,
            "reference_unit_internal_id": reference_id,
            "reference_unit_name": name.strip(),
            "reference_unit_mean_value_lexical": mean_lexical.strip(),
            "reference_unit_mean_value_decimal": mean_canonical,
            "identity_conversion": True,
        },
        "unit_identity_basis": "EXACT_UNIT_GROUP_UUID_AND_REFERENCE_UNIT_INTERNAL_ID",
        "implicit_unit_conversion_permitted": False,
        "extractor_accepted": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
    }
    raw = json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    report["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_receipt(args.master_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
