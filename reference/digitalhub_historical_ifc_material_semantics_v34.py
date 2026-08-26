#!/usr/bin/env python3
"""ProofGrid v3.4 historical DigitalHub IFC material-semantics discovery."""
from __future__ import annotations

import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

UPSTREAM_COMMIT = "36565d529b4dadeca625de2b793d7e16700171e9"
SOURCES = {
    "arc_v1": {
        "path": "Version_1/FM_ARC_DigitalHub_v1.ifc",
        "size": 14322717,
        "git_blob_sha1": "8fd67fe7f5fa45c76d4d43170f2bf9df99b8978b",
    },
    "arc_with_sb_v1": {
        "path": "Version_1/FM_ARC_DigitalHub_with_SB_v1.ifc",
        "size": 17621384,
        "git_blob_sha1": "f97213907f912a7703bd3833a624a00e4516e5fd",
    },
}
CANDIDATE = {
    "global_id": "3BmeJtEDj3AQO77Os2w7Ny",
    "revit_object_id": "2395272",
    "type_token": "STB 250 x 400",
    "material_name": "Ortbeton - bewehrt",
}
STRENGTH_RE = re.compile(r"(?<![A-Z0-9])C\s*(\d{2})\s*/\s*(\d{2})(?![0-9])", re.I)
VERDICT = "DIGITALHUB_HISTORICAL_IFC_MATERIAL_SEMANTICS_DISCOVERY_VERIFIABLE"
STATE_BOUND = "HISTORICAL_IFC_MATERIAL_SEMANTICS_FOUND_CANDIDATE_BOUND"
STATE_UNBOUND = "HISTORICAL_IFC_MATERIAL_SEMANTICS_FOUND_NOT_CANDIDATE_BOUND"
STATE_ABSENT = "HISTORICAL_IFC_MATERIAL_SEMANTICS_NOT_FOUND"
CANON = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"

class DiscoveryError(ValueError): pass

def require(c: bool, m: str) -> None:
    if not c: raise DiscoveryError(m)

def cbytes(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def pbytes(v: Any) -> bytes:
    return (json.dumps(v, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def git_blob_sha1(b: bytes) -> str:
    return hashlib.sha1(f"blob {len(b)}\0".encode("ascii") + b).hexdigest()

def scan_one(key: str, path: Path) -> dict[str, Any]:
    meta = SOURCES[key]
    raw = path.read_bytes()
    require(len(raw) == meta["size"], f"{key} size mismatch")
    require(git_blob_sha1(raw) == meta["git_blob_sha1"], f"{key} Git blob mismatch")
    try: text = raw.decode("utf-8")
    except UnicodeDecodeError as exc: raise DiscoveryError(f"{key} is not UTF-8 IFC text") from exc

    token_defs = {
        "candidate_global_id": CANDIDATE["global_id"],
        "candidate_revit_object_id": CANDIDATE["revit_object_id"],
        "candidate_type_token": CANDIDATE["type_token"],
        "candidate_material_name": CANDIDATE["material_name"],
        "literal_C25_30": "C25/30",
        "literal_C30_37": "C30/37",
    }
    exact_hits = {k: [] for k in token_defs}
    strength_hits = []
    candidate_bound_strength = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        step = re.match(r"\s*#(\d+)\s*=", line)
        step_id = int(step.group(1)) if step else None
        line_has_candidate_id = (
            CANDIDATE["global_id"].casefold() in line.casefold()
            or CANDIDATE["revit_object_id"].casefold() in line.casefold()
        )
        for name, token in token_defs.items():
            if token.casefold() in line.casefold():
                exact_hits[name].append({"line_number": line_no, "step_id": step_id, "source_line_sha256": sha256(line.encode("utf-8"))})
        for m in STRENGTH_RE.finditer(line):
            hit = {
                "line_number": line_no,
                "step_id": step_id,
                "matched_lexical": m.group(0),
                "normalized_class": f"C{m.group(1)}/{m.group(2)}",
                "source_line_sha256": sha256(line.encode("utf-8")),
            }
            strength_hits.append(hit)
            if line_has_candidate_id:
                candidate_bound_strength.append(hit)

    strength_hits.sort(key=lambda x: (x["line_number"], x["normalized_class"], x["matched_lexical"]))
    candidate_bound_strength.sort(key=lambda x: (x["line_number"], x["normalized_class"]))
    return {
        "upstream_path": meta["path"],
        "size_bytes": meta["size"],
        "git_blob_sha1": meta["git_blob_sha1"],
        "file_sha256": sha256(raw),
        "exact_token_hits": exact_hits,
        "strength_class_hits": strength_hits,
        "literal_strength_classes": sorted({h["normalized_class"] for h in strength_hits}),
        "candidate_bound_strength_class_hits": candidate_bound_strength,
    }

def build(arc: Path, arc_with_sb: Path) -> dict[str, Any]:
    scans = {"arc_v1": scan_one("arc_v1", arc), "arc_with_sb_v1": scan_one("arc_with_sb_v1", arc_with_sb)}
    all_strength = [h for s in scans.values() for h in s["strength_class_hits"]]
    all_bound = [h for s in scans.values() for h in s["candidate_bound_strength_class_hits"]]
    if all_bound: state = STATE_BOUND
    elif all_strength: state = STATE_UNBOUND
    else: state = STATE_ABSENT
    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridDigitalHubHistoricalIFCMaterialSemanticsDiscovery",
        "verdict": VERDICT,
        "discovery_state": state,
        "upstream_repository": "RWTH-E3D/DigitalHub",
        "upstream_commit": UPSTREAM_COMMIT,
        "candidate_from_accepted_v2": CANDIDATE,
        "historical_sources": scans,
        "combined": {
            "strength_class_hit_count": len(all_strength),
            "candidate_bound_strength_class_hit_count": len(all_bound),
            "literal_strength_classes": sorted({h["normalized_class"] for h in all_strength}),
        },
        "historical_authority_boundary": {
            "historical_source_may_override_accepted_v2_source": False,
            "candidate_binding_requires_exact_v2_global_id_or_object_id_same_line": True,
            "type_or_material_name_alone_is_binding_authority": False,
            "fuzzy_matching": False,
            "strength_class_inferred": False,
            "ifc_environmental_mapping_performed": False,
            "impact_calculation_performed": False,
            "scientific_suitability_decided": False,
            "certified": False,
        },
    }
    record["integrity"] = {"content_sha256": sha256(cbytes(record)), "canonicalization": CANON, "signature": None}
    return record

def main(argv=None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--arc", type=Path, required=True); p.add_argument("--arc-with-sb", type=Path, required=True); p.add_argument("--output", type=Path, required=True); a = p.parse_args(argv)
    try:
        r = build(a.arc, a.arc_with_sb); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_bytes(pbytes(r))
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr); return 2
    print("RESULT=" + r["verdict"]); print("DISCOVERY_STATE=" + r["discovery_state"]); print("STRENGTH_HITS=" + str(r["combined"]["strength_class_hit_count"])); print("CANDIDATE_BOUND_STRENGTH_HITS=" + str(r["combined"]["candidate_bound_strength_class_hit_count"])); print("CLASSES=" + ",".join(r["combined"]["literal_strength_classes"])); return 0

if __name__ == "__main__": raise SystemExit(main())
