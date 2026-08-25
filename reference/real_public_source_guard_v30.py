#!/usr/bin/env python3
"""ProofGrid v3.0 exact public-real-IFC source guard.

This guard runs before the model inventory engine. It binds an immutable public
source manifest to exact IFC bytes, exact license bytes, their SHA-256 digests,
and Git blob identities, then emits the USER_AUTHORIZED_REAL_IFC authorization
record consumed by model_inventory_v30.

It never treats a public model as the user's own project and never upgrades
model-inventory closure into LCA/scientific/professional/certification claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
AUTH_SCHEMA = ROOT / "schemas" / "model-source-authorization-v30.schema.json"
VERDICT = "V30_REAL_PUBLIC_SOURCE_GUARD_VERIFIABLE"


class SourceGuardError(ValueError):
    pass


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SourceGuardError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_blob_sha1(value: bytes) -> str:
    header = f"blob {len(value)}\0".encode("ascii")
    return hashlib.sha1(header + value).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceGuardError(f"invalid manifest JSON: {exc}") from exc
    require(isinstance(value, dict), "source manifest must be a JSON object")
    return value, raw


def validate_manifest_structure(manifest: dict[str, Any]) -> None:
    require(manifest.get("schema_version") == "1.0", "source manifest schema version mismatch")
    require(manifest.get("manifest_version") == "3.0.0", "source manifest version mismatch")
    require(manifest.get("source_role") == "PUBLIC_OPEN_REAL_IFC_CONTROL", "source role mismatch")
    require(manifest.get("source_is_user_project") is False, "public control cannot be represented as the user's project")
    require(manifest.get("source_sha256_state") == "FROZEN", "source SHA-256 must be frozen before production admission")

    upstream = manifest.get("upstream")
    require(isinstance(upstream, dict), "source manifest upstream block missing")
    for key in ("repository", "commit", "path", "git_blob_sha1", "size_bytes", "source_sha256", "raw_url"):
        require(upstream.get(key) not in (None, ""), f"source manifest upstream.{key} missing")
    require(str(upstream["path"]).lower().endswith(".ifc"), "source path must be native .ifc")
    require(isinstance(upstream["size_bytes"], int) and upstream["size_bytes"] > 0, "source size must be positive integer")
    require(len(str(upstream["git_blob_sha1"])) == 40, "source Git blob SHA-1 must be 40 hex chars")
    require(len(str(upstream["source_sha256"])) == 64, "source SHA-256 must be 64 hex chars")

    license_block = manifest.get("license")
    require(isinstance(license_block, dict), "source manifest license block missing")
    require(license_block.get("spdx") == "MIT", "v3.0 public control currently requires MIT license")
    for key in ("path", "git_blob_sha1", "license_sha256", "raw_url", "copyright"):
        require(license_block.get(key) not in (None, ""), f"source manifest license.{key} missing")
    require(len(str(license_block["git_blob_sha1"])) == 40, "license Git blob SHA-1 must be 40 hex chars")
    require(len(str(license_block["license_sha256"])) == 64, "license SHA-256 must be 64 hex chars")

    authorization = manifest.get("analysis_authorization")
    require(isinstance(authorization, dict), "analysis authorization block missing")
    require(authorization.get("authorized_purpose") == "ProofGrid v3.0 authoritative model inventory basis", "authorized purpose mismatch")
    require(authorization.get("public_license_required") is True, "public license requirement missing")
    require(authorization.get("publication_of_user_private_model_authorized") is False, "private-model publication cannot be implied")
    require(isinstance(authorization.get("user_directive_reference"), str) and authorization["user_directive_reference"], "user directive reference missing")


def verify_source(manifest: dict[str, Any], manifest_raw: bytes, ifc_bytes: bytes, license_bytes: bytes) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_manifest_structure(manifest)
    upstream = manifest["upstream"]
    license_block = manifest["license"]

    source_sha = sha256_bytes(ifc_bytes)
    license_sha = sha256_bytes(license_bytes)
    manifest_sha = sha256_bytes(manifest_raw)

    require(len(ifc_bytes) == upstream["size_bytes"], "IFC source byte size mismatch")
    require(source_sha == upstream["source_sha256"], "IFC source SHA-256 mismatch")
    require(git_blob_sha1(ifc_bytes) == upstream["git_blob_sha1"], "IFC source Git blob identity mismatch")
    require(license_sha == license_block["license_sha256"], "license SHA-256 mismatch")
    require(git_blob_sha1(license_bytes) == license_block["git_blob_sha1"], "license Git blob identity mismatch")

    license_text = license_bytes.decode("utf-8")
    require("MIT License" in license_text, "MIT license marker missing")
    require(str(license_block["copyright"]) in license_text, "expected copyright notice missing from license")

    provenance = {
        "schema_version": "1.0",
        "verdict": VERDICT,
        "source_name": manifest["source_name"],
        "source_role": manifest["source_role"],
        "source_is_user_project": False,
        "upstream_repository": upstream["repository"],
        "upstream_commit": upstream["commit"],
        "upstream_path": upstream["path"],
        "upstream_git_blob_sha1": upstream["git_blob_sha1"],
        "source_size_bytes": len(ifc_bytes),
        "source_sha256": source_sha,
        "license_spdx": license_block["spdx"],
        "license_git_blob_sha1": license_block["git_blob_sha1"],
        "license_sha256": license_sha,
        "source_manifest_sha256": manifest_sha,
        "synthetic": False,
        "reconstructed": False,
        "publication_of_user_private_model_authorized": False,
    }

    directive = manifest["analysis_authorization"]["user_directive_reference"]
    auth = {
        "authorization_reference": (
            f"github-public-source://{upstream['repository']}@{upstream['commit']}/{upstream['path']}"
            f"?source_sha256={source_sha}&license_sha256={license_sha}&manifest_sha256={manifest_sha}"
            f";user-directive={directive}"
        ),
        "authorization_version": "3.0.0",
        "authorized_purpose": "ProofGrid v3.0 authoritative model inventory basis",
        "notes": [
            "User explicitly authorized removing blockers and proceeding with an openly licensed public real IFC control.",
            f"Exact source is {manifest['source_name']} at the immutable upstream commit/path/blob.",
            "MIT license is verified from the same immutable upstream commit.",
            "Authorization binds exact IFC SHA-256, license SHA-256, and source-manifest SHA-256.",
            "This public model is not claimed to be the user's own project model.",
        ],
        "reconstructed": False,
        "schema_version": "1.0",
        "source_classification": "USER_AUTHORIZED_REAL_IFC",
        "synthetic": False,
        "user_authorized": True,
    }

    schema = json.loads(AUTH_SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(auth))
    require(not errors, "generated source authorization failed schema validation")

    receipt = {
        "verdict": VERDICT,
        "source_sha256": source_sha,
        "source_git_blob_sha1": upstream["git_blob_sha1"],
        "license_sha256": license_sha,
        "license_git_blob_sha1": license_block["git_blob_sha1"],
        "source_manifest_sha256": manifest_sha,
        "authorization_sha256": sha256_bytes(pretty_json_bytes(auth)),
        "source_byte_identity_verified": True,
        "license_identity_verified": True,
        "user_analysis_authorization_bound": True,
        "source_is_user_project": False,
        "synthetic": False,
        "reconstructed": False,
        "certified": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    return provenance, auth, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ifc", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest, manifest_raw = load_json(args.manifest)
        provenance, auth, receipt = verify_source(manifest, manifest_raw, args.ifc.read_bytes(), args.license.read_bytes())
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "source-provenance.json").write_bytes(pretty_json_bytes(provenance))
        (args.output_dir / "authorization.json").write_bytes(pretty_json_bytes(auth))
        (args.output_dir / "source-guard-receipt.json").write_bytes(pretty_json_bytes(receipt))
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 2
    print(f"RESULT: {VERDICT}")
    print(f"SOURCE_SHA256={provenance['source_sha256']}")
    print(f"LICENSE_SHA256={provenance['license_sha256']}")
    print(f"SOURCE_MANIFEST_SHA256={provenance['source_manifest_sha256']}")
    print(f"AUTHORIZATION_SHA256={receipt['authorization_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
