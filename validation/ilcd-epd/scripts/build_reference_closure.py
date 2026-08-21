#!/usr/bin/env python3
"""Build a deterministic local reference closure for one ILCD process fixture.

The script is deliberately format-agnostic about dataset directory names. It
indexes XML datasets by the first ILCD/Common UUID element it can find, follows
all refObjectId attributes recursively, and copies only the resolved dataset
closure plus root-level XML/catalog files required by the sample package.

It never edits upstream files. The emitted manifest records the immutable source
file hashes, selected root process, resolved closure, and unresolved UUIDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_xml(path: Path) -> ET.Element:
    return ET.fromstring(path.read_bytes())


def dataset_uuid(root: ET.Element) -> str | None:
    for elem in root.iter():
        if local_name(elem.tag) == "UUID" and elem.text and elem.text.strip():
            return elem.text.strip()
    return None


def references(root: ET.Element) -> set[str]:
    out: set[str] = set()
    for elem in root.iter():
        value = elem.attrib.get("refObjectId")
        if value and value.strip():
            out.add(value.strip())
    return out


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--root-process", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    root_process = args.root_process.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise SystemExit(f"source directory not found: {source}")
    try:
        root_process.relative_to(source)
    except ValueError as exc:
        raise SystemExit("root process must be inside source directory") from exc
    if not root_process.is_file():
        raise SystemExit(f"root process not found: {root_process}")

    index: dict[str, Path] = {}
    parsed: dict[Path, ET.Element] = {}
    duplicate_uuids: dict[str, list[str]] = {}

    for path in sorted(source.rglob("*.xml")):
        try:
            root = parse_xml(path)
        except ET.ParseError:
            continue
        parsed[path] = root
        uid = dataset_uuid(root)
        if not uid:
            continue
        if uid in index:
            duplicate_uuids.setdefault(uid, [index[uid].relative_to(source).as_posix()]).append(
                path.relative_to(source).as_posix()
            )
        else:
            index[uid] = path

    if duplicate_uuids:
        raise SystemExit(f"duplicate dataset UUIDs in source package: {json.dumps(duplicate_uuids, sort_keys=True)}")

    root_xml = parsed.get(root_process) or parse_xml(root_process)
    root_uuid = dataset_uuid(root_xml)
    if not root_uuid:
        raise SystemExit("root process does not contain an ILCD UUID")

    queue = [root_uuid]
    visited: set[str] = set()
    unresolved: set[str] = set()
    closure_paths: set[Path] = set()
    edges: list[dict[str, str]] = []

    while queue:
        uid = queue.pop(0)
        if uid in visited:
            continue
        visited.add(uid)
        path = index.get(uid)
        if path is None:
            unresolved.add(uid)
            continue
        closure_paths.add(path)
        root = parsed.get(path) or parse_xml(path)
        for target in sorted(references(root)):
            edges.append({"from_uuid": uid, "to_uuid": target})
            if target in index:
                if target not in visited:
                    queue.append(target)
            else:
                unresolved.add(target)

    # Preserve package-level XML/catalog files (classification/location metadata)
    # without importing unrelated dataset directories. These files do not have
    # dataset UUIDs and are referenced by relative URI/catalog attributes.
    package_files: set[Path] = set()
    for path in sorted(source.iterdir()):
        if path.is_file() and path.suffix.lower() in {".xml", ".xsd", ".json"}:
            package_files.add(path)

    selected = sorted(closure_paths | package_files, key=lambda p: p.relative_to(source).as_posix())
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    files = []
    for path in selected:
        rel = path.relative_to(source)
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        files.append({
            "path": rel.as_posix(),
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "dataset_uuid": dataset_uuid(parsed[path]) if path in parsed else None,
        })

    manifest = {
        "root_process": root_process.relative_to(source).as_posix(),
        "root_uuid": root_uuid,
        "source_root": args.source.as_posix(),
        "selected_file_count": len(files),
        "selected_files": files,
        "resolved_dataset_uuids": sorted(uid for uid in visited if uid in index),
        "unresolved_reference_uuids": sorted(unresolved),
        "reference_edges": sorted(edges, key=lambda x: (x["from_uuid"], x["to_uuid"])),
    }
    manifest["closure_manifest_sha256"] = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
