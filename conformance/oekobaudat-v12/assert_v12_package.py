#!/usr/bin/env python3
"""Fail-closed ILCD+EPD v1.2 package guard for the v0.8 profile lane.

This guard runs before ÖKOBAUDAT profile 3.8.0 evaluation. It prevents a v1.3
process dataset from being represented as validated by the v1.2 profile lane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
EXPECTED_VERSION = "1.2"


class VersionGuardError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def inspect_package(package_root: Path) -> dict:
    package_root = package_root.resolve()
    if not package_root.is_dir():
        raise VersionGuardError(f"package root not found: {package_root}")

    processes = sorted(package_root.rglob("*.xml"))
    rows = []
    process_count = 0
    for path in processes:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != f"{{{PROCESS_NS}}}processDataSet":
            continue
        process_count += 1
        version = root.attrib.get(f"{{{EPD_2019_NS}}}epd-version")
        rows.append({
            "path": path.relative_to(package_root).as_posix(),
            "sha256": sha256_file(path),
            "epd_version": version,
        })

    if process_count == 0:
        raise VersionGuardError("no ILCD processDataSet was found in package")

    mismatches = [row for row in rows if row["epd_version"] != EXPECTED_VERSION]
    receipt = {
        "guard": {
            "name": "ProofGrid v0.8 ILCD+EPD v1.2 package guard",
            "version": "0.8.0",
            "expected_epd_version": EXPECTED_VERSION,
        },
        "process_datasets": rows,
        "process_count": process_count,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "verdict": "ILCD_EPD_V12_VERSION_GUARD_PASS" if not mismatches else "ILCD_EPD_V12_VERSION_GUARD_FAIL",
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    if mismatches:
        raise VersionGuardError(json.dumps(receipt, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = inspect_package(args.package_root)
    except VersionGuardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT: {receipt['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
