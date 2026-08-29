"""Command-line interface for RegenExcalibur PromptOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .core import (
    FoundryRequest,
    PromptOSError,
    compile_request,
    generate_corpus,
    run_conformance,
    split_corpus,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptos",
        description="Compile and validate task-specific RegenExcalibur prompts.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    compile_parser = subcommands.add_parser(
        "compile", help="Compile a FoundryRequest JSON file."
    )
    compile_parser.add_argument("--request", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)

    conformance_parser = subcommands.add_parser(
        "conformance", help="Run the 120-case deterministic conformance corpus."
    )
    conformance_parser.add_argument("--output", type=Path)

    corpus_parser = subcommands.add_parser(
        "corpus", help="Write development, validation, and holdout JSONL files."
    )
    corpus_parser.add_argument("--output-dir", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "compile":
            raw = json.loads(args.request.read_text(encoding="utf-8"))
            package = compile_request(FoundryRequest.from_dict(raw))
            _write_json(args.output, package)
            print(
                json.dumps(
                    {
                        "status": package["validation"]["status"],
                        "operation": package["operation"],
                        "modules": package["selected_modules"],
                        "output": str(args.output),
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        if args.command == "conformance":
            report = run_conformance()
            if args.output:
                _write_json(args.output, report)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if report["status"] == "PASS" else 1

        if args.command == "corpus":
            cases = generate_corpus()
            partitions = split_corpus(cases)
            for name, rows in partitions.items():
                _write_jsonl(args.output_dir / f"{name}.jsonl", rows)
            manifest = {
                "total": len(cases),
                "development": len(partitions["development"]),
                "validation": len(partitions["validation"]),
                "holdout": len(partitions["holdout"]),
                "seed": 4001,
            }
            _write_json(args.output_dir / "manifest.json", manifest)
            print(json.dumps(manifest, sort_keys=True))
            return 0
    except (OSError, ValueError, json.JSONDecodeError, PromptOSError) as exc:
        parser.exit(2, f"promptos: error: {exc}\n")

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
