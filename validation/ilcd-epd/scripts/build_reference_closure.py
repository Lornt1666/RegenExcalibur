#!/usr/bin/env python3
"""Build a deterministic local reference closure for one ILCD process fixture.

The script indexes XML datasets by ILCD/Common UUID, follows refObjectId
references recursively, and copies only the resolved dataset closure plus
package-level catalog files.

Official format-development sample repositories may intentionally contain more
than one example with the same UUID. The explicitly selected root process wins
for its own UUID. Any other multiply-defined referenced UUID is preserved as an
ambiguity and left unresolved rather than guessed.

No upstream file is edited. The manifest records exact source hashes, resolved
and unresolved references, and duplicate/ambiguous UUID evidence.
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

    parsed: dict[Path, ET.Element] = {}
    candidates_by_uuid: dict[str, list[Path]] = {}

    for path in sorted(source.rglob("*.xml")):
        try:
            root = parse_xml(path)
        except ET.ParseError:
            continue
        parsed[path] = root
        uid = dataset_uuid(root)
        if uid:
            candidates_by_uuid.setdefault(uid, []).append(path)

    root_xml = parsed.get(root_process) or parse_xml(root_process)
    root_uuid = dataset_uuid(root_xml)
    if not root_uuid:
        raise SystemExit("root process does not contain an ILCD UUID")

    duplicate_uuids = {
        uid: [path.relative_to(source).as_posix() for path in paths]
        for uid, paths in sorted(candidates_by_uuid.items())
        if len(paths) > 1
    }

    # Resolution rules are deterministic and non-inferential:
    # - the explicitly requested root path resolves its UUID;
    # - a UUID with exactly one package candidate resolves to that candidate;
    # - all other duplicate UUIDs remain ambiguous/unresolved.
    def resolve(uid: str) -> Path | None:
        if uid == root_uuid:
            return root_process
        paths = candidates_by_uuid.get(uid, [])
        if len(paths) == 1:
            return paths[0]
        return None

    queue = [root_uuid]
    visited: set[str] = set()
    unresolved: set[str] = set()
    ambiguous: dict[str, list[str]] = {}
    closure_paths: set[Path] = set()
    edges: list[dict[str, str]] = []

    while queue:
        uid = queue.pop(0)
        if uid in visited:
            continue
        visited.add(uid)
        path = resolve(uid)
        if path is None:
            paths = candidates_by_uuid.get(uid, [])
            if len(paths) > 1:
                ambiguous[uid] = [path.relative_to(source).as_posix() for path in paths]
            else:
                unresolved.add(uid)
            continue
        closure_paths.add(path)
        root = parsed.get(path) or parse_xml(path)
        for target in sorted(references(root)):
            edges.append({"from_uuid": uid, "to_uuid": target})
            if resolve(target) is not None:
                if target not in visited:
                    queue.append(target)
            else:
                paths = candidates_by_uuid.get(target, [])
                if len(paths) > 1:
                    ambiguous[target] = [path.relative_to(source).as_posix() for path in paths]
                else:
                    unresolved.add(target)

    # Preserve package-level XML/catalog files (classification/location metadata)
    # without importing unrelated dataset directories. These files generally do
    # not carry dataset UUIDs and are referenced through relative catalog attrs.
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
        "resolved_dataset_uuids": sorted(
            uid for uid in visited if resolve(uid) is not None
        ),
        "unresolved_reference_uuids": sorted(unresolved),
        "ambiguous_reference_uuids": ambiguous,
        "duplicate_dataset_uuids_in_source_package": duplicate_uuids,
        "reference_edges": sorted(edges, key=lambda x: (x["from_uuid"], x["to_uuid"])),
    }
    manifest["closure_manifest_sha256"] = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
