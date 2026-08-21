#!/usr/bin/env python3
"""ProofGrid v0.7 authoritative ILCD+EPD v1.3 XSD/master-data conformance.

This validator proves only the declared software-format gate. It does not claim
validation-profile compliance, scientific validity, professional LCA review,
provider authorization, or certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "conformance" / "ilcd-epd-v13" / "upstream.json"

PROCESS_NS = "http://lca.jrc.it/ILCD/Process"
COMMON_NS = "http://lca.jrc.it/ILCD/Common"
EPD_2013_NS = "http://www.iai.kit.edu/EPD/2013"
EPD_2019_NS = "http://www.indata.network/EPD/2019"
EPD_2024_NS = "http://www.indata.network/EPD/2024"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XML_NS = "http://www.w3.org/XML/1998/namespace"


class ConformanceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConformanceError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_output(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def verify_checkout(repo: Path, expected_commit: str, expected_license: str) -> None:
    require((repo / ".git").exists(), f"upstream checkout is not a git repository: {repo}")
    actual = git_output(repo, "rev-parse", "HEAD")
    require(actual == expected_commit, f"upstream commit mismatch for {repo.name}: expected {expected_commit}, got {actual}")
    license_path = repo / "LICENSE"
    require(license_path.is_file(), f"upstream LICENSE missing: {repo}")
    license_text = license_path.read_text(encoding="utf-8", errors="replace")
    if expected_license == "Apache-2.0":
        require("Apache License" in license_text and "Version 2.0" in license_text, f"Apache-2.0 license evidence missing: {repo}")


def verify_git_blob(repo: Path, relative_path: str, expected_blob_sha: str) -> Path:
    path = repo / relative_path
    require(path.is_file(), f"required upstream file missing: {relative_path}")
    actual_blob = git_output(repo, "hash-object", relative_path)
    require(actual_blob == expected_blob_sha, f"upstream git blob mismatch for {relative_path}: expected {expected_blob_sha}, got {actual_blob}")
    return path


def build_synthetic_fixture(official_example: Path, output_path: Path, fixture: dict[str, Any]) -> None:
    ET.register_namespace("", PROCESS_NS)
    ET.register_namespace("common", COMMON_NS)
    ET.register_namespace("epd", EPD_2013_NS)
    ET.register_namespace("epd2", EPD_2019_NS)
    ET.register_namespace("epd24", EPD_2024_NS)
    ET.register_namespace("xsi", XSI_NS)

    tree = ET.parse(official_example)
    root = tree.getroot()
    require(root.tag == f"{{{PROCESS_NS}}}processDataSet", "official example root is not ILCD Process/processDataSet")
    require(root.attrib.get(f"{{{EPD_2019_NS}}}epd-version") == "1.3", "official example does not declare epd-version 1.3")

    dataset_info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    require(dataset_info is not None, "official example lacks processInformation/dataSetInformation")
    uuid_node = dataset_info.find(f"{{{COMMON_NS}}}UUID")
    require(uuid_node is not None and bool(uuid_node.text), "official example lacks dataset UUID")
    uuid_node.text = str(fixture["uuid"])

    name_node = dataset_info.find(f"{{{PROCESS_NS}}}name")
    require(name_node is not None, "official example lacks dataset name")
    base_names = name_node.findall(f"{{{PROCESS_NS}}}baseName")
    require(bool(base_names), "official example lacks baseName")
    for node in base_names:
        lang = node.attrib.get(f"{{{XML_NS}}}lang")
        if lang == "de":
            node.text = str(fixture["german_name"])
        else:
            node.text = str(fixture["english_name"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)


def parse_dataset_identity(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    dataset_info = root.find(f"{{{PROCESS_NS}}}processInformation/{{{PROCESS_NS}}}dataSetInformation")
    require(dataset_info is not None, "dataset information missing")
    uuid_node = dataset_info.find(f"{{{COMMON_NS}}}UUID")
    require(uuid_node is not None and bool(uuid_node.text), "dataset UUID missing")
    names = []
    name_node = dataset_info.find(f"{{{PROCESS_NS}}}name")
    if name_node is not None:
        for node in name_node.findall(f"{{{PROCESS_NS}}}baseName"):
            names.append({"language": node.attrib.get(f"{{{XML_NS}}}lang"), "value": node.text})
    return {
        "root": root.tag,
        "ilcd_version": root.attrib.get("version"),
        "epd_version": root.attrib.get(f"{{{EPD_2019_NS}}}epd-version"),
        "uuid": uuid_node.text,
        "names": names,
    }


def verify_master_identity(master_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    path = master_root / str(spec["path"])
    require(path.is_file(), f"required authoritative master-data file missing: {spec['path']}")
    root = ET.parse(path).getroot()
    uuid_node = root.find(f".//{{{COMMON_NS}}}UUID")
    require(uuid_node is not None and uuid_node.text == spec["uuid"], f"master-data UUID mismatch for {spec['path']}")
    return {"uuid": uuid_node.text, "path": str(spec["path"]), "sha256": sha256_file(path)}


def validate_v13(format_root: Path, master_root: Path, output_dir: Path) -> dict[str, Any]:
    try:
        import elementpath  # type: ignore
        import xmlschema  # type: ignore
    except ImportError as exc:
        raise ConformanceError("install requirements-proofgrid-v07.txt") from exc

    manifest = load_json(MANIFEST_PATH)
    format_spec = manifest["format"]
    master_spec = manifest["master_data"]
    profile_policy = manifest["profile_policy"]

    require(profile_policy.get("profile_validation_performed") is False, "v1.3 profile validation must remain false while the authoritative profile is unavailable")

    verify_checkout(format_root, str(format_spec["commit"]), str(format_spec["license"]))
    verify_checkout(master_root, str(master_spec["commit"]), str(master_spec["license"]))

    xsd_path = verify_git_blob(format_root, format_spec["xsd"]["path"], format_spec["xsd"]["git_blob_sha"])
    official_example = verify_git_blob(
        format_root,
        format_spec["official_example"]["path"],
        format_spec["official_example"]["git_blob_sha"],
    )
    master_identity = verify_master_identity(master_root, master_spec["required_identity"])

    # Sandbox schema composition to the pinned local schema checkout and always use
    # the safe XML parser. Instance schemaLocation hints are ignored by validate().
    schema = xmlschema.XMLSchema(
        str(xsd_path),
        allow="sandbox",
        defuse="always",
        base_url=str(xsd_path.parent),
    )

    official_resource = xmlschema.XMLResource(
        str(official_example),
        base_url=str(official_example.parent),
        allow="sandbox",
        defuse="always",
    )
    schema.validate(official_resource, use_location_hints=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    synthetic_path = output_dir / "proofgrid-synthetic-ilcd-epd-v1.3.xml"
    build_synthetic_fixture(official_example, synthetic_path, manifest["synthetic_fixture"])
    synthetic_resource = xmlschema.XMLResource(
        str(synthetic_path),
        base_url=str(synthetic_path.parent),
        allow="sandbox",
        defuse="always",
    )
    schema.validate(synthetic_resource, use_location_hints=False)

    official_identity = parse_dataset_identity(official_example)
    synthetic_identity = parse_dataset_identity(synthetic_path)
    require(synthetic_identity["uuid"] == manifest["synthetic_fixture"]["uuid"], "synthetic fixture UUID mismatch")
    require(synthetic_identity["epd_version"] == "1.3", "synthetic fixture lost ILCD+EPD v1.3 declaration")

    receipt: dict[str, Any] = {
        "engine": {
            "name": "RegenExcalibur ProofGrid ILCD+EPD v1.3 Conformance Validator",
            "version": "0.7.0",
        },
        "verdict": "ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT",
        "certified": False,
        "format_conformance": {
            "xsd_validation": True,
            "master_data_identity_validation": True,
            "profile_validation_performed": False,
            "profile_status": "AUTHORITATIVE_V1_3_PROFILE_NOT_AVAILABLE_IN_GATE",
        },
        "upstream": {
            "format": {
                "repository": format_spec["repository"],
                "commit": format_spec["commit"],
                "license": format_spec["license"],
                "xsd": {
                    "path": format_spec["xsd"]["path"],
                    "git_blob_sha": format_spec["xsd"]["git_blob_sha"],
                    "sha256": sha256_file(xsd_path),
                },
                "official_example": {
                    "path": format_spec["official_example"]["path"],
                    "git_blob_sha": format_spec["official_example"]["git_blob_sha"],
                    "sha256": sha256_file(official_example),
                    "identity": official_identity,
                    "xsd_valid": True,
                },
            },
            "master_data": {
                "repository": master_spec["repository"],
                "commit": master_spec["commit"],
                "license": master_spec["license"],
                "resolved_identity": master_identity,
            },
        },
        "synthetic_fixture": {
            "path": synthetic_path.name,
            "sha256": sha256_file(synthetic_path),
            "identity": synthetic_identity,
            "xsd_valid": True,
            "derivation": manifest["synthetic_fixture"]["derivation"],
        },
        "dependencies": {
            "python": ".".join(str(part) for part in sys.version_info[:3]),
            "xmlschema": str(xmlschema.__version__),
            "elementpath": str(elementpath.__version__),
        },
        "security": {
            "schema_resource_access": "sandbox-local-only",
            "xml_defuse": "always",
            "instance_location_hints_used": False,
        },
        "limitations": [
            "This gate proves XML Schema and selected authoritative master-data identity conformance against immutable InData upstream commits only.",
            "InData v1.3 validation profiles are not treated as available in this gate; profile compliance is not claimed.",
            "The local fixture is a deterministic synthetic derivative of the pinned InData Apache-2.0 example and is not a real provider EPD.",
            "Format conformance does not establish scientific validity, product representativeness, professional LCA suitability, provider authorization, or certification.",
            "No code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion is produced.",
        ],
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    (output_dir / "ilcd-epd-v13-conformance-receipt.json").write_bytes(
        (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format-root", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = validate_v13(args.format_root.resolve(), args.master_root.resolve(), args.output_dir.resolve())
    except (ConformanceError, subprocess.CalledProcessError, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: ILCD+EPD v1.3 schema validation failed: {exc}", file=sys.stderr)
        return 2

    print("✓ pinned InData ILCD+EPD v1.3 format commit")
    print("✓ pinned InData master-data commit")
    print("✓ authoritative Apache-2.0 upstream license evidence")
    print("✓ authoritative EPD_DataSet.xsd git object")
    print("✓ official InData v1.3 example XSD validation")
    print("✓ ProofGrid synthetic v1.3 fixture XSD validation")
    print("✓ selected authoritative EN 15804+A2 master-data identity")
    print("✓ sandbox-only schema resolution and defused XML parsing")
    print("PROFILE VALIDATION: NOT PERFORMED")
    print(f"RESULT: {receipt['verdict']}")
    print("NOT CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
