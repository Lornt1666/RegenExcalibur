#!/usr/bin/env python3
"""ProofGrid v2.2 declared evidence-scope coverage ledger.

This layer verifies that the exact two semantic members declared by a bounded
synthetic scope manifest are present exactly once in the accepted v1.9
contribution set and remain bound to the accepted v2.1 RXEP partial aggregate.

It does not evaluate or claim whole-building completeness and performs no new
environmental aggregation arithmetic.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ENGINE_NAME = "RegenExcalibur ProofGrid Declared Evidence Scope Coverage Ledger"
ENGINE_VERSION = "2.2.0"
VERDICT = "DECLARED_EVIDENCE_SCOPE_COVERAGE_VERIFIABLE"
ZERO_DIGEST = "0" * 64
CANONICALIZATION = "UTF-8 JSON; sorted keys; compact separators; ensure_ascii=false"

EXPECTED_V19 = {
    "record_content": "f2d790e499da25204877817b8d396a335be9dbc60e118fb4bf2f61009c289a8b",
    "record_file": "427150971842dbd1dd4d1deb87c762abb366bb3c9d56986453bec70d6ad6357b",
    "receipt": "1f1d0b7ffae6caebf3c43201f277bc3997c28112095e9e99fb8208bc77e2fa9e",
    "receipt_file": "8ab034122a244c9a8974b44ae8d84e3170c81b5d92c6d74b660059c950e3a797",
}
EXPECTED_V21 = {
    "record_content": "9826ae5517b0412b9bc2b1c6f8313a123138f55574d6f34e92eeb7129cc26524",
    "record_file": "d9635057c4f55e1d08258b50d784e6f5b58894126953e6ebe9ff564a1a05d1f7",
    "receipt": "aaa309c6622db57a6ec6432af45c2a13affc08c129da72a89e403a7b623215c2",
    "receipt_file": "68d49e3ae9067827afd436279e109305d5775ca59b404d0fe4cc5421e82e117d",
}
EXPECTED_MEMBERS = {
    "75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950": "1CXL7DJx51bvggyIPU2Xi6",
    "b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc": "1BXL7DJx51bvggyIPU2Xi5",
}


class CoverageError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise CoverageError(f"missing required file: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value, raw


def verify_self_hash(record: dict[str, Any], label: str) -> str:
    integrity = record.get("integrity")
    require(isinstance(integrity, dict), f"{label} missing integrity")
    claimed = integrity.get("content_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing content SHA-256")
    shadow = copy.deepcopy(record)
    shadow["integrity"]["content_sha256"] = ZERO_DIGEST
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, f"{label} content hash mismatch")
    return claimed


def verify_receipt_digest(receipt: dict[str, Any], label: str) -> str:
    claimed = receipt.get("receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, f"{label} missing receipt SHA-256")
    shadow = copy.deepcopy(receipt)
    shadow.pop("receipt_sha256", None)
    require(sha256_bytes(canonical_json_bytes(shadow)) == claimed, f"{label} receipt hash mismatch")
    return claimed


def verify_manifest(manifest: dict[str, Any]) -> None:
    require(manifest.get("schema_version") == "1.0" and manifest.get("manifest_version") == "2.2.0", "manifest version mismatch")
    require(manifest.get("scope_type") == "DECLARED_SYNTHETIC_EVIDENCE_SCOPE", "scope type mismatch")
    require(manifest.get("declared_scope_defined") is True, "declared scope missing")
    require(manifest.get("whole_building_scope") is False, "whole-building scope promotion rejected")
    require(manifest.get("expected_member_count") == 2, "expected member count mismatch")
    require(manifest.get("missing_evidence_as_zero") is False, "missing-as-zero rejected")
    members = manifest.get("expected_members")
    require(isinstance(members, list) and len(members) == 2, "expected member list mismatch")
    identity_map = {m.get("semantic_identity_sha256"): m.get("element_global_id") for m in members}
    require(len(identity_map) == 2 and identity_map == EXPECTED_MEMBERS, "manifest semantic/element identity mismatch")
    require(isinstance(manifest.get("exclusions_and_unknowns"), list) and len(manifest["exclusions_and_unknowns"]) >= 1, "scope exclusions/unknowns required")


def verify_v19(record: dict[str, Any], raw: bytes, receipt: dict[str, Any], receipt_raw: bytes) -> dict[str, str]:
    require(record.get("verdict") == "ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE", "v1.9 verdict mismatch")
    content = verify_self_hash(record, "v1.9 set")
    require(content == EXPECTED_V19["record_content"] and sha256_bytes(raw) == EXPECTED_V19["record_file"], "unaccepted v1.9 set")
    receipt_sha = verify_receipt_digest(receipt, "v1.9 set receipt")
    require(receipt_sha == EXPECTED_V19["receipt"] and sha256_bytes(receipt_raw) == EXPECTED_V19["receipt_file"], "unaccepted v1.9 receipt")
    require(receipt.get("record_content_sha256") == content and receipt.get("record_file_sha256") == EXPECTED_V19["record_file"], "v1.9 receipt binding mismatch")
    require(record.get("member_count") == 2 and record.get("completeness_status") == "PARTIAL", "v1.9 set state mismatch")
    require(record.get("aggregation_performed") is False and record.get("sum_performed") is False, "v1.9 aggregation promotion rejected")
    require(record.get("missing_contributions_are_zero") is False and record.get("missing_modules_are_zero") is False, "v1.9 missing-as-zero rejected")
    actual = {m["semantic_identity_sha256"]: m["semantic_identity"]["element_global_id"] for m in record["members"]}
    require(actual == EXPECTED_MEMBERS, "v1.9 semantic/element identity mismatch")
    return actual


def verify_v21(record: dict[str, Any], raw: bytes, receipt: dict[str, Any], receipt_raw: bytes) -> str:
    require(record.get("id", "").startswith("rxep:v21:partial-aggregate:"), "v2.1 RXEP identity mismatch")
    content = verify_self_hash(record, "v2.1 RXEP")
    require(content == EXPECTED_V21["record_content"] and sha256_bytes(raw) == EXPECTED_V21["record_file"], "unaccepted v2.1 RXEP")
    receipt_sha = verify_receipt_digest(receipt, "v2.1 receipt")
    require(receipt_sha == EXPECTED_V21["receipt"] and sha256_bytes(receipt_raw) == EXPECTED_V21["receipt_file"], "unaccepted v2.1 receipt")
    require(receipt.get("record_content_sha256") == content and receipt.get("record_file_sha256") == EXPECTED_V21["record_file"], "v2.1 receipt binding mismatch")
    require(record.get("completeness_status") == "PARTIAL", "v2.1 completeness promotion rejected")
    require(record.get("whole_building_lca_claimed") is False and record.get("declared_scope_complete_claimed") is False, "v2.1 completeness claim promotion rejected")
    require(record.get("member_count") == 2 and record.get("member_semantic_identity_sha256") == list(EXPECTED_MEMBERS.keys()), "v2.1 member identity mismatch")
    require(record.get("missing_contributions_are_zero") is False and record.get("missing_modules_are_zero") is False, "v2.1 missing-as-zero rejected")
    return record["measurement"]["value_decimal"]


def build_coverage(manifest: dict[str, Any], v19: dict[str, Any], v19_raw: bytes, v19_receipt: dict[str, Any], v19_receipt_raw: bytes, v21: dict[str, Any], v21_raw: bytes, v21_receipt: dict[str, Any], v21_receipt_raw: bytes) -> dict[str, Any]:
    verify_manifest(manifest)
    actual = verify_v19(v19, v19_raw, v19_receipt, v19_receipt_raw)
    total = verify_v21(v21, v21_raw, v21_receipt, v21_receipt_raw)
    expected = set(EXPECTED_MEMBERS)
    present = set(actual)
    missing = sorted(expected - present)
    extra = sorted(present - expected)
    require(not missing, f"missing declared-scope members: {missing}")
    require(not extra, f"extra undeclared members: {extra}")

    members = [
        {
            "semantic_identity_sha256": key,
            "element_global_id": EXPECTED_MEMBERS[key],
            "coverage_status": "COVERED",
        }
        for key in sorted(EXPECTED_MEMBERS)
    ]

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredEvidenceScopeCoverageLedger",
        "verdict": VERDICT,
        "scope": {
            "scope_id": manifest["scope_id"],
            "scope_type": manifest["scope_type"],
            "declared_scope_defined": True,
            "whole_building_scope": False,
            "expected_member_count": 2,
            "exclusions_and_unknowns": manifest["exclusions_and_unknowns"],
        },
        "coverage": {
            "declared_scope_coverage_status": "COVERED",
            "covered_member_count": 2,
            "uncovered_member_count": 0,
            "declared_scope_coverage_fraction_decimal": "1",
            "members": members,
        },
        "bound_partial_aggregate": {
            "rxep_record_content_sha256": EXPECTED_V21["record_content"],
            "value_decimal": total,
            "unit": v21["measurement"]["unit"],
            "completeness_status": "PARTIAL",
        },
        "whole_building_completeness_evaluated": False,
        "whole_building_lca_claimed": False,
        "declared_scope_complete_claimed": False,
        "missing_contributions_are_zero": False,
        "missing_modules_are_zero": False,
        "aggregation_recomputed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": [
            "COVERED applies only to the two-member declared synthetic evidence scope.",
            "Whole-building completeness, unmodeled elements/materials/systems, and unlisted lifecycle modules remain unevaluated.",
            "No missing evidence is treated as zero and the v2.1 aggregate is not recomputed by this layer.",
        ],
        "integrity": {"content_sha256": ZERO_DIGEST, "canonicalization": CANONICALIZATION, "signature": None},
    }
    record["integrity"]["content_sha256"] = sha256_bytes(canonical_json_bytes(record))
    return record


def write_outputs(record: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "declared-evidence-scope-coverage.json"
    receipt_path = output_dir / "declared-evidence-scope-coverage-receipt.json"
    record_bytes = pretty_json_bytes(record)
    record_path.write_bytes(record_bytes)
    receipt: dict[str, Any] = {
        "verdict": VERDICT,
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "scope_id": record["scope"]["scope_id"],
        "declared_scope_coverage_status": "COVERED",
        "covered_member_count": 2,
        "uncovered_member_count": 0,
        "declared_scope_coverage_fraction_decimal": "1",
        "whole_building_scope": False,
        "whole_building_completeness_evaluated": False,
        "whole_building_lca_claimed": False,
        "declared_scope_complete_claimed": False,
        "missing_contributions_are_zero": False,
        "aggregation_recomputed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    receipt_bytes = pretty_json_bytes(receipt)
    receipt_path.write_bytes(receipt_bytes)
    return {
        "record": str(record_path),
        "receipt": str(receipt_path),
        "record_content_sha256": record["integrity"]["content_sha256"],
        "record_file_sha256": sha256_bytes(record_bytes),
        "receipt_sha256": receipt["receipt_sha256"],
        "receipt_file_sha256": sha256_bytes(receipt_bytes),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--v19-set", type=Path, required=True)
    parser.add_argument("--v19-receipt", type=Path, required=True)
    parser.add_argument("--v21-rxep", type=Path, required=True)
    parser.add_argument("--v21-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest, _ = load_json(args.manifest)
        v19, v19_raw = load_json(args.v19_set)
        v19_receipt, v19_receipt_raw = load_json(args.v19_receipt)
        v21, v21_raw = load_json(args.v21_rxep)
        v21_receipt, v21_receipt_raw = load_json(args.v21_receipt)
        record = build_coverage(manifest, v19, v19_raw, v19_receipt, v19_receipt_raw, v21, v21_raw, v21_receipt, v21_receipt_raw)
        outputs = write_outputs(record, args.output_dir)
    except CoverageError as exc:
        print("FAILED:", exc)
        return 2
    print("RESULT:", VERDICT)
    print("DECLARED_SCOPE_COVERAGE=COVERED")
    print("WHOLE_BUILDING_COMPLETENESS_EVALUATED=false")
    print(json.dumps(outputs, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
