#!/usr/bin/env python3
"""ProofGrid v2.3 declared synthetic source inventory and uncovered-evidence ledger.

This gate inventories exactly three synthetic source entries:
- two already accepted evidence-covered IFC elements from v1.9;
- one deterministic synthetic IFC element with no accepted environmental contribution.

It does not evaluate whole-building/model completeness and never treats uncovered
inventory as zero impact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ENGINE_NAME = "RegenExcalibur ProofGrid Declared Source Inventory Gap Ledger"
ENGINE_VERSION = "2.3.0"
VERDICT = "DECLARED_SOURCE_INVENTORY_GAP_LEDGER_VERIFIABLE"
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"
ZERO = "0" * 64

V22 = {
    "content": "0604632912bdf489cb9cc443c536e35da357a062084d21204929d64a75ad4f35",
    "file": "cc515d82768a05da3dbb67fa769d071576e5305ff18d453022dc093739793162",
    "receipt": "797d139327467952b796943a35f0da0273ece1da2a1381c7084608a1bb7b7e8c",
    "receipt_file": "e7d5c4eeae93357b98721f59ba71091f2eab93c5015d94dcfabd068d92e3b8ae",
    "comparison": "324ddd9ae3997b94fd996fa070fa6cdbfab4f0052aa3bfe5a91f847e2ed847ec",
    "comparison_file": "e76323d67f7a29ca980ec07d6fd1843b9b62e41c1345e9868f59653744fd342e",
}
V19 = {
    "content": "f2d790e499da25204877817b8d396a335be9dbc60e118fb4bf2f61009c289a8b",
    "file": "427150971842dbd1dd4d1deb87c762abb366bb3c9d56986453bec70d6ad6357b",
    "receipt": "1f1d0b7ffae6caebf3c43201f277bc3997c28112095e9e99fb8208bc77e2fa9e",
    "receipt_file": "8ab034122a244c9a8974b44ae8d84e3170c81b5d92c6d74b660059c950e3a797",
}
COVERED = [
    {
        "inventory_entry_id": "covered-first",
        "element_global_id": "1BXL7DJx51bvggyIPU2Xi5",
        "ifc_source_sha256": "23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6",
        "semantic_identity_sha256": "b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc",
    },
    {
        "inventory_entry_id": "covered-second",
        "element_global_id": "1CXL7DJx51bvggyIPU2Xi6",
        "ifc_source_sha256": "14c4be5561131bd6213d45dd0e00064ac916da28f825450133b5dd48d1fcd54d",
        "semantic_identity_sha256": "75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950",
    },
]
UNCOVERED_GLOBAL_ID = "1DXL7DJx51bvggyIPU2Xi7"


class InventoryGapError(ValueError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise InventoryGapError(msg)


def cbytes(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pbytes(v: Any) -> bytes:
    return (json.dumps(v, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = Path(path).read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    require(isinstance(obj, dict), f"expected object: {path}")
    return obj, raw


def verify_self_hash(record: dict[str, Any], label: str) -> str:
    integ = record.get("integrity")
    require(isinstance(integ, dict), f"{label} missing integrity")
    claimed = integ.get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing content hash")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO
    require(sha(cbytes(shadow)) == claimed, f"{label} content digest mismatch")
    return claimed


def verify_receipt_digest(receipt: dict[str, Any], field: str, label: str) -> str:
    claimed = receipt.get(field)
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing {field}")
    shadow = copy.deepcopy(receipt)
    shadow.pop(field, None)
    require(sha(cbytes(shadow)) == claimed, f"{label} digest mismatch")
    return claimed


def verify_parents(v22, v22_raw, v22r, v22r_raw, v22c, v22c_raw, v19, v19_raw, v19r, v19r_raw) -> None:
    require(v22.get("verdict") == "DECLARED_EVIDENCE_SCOPE_COVERAGE_VERIFIABLE", "wrong v2.2 verdict")
    require(verify_self_hash(v22, "v2.2 ledger") == V22["content"], "unaccepted v2.2 content")
    require(sha(v22_raw) == V22["file"], "unaccepted v2.2 file")
    require(verify_receipt_digest(v22r, "receipt_sha256", "v2.2 receipt") == V22["receipt"], "unaccepted v2.2 receipt")
    require(sha(v22r_raw) == V22["receipt_file"], "unaccepted v2.2 receipt file")
    require(verify_receipt_digest(v22c, "comparison_receipt_sha256", "v2.2 comparison") == V22["comparison"], "unaccepted v2.2 comparison")
    require(sha(v22c_raw) == V22["comparison_file"], "unaccepted v2.2 comparison file")
    require(v22.get("coverage", {}).get("covered_member_count") == 2, "v2.2 covered count mismatch")
    require(v22.get("whole_building_completeness_evaluated") is False, "v2.2 whole-building promotion")

    require(v19.get("verdict") == "ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE", "wrong v1.9 verdict")
    require(verify_self_hash(v19, "v1.9 set") == V19["content"], "unaccepted v1.9 content")
    require(sha(v19_raw) == V19["file"], "unaccepted v1.9 file")
    require(verify_receipt_digest(v19r, "receipt_sha256", "v1.9 receipt") == V19["receipt"], "unaccepted v1.9 receipt")
    require(sha(v19r_raw) == V19["receipt_file"], "unaccepted v1.9 receipt file")
    require(v19.get("member_count") == 2 and v19.get("completeness_status") == "PARTIAL", "v1.9 membership state mismatch")

    indexed = {m["semantic_identity_sha256"]: m for m in v19.get("members", [])}
    v22_indexed = {m["semantic_identity_sha256"]: m for m in v22.get("coverage", {}).get("members", [])}
    for expected in COVERED:
        sid = expected["semantic_identity_sha256"]
        require(sid in indexed, f"missing accepted v1.9 semantic identity: {sid}")
        ident = indexed[sid].get("semantic_identity", {})
        require(ident.get("element_global_id") == expected["element_global_id"], "covered element mismatch")
        require(ident.get("ifc_source_sha256") == expected["ifc_source_sha256"], "covered source mismatch")
        require(sid in v22_indexed and v22_indexed[sid].get("element_global_id") == expected["element_global_id"], "v2.2 coverage binding mismatch")


def build_uncovered_ifc(path: Path) -> None:
    import ifcopenshell  # type: ignore
    model = ifcopenshell.file(schema="IFC4")
    project = model.create_entity("IfcProject", GlobalId="0jS$wWKLjAuhSPZ5IG0yTy", Name="ProofGrid v2.3 inventory-only source")
    wall = model.create_entity("IfcWall", GlobalId=UNCOVERED_GLOBAL_ID, Name="Uncovered Inventory Wall")
    model.create_entity("IfcRelAggregates", GlobalId="2DXL7DJx51bvggyIPU2Xi8", RelatingObject=project, RelatedObjects=[wall])
    model.write(str(path))
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(
        r"FILE_NAME\('[^']*','[^']*'",
        "FILE_NAME('proofgrid-v23-uncovered.ifc','2026-01-01T00:00:00'",
        text,
        count=1,
    )
    require(count == 1, "failed to canonicalize IFC FILE_NAME header")
    path.write_text(text, encoding="utf-8", newline="\n")


def verify_uncovered_ifc(path: Path) -> str:
    import ifcopenshell  # type: ignore
    raw = path.read_bytes()
    model = ifcopenshell.open(str(path))
    walls = [w for w in model.by_type("IfcWall") if getattr(w, "GlobalId", None) == UNCOVERED_GLOBAL_ID]
    require(len(walls) == 1, "uncovered fixture must contain exactly one expected wall")
    return sha(raw)


def validate_entries(entries: list[dict[str, Any]]) -> None:
    require(len(entries) == 3, "inventory must contain exactly three entries")
    keys = [(e.get("ifc_source_sha256"), e.get("element_global_id")) for e in entries]
    require(len(set(keys)) == 3, "duplicate inventory source/element entry")
    covered = [e for e in entries if e.get("evidence_status") == "EVIDENCE_COVERED"]
    uncovered = [e for e in entries if e.get("evidence_status") == "EVIDENCE_UNCOVERED"]
    require(len(covered) == 2 and len(uncovered) == 1, "expected 2 covered + 1 uncovered")
    accepted_sids = {x["semantic_identity_sha256"] for x in COVERED}
    for e in covered:
        require(e.get("semantic_identity_sha256") in accepted_sids, "covered entry lacks accepted semantic identity")
        require(e.get("assumed_zero") is False, "covered entry cannot use assumed zero")
    u = uncovered[0]
    require(u.get("semantic_identity_sha256") is None, "uncovered entry cannot reuse semantic identity")
    require(u.get("uncovered_reason") == "NO_ACCEPTED_ENVIRONMENTAL_CONTRIBUTION", "wrong uncovered reason")
    require(u.get("assumed_zero") is False, "uncovered entry cannot be treated as zero")


def build_ledger(v22_path: Path, v22_receipt_path: Path, v22_comparison_path: Path, v19_path: Path, v19_receipt_path: Path, uncovered_ifc: Path) -> dict[str, Any]:
    v22, v22_raw = load(v22_path); v22r, v22r_raw = load(v22_receipt_path); v22c, v22c_raw = load(v22_comparison_path)
    v19, v19_raw = load(v19_path); v19r, v19r_raw = load(v19_receipt_path)
    verify_parents(v22, v22_raw, v22r, v22r_raw, v22c, v22c_raw, v19, v19_raw, v19r, v19r_raw)
    uncovered_sha = verify_uncovered_ifc(uncovered_ifc)

    entries = []
    for e in COVERED:
        entries.append({
            **e,
            "evidence_status": "EVIDENCE_COVERED",
            "assumed_zero": False,
            "coverage_source": "ACCEPTED_V1_9_SEMANTIC_CONTRIBUTION",
        })
    entries.append({
        "inventory_entry_id": "uncovered-third",
        "element_global_id": UNCOVERED_GLOBAL_ID,
        "ifc_source_sha256": uncovered_sha,
        "semantic_identity_sha256": None,
        "evidence_status": "EVIDENCE_UNCOVERED",
        "uncovered_reason": "NO_ACCEPTED_ENVIRONMENTAL_CONTRIBUTION",
        "assumed_zero": False,
        "coverage_source": None,
    })
    entries.sort(key=lambda x: (x["ifc_source_sha256"], x["element_global_id"]))
    validate_entries(entries)

    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredSourceInventoryGapLedger",
        "verdict": VERDICT,
        "inventory_scope": {
            "inventory_id": "proofgrid:v23:declared-synthetic-source-inventory",
            "inventory_scope_type": "DECLARED_SYNTHETIC_SOURCE_INVENTORY",
            "inventory_entry_count": 3,
            "whole_building_scope": False,
            "whole_model_inventory_claimed": False,
            "description": "Bounded synthetic inventory for two evidenced elements plus one intentionally uncovered inventory-only element.",
        },
        "coverage": {
            "covered_entry_count": 2,
            "uncovered_entry_count": 1,
            "coverage_ratio_rational": {"numerator": "2", "denominator": "3"},
            "rounded_decimal_coverage_authority_present": False,
        },
        "entries": entries,
        "parent_evidence": {
            "v22_coverage_content_sha256": V22["content"],
            "v22_coverage_receipt_sha256": V22["receipt"],
            "v22_comparison_receipt_sha256": V22["comparison"],
            "v19_set_content_sha256": V19["content"],
            "v19_set_receipt_sha256": V19["receipt"],
        },
        "whole_building_scope": False,
        "whole_model_inventory_claimed": False,
        "whole_building_completeness_evaluated": False,
        "whole_building_lca_claimed": False,
        "missing_contributions_are_zero": False,
        "uncovered_inventory_is_zero": False,
        "aggregation_recomputed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "The declared inventory is a synthetic three-entry control, not a whole-building or whole-model inventory.",
            "The uncovered entry has no accepted environmental contribution and is explicitly not treated as zero impact.",
            "Coverage ratio is represented exactly as 2/3 rational; no rounded Decimal is evidence authority.",
        ],
        "integrity": {"content_sha256": ZERO, "canonicalization": CANONICALIZATION, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha(cbytes(record))
    return record


def make_receipt(record: dict[str, Any], raw: bytes) -> dict[str, Any]:
    uncovered = next(e for e in record["entries"] if e["evidence_status"] == "EVIDENCE_UNCOVERED")
    receipt = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha(raw),
        "inventory_entry_count": 3,
        "covered_entry_count": 2,
        "uncovered_entry_count": 1,
        "coverage_ratio_rational": {"numerator": "2", "denominator": "3"},
        "uncovered_ifc_source_sha256": uncovered["ifc_source_sha256"],
        "uncovered_element_global_id": uncovered["element_global_id"],
        "uncovered_assumed_zero": False,
        "whole_building_completeness_evaluated": False,
        "whole_building_lca_claimed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha(cbytes(receipt))
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-uncovered-ifc"); b.add_argument("--output", type=Path, required=True)
    l = sub.add_parser("ledger")
    for name in ("v22-ledger", "v22-receipt", "v22-comparison", "v19-set", "v19-receipt", "uncovered-ifc", "output-dir"):
        l.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "build-uncovered-ifc":
            a.output.parent.mkdir(parents=True, exist_ok=True); build_uncovered_ifc(a.output)
            print("UNCOVERED_IFC_SHA256=" + sha(a.output.read_bytes()))
            print("UNCOVERED_GLOBAL_ID=" + UNCOVERED_GLOBAL_ID)
            return 0
        record = build_ledger(a.v22_ledger, a.v22_receipt, a.v22_comparison, a.v19_set, a.v19_receipt, a.uncovered_ifc)
        a.output_dir.mkdir(parents=True, exist_ok=True)
        raw = pbytes(record); (a.output_dir / "declared-source-inventory-gap-ledger.json").write_bytes(raw)
        receipt = make_receipt(record, raw); (a.output_dir / "declared-source-inventory-gap-ledger-receipt.json").write_bytes(pbytes(receipt))
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print("FAILED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
