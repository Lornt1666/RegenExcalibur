#!/usr/bin/env python3
"""Dry-run NexusPrime compile card. Does not mutate cloud resources."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from load_kernel import CANONICAL, MAP, resolve


def compile_card(kernel: str, job: str) -> dict:
    path = resolve(kernel)
    return {
        "agent": "NexusPrimeAgent",
        "action": "compile_kernel",
        "dry_run": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job": job,
        "kernel": kernel,
        "kernel_found": path is not None,
        "kernel_path": str(path) if path else None,
        "canonical_url": f"{CANONICAL}/{MAP[kernel]}",
        "next_move": "Paste the kernel into the target runtime or run tools/install.sh from NEXUS-GENESIS-PRIME.",
        "guardrails": ["no_credentials", "no_external_mutate", "destructive_actions_disabled"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a NEXUS kernel card for RegenExcalibur.")
    parser.add_argument("--kernel", default="master", choices=["master", "gem", "gpt", "genesis"])
    parser.add_argument("--job", default="operator-compile")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    payload = compile_card(args.kernel, args.job)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
