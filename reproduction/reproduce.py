#!/usr/bin/env python3
"""ProofGrid R5 clean-environment reproduction harness.

This harness reproduces the frozen v0.4 implementation in a fresh environment,
checks exact input/evidence/receipt hashes for the synthetic Alberta fixture,
executes both IFC structural ingestion and declared-data extraction, and emits a
machine-readable reproduction receipt.

It does not claim professional, scientific, regulatory, or certification review.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(__file__).resolve().with_name("r5-manifest.json")


class ReproductionError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ReproductionError(f"unable to load JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReproductionError(message)


def _subprocess_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def run(command: list[str], *, cwd: Path = ROOT, echo: bool = True) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=_subprocess_environment(),
    )
    if echo and process.stdout:
        print(process.stdout, end="" if process.stdout.endswith("\n") else "\n")
    if process.returncode != 0:
        if process.stderr:
            print(process.stderr, file=sys.stderr, end="" if process.stderr.endswith("\n") else "\n")
        raise ReproductionError(f"command failed ({process.returncode}): {' '.join(command)}")
    return process


def installed_lock_state(lock_path: Path) -> dict[str, str]:
    installed: dict[str, str] = {}
    for raw in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        require("==" in line, f"unlocked dependency line in {lock_path}: {line}")
        name, expected = line.split("==", 1)
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ReproductionError(f"locked dependency not installed: {name}=={expected}") from exc
        require(actual == expected, f"dependency version mismatch for {name}: expected {expected}, got {actual}")
        installed[name] = actual
    return installed


def git_state(manifest: dict[str, Any]) -> dict[str, Any]:
    git_dir = ROOT / ".git"
    require(git_dir.exists(), "R5 clean-environment gate requires a Git checkout so the frozen implementation commit can be verified")
    implementation_commit = str(manifest["implementation_commit"])
    run(["git", "cat-file", "-e", f"{implementation_commit}^{{commit}}"], echo=False)
    head = run(["git", "rev-parse", "HEAD"], echo=False).stdout.strip()
    command = ["git", "diff", "--exit-code", implementation_commit, "HEAD", "--", *manifest["core_paths"]]
    process = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=_subprocess_environment(),
    )
    if process.returncode != 0:
        detail = process.stdout[-4000:] if process.stdout else process.stderr[-4000:]
        raise ReproductionError(
            "core implementation differs from frozen implementation_commit; reproduction result would not be comparable\n" + detail
        )
    return {
        "implementation_commit": implementation_commit,
        "execution_checkout_sha": head,
        "core_diff_from_implementation_commit": "CLEAN",
    }


def expected_python_for_platform(manifest: dict[str, Any]) -> tuple[str, str]:
    system = platform.system()
    mapping = manifest["runtime"]["python_by_platform"]
    require(system in mapping, f"no exact Python runtime declared for platform {system!r}")
    return system, str(mapping[system])


def verify_inputs(manifest: dict[str, Any]) -> dict[str, str]:
    fixture = ROOT / str(manifest["fixture"])
    hashes: dict[str, str] = {}
    for relative, expected in manifest["expected"]["input_sha256"].items():
        path = fixture / relative
        require(path.is_file(), f"required reproduction input missing: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"input hash mismatch for {relative}: expected {expected}, got {actual}")
        hashes[relative] = actual
    return hashes


def reproduce_environmental(manifest: dict[str, Any], work: Path) -> dict[str, Any]:
    fixture = ROOT / str(manifest["fixture"])
    output = work / "environmental"
    run([sys.executable, "reference/rx_cli.py", "verify", str(fixture), "--output", str(output)])

    evidence = load_json(output / "evidence.json")
    receipt = load_json(output / "receipt.json")
    expected = manifest["expected"]

    require(receipt["project_id"] == expected["project_id"], "project ID does not match reproduction manifest")
    require(receipt["engine"]["version"] == expected["engine_version"], "verifier software version does not match reproduction manifest")
    require(evidence["methodology"]["version"] == expected["method_version"], "calculation method version does not match reproduction manifest")
    require(float(evidence["measurement"]["value"]) == float(expected["total_kgco2e"]), "known-answer GWP changed")
    require(receipt["evidence_content_sha256"] == expected["evidence_content_sha256"], "evidence-content digest mismatch")
    require(receipt["receipt_sha256"] == expected["receipt_sha256"], "RXEP receipt digest mismatch")
    require(receipt["verdict"] == "VERIFIABLE", "environmental result is not VERIFIABLE")
    require(receipt["certified"] is False, "reproduction must not promote the synthetic result to certification")
    require(receipt["lca_registry"]["indicator"] == expected["indicator"], "indicator mismatch")
    require(receipt["lca_registry"]["system_boundary"]["modules"] == expected["system_boundary_modules"], "system-boundary mismatch")

    actual_records = {item["id"]: item["sha256"] for item in receipt["lca_registry"]["source_record_digests"]}
    require(actual_records == expected["source_record_sha256"], "environmental source-record digest set changed")

    receipt_source_hashes = {item["path"]: item["sha256"] for item in receipt["source_hashes"]}
    for path, expected_hash in expected["input_sha256"].items():
        require(receipt_source_hashes.get(path) == expected_hash, f"RXEP receipt source hash mismatch for {path}")

    output_hashes = {
        name: sha256_file(output / name)
        for name in ("evidence.json", "graph.jsonld", "receipt.json", "report.html")
    }
    expected_output_hashes = expected["generated_output_sha256"]
    require(
        output_hashes == expected_output_hashes,
        f"generated environmental artifact hash set changed: expected {expected_output_hashes}, got {output_hashes}",
    )
    return {
        "known_answer_kgco2e": float(evidence["measurement"]["value"]),
        "verdict": receipt["verdict"],
        "certified": receipt["certified"],
        "engine_version": receipt["engine"]["version"],
        "method_version": evidence["methodology"]["version"],
        "evidence_content_sha256": receipt["evidence_content_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "source_record_digests": actual_records,
        "generated_output_sha256": output_hashes,
    }


def build_reproduction_ifc(path: Path) -> None:
    import ifcopenshell
    import ifcopenshell.guid

    model = ifcopenshell.file(schema="IFC4")
    length_unit = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    units = model.create_entity("IfcUnitAssignment", Units=[length_unit])
    project = model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="R5 Reproduction Project", UnitsInContext=units)
    site = model.create_entity("IfcSite", GlobalId=ifcopenshell.guid.new(), Name="R5 Site")
    building = model.create_entity("IfcBuilding", GlobalId=ifcopenshell.guid.new(), Name="R5 Building")
    storey = model.create_entity("IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), Name="R5 Level")
    space = model.create_entity("IfcSpace", GlobalId=ifcopenshell.guid.new(), Name="R5 Room")
    model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=project, RelatedObjects=[site])
    model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=site, RelatedObjects=[building])
    model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=building, RelatedObjects=[storey])
    model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=storey, RelatedObjects=[space])
    wall = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), Name="R5 Wall")
    model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(), RelatedElements=[wall], RelatingStructure=storey)
    material = model.create_entity("IfcMaterial", Name="Concrete")
    model.create_entity("IfcRelAssociatesMaterial", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingMaterial=material)
    quantity = model.create_entity("IfcQuantityLength", Name="Length", LengthValue=3.5)
    qset = model.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_WallBaseQuantities", Quantities=[quantity])
    model.create_entity("IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingPropertyDefinition=qset)
    model.write(str(path))


def reproduce_ifc(manifest: dict[str, Any], work: Path) -> dict[str, Any]:
    ifc_path = work / "reproduction.ifc"
    structural_path = work / "ifc-structural.json"
    extraction_path = work / "ifc-extraction.json"
    build_reproduction_ifc(ifc_path)
    run([sys.executable, "reference/rx_cli.py", "ifc-inspect", str(ifc_path), "--output", str(structural_path)])
    run([sys.executable, "reference/ifc_extract.py", str(ifc_path), "--output", str(extraction_path)])
    structural = load_json(structural_path)
    extraction = load_json(extraction_path)
    expected = manifest["expected"]["ifc"]

    require(str(structural["schema"]).upper().startswith(expected["schema_prefix"]), "IFC structural schema mismatch")
    require(structural["counts"]["projects"] == expected["projects"], "IFC project count mismatch")
    require(structural["counts"]["buildings"] == expected["buildings"], "IFC building count mismatch")
    walls = [item for item in extraction["elements"] if item["ifc_type"] == "IfcWall"]
    require(len(walls) == expected["walls"], "IFC wall count mismatch")
    wall = walls[0]
    require(any(item["name"] == expected["material_name"] for item in wall["materials"]), "IFC material association mismatch")
    quantities = [item for item in wall["quantities"] if item["name"] == expected["declared_quantity_name"]]
    require(len(quantities) == 1, "expected exactly one declared IFC reproduction quantity")
    quantity = quantities[0]
    require(float(quantity["value"]) == float(expected["declared_quantity_value"]), "declared IFC quantity value mismatch")
    require(quantity["value_source"] == "declared_ifc_element_quantity", "IFC quantity provenance state mismatch")
    require(quantity["unit"]["unit_type"] == expected["declared_quantity_unit_type"], "IFC quantity unit type mismatch")
    require(quantity["unit"]["name"] == expected["declared_quantity_unit_name"], "IFC quantity unit name mismatch")
    require("source_record_id" not in wall["materials"][0], "IFC material was unexpectedly linked to an environmental source record")

    return {
        "ifc_source_sha256": sha256_file(ifc_path),
        "schema": extraction["schema"],
        "projects": len(extraction["spatial"]["projects"]),
        "buildings": len(extraction["spatial"]["buildings"]),
        "walls": len(walls),
        "material_name": expected["material_name"],
        "declared_quantity": {
            "name": quantity["name"],
            "value": quantity["value"],
            "value_source": quantity["value_source"],
            "unit": quantity["unit"],
        },
        "structural_output_sha256": sha256_file(structural_path),
        "extraction_output_sha256": sha256_file(extraction_path),
        "environmental_factor_linkage": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce ProofGrid v0.4 in a clean environment")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_json(args.manifest)
        system, expected_python = expected_python_for_platform(manifest)
        require(platform.python_version() == expected_python, f"Python mismatch for {system}: expected {expected_python}, got {platform.python_version()}")
        git = git_state(manifest)
        dependencies = installed_lock_state(ROOT / str(manifest["runtime"]["dependencies"]))
        input_hashes = verify_inputs(manifest)

        with tempfile.TemporaryDirectory(prefix="proofgrid-r5-") as tmp:
            work = Path(tmp)
            environmental = reproduce_environmental(manifest, work)
            ifc = reproduce_ifc(manifest, work)

        receipt: dict[str, Any] = {
            "result": manifest["result_label"],
            "r5_gate_status": "ENVIRONMENT_REPRODUCTION_EVIDENCE_GENERATED",
            "independence_scope": manifest["independence_scope"],
            "professional_certification": False,
            "scientific_validation": False,
            "manual_corrections_during_run": False,
            "deviations": [],
            "manifest_sha256": sha256_file(args.manifest),
            "git": git,
            "runtime_policy": manifest["runtime"],
            "environment": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "platform_system": system,
                "platform": platform.platform(),
                "python": platform.python_version(),
                "python_executable": sys.executable,
                "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
                "github_runner_os": os.environ.get("RUNNER_OS"),
                "github_runner_arch": os.environ.get("RUNNER_ARCH"),
                "dependencies": dependencies,
            },
            "input_sha256": input_hashes,
            "environmental": environmental,
            "ifc": ifc,
            "limitations": manifest["limitations"],
        }
        receipt["reproduction_receipt_sha256"] = hashlib.sha256(canonical_json_bytes(receipt)).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print("RESULT: CLEAN_ENVIRONMENT_REPRODUCED")
        print("NOT INDEPENDENT PROFESSIONAL OR SCIENTIFIC CERTIFICATION")
        return 0
    except ReproductionError as exc:
        print(f"REPRODUCTION FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
