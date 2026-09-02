#!/usr/bin/env python3
"""Load a NEXUS kernel from the local hook or print the canonical GitHub URL."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANONICAL = "https://github.com/Lornt1666/NEXUS-GENESIS-PRIME/blob/main/prompts"
MAP = {
    "master": "NEXUS-PRIME_MASTER_PROMPT.md",
    "gem": "NEXUS-PRIME_GEM_INSTRUCTIONS.md",
    "gpt": "NEXUS-PRIME_CUSTOM_GPT.md",
    "genesis": "NEXUS-GENESIS-PRIME.md",
}


def resolve(name: str) -> Path | None:
    filename = MAP[name]
    refmap = {
        "master": "master-prompt.md",
        "gem": "gem-instructions.md",
        "gpt": "custom-gpt.md",
        "genesis": "master-prompt.md",
    }
    candidates = [
        HERE / "kernels" / filename,
        Path.home() / ".grok" / "skills" / "nexus-prime" / "references" / refmap[name],
    ]
    for path in candidates:
        try:
            if path.is_file() and path.stat().st_size > 0:
                return path
        except OSError:
            continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a NEXUS kernel for RegenExcalibur.")
    parser.add_argument("kernel", choices=sorted(MAP))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = resolve(args.kernel)
    payload = {
        "kernel": args.kernel,
        "found": path is not None,
        "path": str(path) if path else None,
        "canonical_url": f"{CANONICAL}/{MAP[args.kernel]}",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if path else 1
    if path:
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return 0
    print(payload["canonical_url"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
