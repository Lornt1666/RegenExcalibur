#!/usr/bin/env python3
"""Generate deterministic SHA-256 checksums for PromptOS source artifacts."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "dist", "build", ".pytest_cache"}
EXCLUDED_NAMES = {"checksums.txt"}


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "releases"
        / "v4.0.0-rc1"
        / "checksums.txt",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    lines = [f"{digest(path)}  {path.relative_to(root).as_posix()}" for path in iter_files(root)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} checksums to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
