#!/usr/bin/env python3
"""ProofGrid v3.3 DigitalHub workbook material-specification discovery.

Parses the exact upstream DigitalHub XLSX as ZIP/XML using the Python standard
library. The output is source evidence only: literal workbook cell values,
candidate identifier hits, and literal concrete strength-class tokens.

No fuzzy matching, material inference, IFC->environmental mapping, or impact
calculation is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
import xml.etree.ElementTree as ET

EXPECTED_BYTES = 27409
EXPECTED_GIT_BLOB_SHA1 = "119270f598aee1c427cc52107bfb60ffee6526d8"
UPSTREAM_COMMIT = "36565d529b4dadeca625de2b793d7e16700171e9"
UPSTREAM_PATH = "Resources/Excel/DigitalHub_v1.xlsx"

CANDIDATE = {
    "global_id": "3BmeJtEDj3AQO77Os2w7Ny",
    "revit_object_id": "2395272",
    "type_token": "STB 250 x 400",
    "material_name": "Ortbeton - bewehrt",
}
STRENGTH_RE = re.compile(r"(?<![A-Z0-9])C\s*(\d{2})\s*/\s*(\d{2})(?![0-9])", re.I)

VERDICT = "DIGITALHUB_AUTHORITATIVE_WORKBOOK_MATERIAL_SPEC_DISCOVERY_VERIFIABLE"
STATE_BOUND = "AUTHORITATIVE_MATERIAL_SPEC_FOUND_AND_CANDIDATE_BOUND"
STATE_UNBOUND = "AUTHORITATIVE_MATERIAL_SPEC_PRESENT_BUT_NOT_CANDIDATE_BOUND"
STATE_ABSENT = "AUTHORITATIVE_MATERIAL_SPEC_NOT_FOUND_IN_UPSTREAM_WORKBOOK"
CANON = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"

class DiscoveryError(ValueError):
    pass

def require(cond: bool, msg: str) -> None:
    if not cond:
        raise DiscoveryError(msg)

def cbytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def pbytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()

def safe_zip_names(zf: zipfile.ZipFile) -> list[str]:
    names = sorted(zf.namelist())
    for name in names:
        p = PurePosixPath(name)
        require(not p.is_absolute(), f"absolute XLSX ZIP path rejected: {name}")
        require(".." not in p.parts, f"parent traversal XLSX ZIP path rejected: {name}")
    return names

def all_text(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.iter() if t.tag.endswith("}t") or t.tag == "t")

def parse_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(path))
    result = []
    for si in list(root):
        if si.tag.endswith("}si") or si.tag == "si":
            result.append(all_text(si))
    return result

def workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map: dict[str, str] = {}
    for rel in list(rels):
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rid and target:
            if target.startswith("/"):
                target = target.lstrip("/")
            elif not target.startswith("xl/"):
                target = "xl/" + target
            rel_map[rid] = str(PurePosixPath(target))
    out = []
    for elem in wb.iter():
        if not (elem.tag.endswith("}sheet") or elem.tag == "sheet"):
            continue
        name = elem.attrib.get("name")
        rid = elem.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id") or elem.attrib.get("r:id")
        if name and rid and rid in rel_map:
            out.append((name, rel_map[rid]))
    return out

def cell_value(cell: ET.Element, shared: list[str]) -> str:
    ctype = cell.attrib.get("t", "")
    if ctype == "inlineStr":
        return all_text(cell)
    v = None
    for child in list(cell):
        if child.tag.endswith("}v") or child.tag == "v":
            v = child.text or ""
            break
    if v is None:
        return ""
    if ctype == "s":
        try:
            idx = int(v)
            return shared[idx]
        except (ValueError, IndexError):
            raise DiscoveryError(f"invalid shared-string index: {v}")
    if ctype == "b":
        return "TRUE" if v == "1" else "FALSE"
    return v

def row_number(cell_ref: str) -> int | None:
    m = re.match(r"^[A-Z]+(\d+)$", cell_ref.upper())
    return int(m.group(1)) if m else None

def normalize_for_search(value: str) -> str:
    return " ".join(value.split())

def exact_contains(value: str, token: str) -> bool:
    return token.casefold() in value.casefold()

def build(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    require(len(raw) == EXPECTED_BYTES, "workbook byte-size mismatch")
    require(git_blob_sha1(raw) == EXPECTED_GIT_BLOB_SHA1, "workbook Git blob SHA-1 mismatch")
    require(zipfile.is_zipfile(path), "workbook is not a valid XLSX/ZIP")

    with zipfile.ZipFile(path) as zf:
        names = safe_zip_names(zf)
        require("xl/workbook.xml" in names, "missing workbook.xml")
        require("xl/_rels/workbook.xml.rels" in names, "missing workbook relationships")
        shared = parse_shared_strings(zf)
        sheets = workbook_sheets(zf)
        require(sheets, "workbook contains no resolved worksheets")

        cells: list[dict[str, Any]] = []
        for sheet_name, sheet_path in sheets:
            require(sheet_path in names, f"worksheet missing: {sheet_path}")
            root = ET.fromstring(zf.read(sheet_path))
            for cell in root.iter():
                if not (cell.tag.endswith("}c") or cell.tag == "c"):
                    continue
                ref = cell.attrib.get("r")
                if not ref:
                    continue
                value = normalize_for_search(cell_value(cell, shared))
                if not value:
                    continue
                cells.append({
                    "sheet": sheet_name,
                    "cell": ref,
                    "row": row_number(ref),
                    "value": value,
                })

    cells.sort(key=lambda x: (x["sheet"], x["row"] if x["row"] is not None else -1, x["cell"]))

    literal_hits: dict[str, list[dict[str, Any]]] = {}
    tokens = {
        "candidate_global_id": CANDIDATE["global_id"],
        "candidate_revit_object_id": CANDIDATE["revit_object_id"],
        "candidate_type_token": CANDIDATE["type_token"],
        "candidate_material_name": CANDIDATE["material_name"],
        "literal_C25_30": "C25/30",
        "literal_C30_37": "C30/37",
    }
    for key, token in tokens.items():
        literal_hits[key] = [
            {"sheet": c["sheet"], "cell": c["cell"], "row": c["row"], "value": c["value"]}
            for c in cells if exact_contains(c["value"], token)
        ]

    strength_hits: list[dict[str, Any]] = []
    for c in cells:
        for m in STRENGTH_RE.finditer(c["value"]):
            strength_hits.append({
                "sheet": c["sheet"],
                "cell": c["cell"],
                "row": c["row"],
                "value": c["value"],
                "matched_lexical": m.group(0),
                "normalized_class": f"C{m.group(1)}/{m.group(2)}",
            })
    strength_hits.sort(key=lambda x: (x["sheet"], x["row"] if x["row"] is not None else -1, x["cell"], x["normalized_class"]))

    candidate_rows: set[tuple[str, int | None]] = set()
    for key in ("candidate_global_id", "candidate_revit_object_id"):
        for hit in literal_hits[key]:
            candidate_rows.add((hit["sheet"], hit["row"]))
    candidate_bound_strength = [
        hit for hit in strength_hits
        if (hit["sheet"], hit["row"]) in candidate_rows
    ]

    if candidate_bound_strength:
        state = STATE_BOUND
    elif strength_hits:
        state = STATE_UNBOUND
    else:
        state = STATE_ABSENT

    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridDigitalHubAuthoritativeWorkbookMaterialSpecDiscovery",
        "verdict": VERDICT,
        "discovery_state": state,
        "source": {
            "upstream_repository": "RWTH-E3D/DigitalHub",
            "upstream_commit": UPSTREAM_COMMIT,
            "upstream_path": UPSTREAM_PATH,
            "git_blob_sha1": EXPECTED_GIT_BLOB_SHA1,
            "size_bytes": EXPECTED_BYTES,
            "file_sha256": sha256(raw),
            "license_context": "MIT repository license inherited from accepted v3.0 source provenance",
        },
        "candidate": CANDIDATE,
        "workbook": {
            "sheet_count": len(sheets),
            "sheet_names": [name for name, _ in sheets],
            "nonempty_cell_count": len(cells),
        },
        "literal_hits": literal_hits,
        "strength_class_hits": strength_hits,
        "candidate_bound_strength_class_hits": candidate_bound_strength,
        "candidate_binding_rule": {
            "binding_authority": "EXACT_GLOBAL_ID_OR_REVIT_OBJECT_ID_SAME_WORKBOOK_ROW",
            "candidate_rows": [
                {"sheet": s, "row": r} for s, r in sorted(candidate_rows, key=lambda x: (x[0], x[1] if x[1] is not None else -1))
            ],
            "type_or_material_name_alone_is_binding_authority": False,
        },
        "authority_boundaries": {
            "fuzzy_matching": False,
            "strength_class_inferred": False,
            "ifc_environmental_mapping_performed": False,
            "impact_calculation_performed": False,
            "scientific_suitability_decided": False,
            "professional_review_performed": False,
            "certified": False,
        },
    }
    record["integrity"] = {
        "content_sha256": sha256(cbytes(record)),
        "canonicalization": CANON,
        "signature": None,
    }
    return record

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        r = build(a.xlsx)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(pbytes(r))
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print("RESULT=" + r["verdict"])
    print("DISCOVERY_STATE=" + r["discovery_state"])
    print("WORKBOOK_SHA256=" + r["source"]["file_sha256"])
    print("SHEETS=" + ",".join(r["workbook"]["sheet_names"]))
    print("STRENGTH_CLASS_HITS=" + str(len(r["strength_class_hits"])))
    print("CANDIDATE_BOUND_STRENGTH_HITS=" + str(len(r["candidate_bound_strength_class_hits"])))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
