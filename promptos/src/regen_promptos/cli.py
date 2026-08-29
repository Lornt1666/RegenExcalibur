"""Command-line interface for RegenExcalibur PromptOS."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from .byok import (
    BYOKConfig,
    BYOKError,
    BYOKProvider,
    build_authorization_request,
    build_byok_plan,
    byok_config_template,
)
from .byok_runner import BYOKRunError, run_byok_plan
from .core import (
    FoundryRequest,
    PromptOSError,
    compile_request,
    generate_corpus,
    run_conformance,
    split_corpus,
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


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
        description="Compile, validate, preflight, and run RegenExcalibur PromptOS jobs.",
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

    template_parser = subcommands.add_parser(
        "byok-template",
        help="Write a secret-free local BYOK configuration template.",
    )
    template_parser.add_argument(
        "--provider",
        choices=[provider.value for provider in BYOKProvider],
        required=True,
    )
    template_parser.add_argument("--output", type=Path, required=True)

    preflight_parser = subcommands.add_parser(
        "byok-preflight",
        help=(
            "Validate local BYOK boundaries and write a secret-free execution plan; "
            "no provider or payment call is performed."
        ),
    )
    preflight_parser.add_argument("--package", type=Path, required=True)
    preflight_parser.add_argument("--config", type=Path, required=True)
    preflight_parser.add_argument("--output", type=Path, required=True)
    preflight_parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Write a BLOCKED plan instead of exiting when required environment values are absent.",
    )

    authorization_parser = subcommands.add_parser(
        "byok-authorization-request",
        help=(
            "Create the secret-free body a future PromptOS control plane will use "
            "to reserve service units."
        ),
    )
    authorization_parser.add_argument("--package", type=Path, required=True)
    authorization_parser.add_argument("--config", type=Path, required=True)
    authorization_parser.add_argument("--idempotency-key", required=True)
    authorization_parser.add_argument("--output", type=Path, required=True)

    run_parser = subcommands.add_parser(
        "byok-run",
        help=(
            "Execute a PASS BYOK plan against the allowlisted provider. "
            "Resolves the provider key from the local environment in memory; "
            "refuses redirects; bounds response size; writes a redacted receipt. "
            "No PromptOS credential is sent to the provider."
        ),
    )
    run_parser.add_argument("--plan", type=Path, required=True)
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--prompt", type=Path, required=True,
                            help="File containing the compiled runtime prompt text.")
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, default=None,
                            help="Local directory to persist raw provider output.")
    run_parser.add_argument("--timeout", type=float, default=30.0)
    run_parser.add_argument("--authorization-id", default=None)
    run_parser.add_argument("--settlement-id", default=None)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and build the request but do not perform the network call.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "compile":
            package = compile_request(FoundryRequest.from_dict(_read_json(args.request)))
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

        if args.command == "byok-template":
            provider = BYOKProvider(args.provider)
            _write_json(args.output, byok_config_template(provider))
            print(
                json.dumps(
                    {
                        "status": "TEMPLATE_WRITTEN",
                        "provider": provider.value,
                        "output": str(args.output),
                        "contains_secret": False,
                    },
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "byok-preflight":
            package = _read_json(args.package)
            config = BYOKConfig.from_dict(_read_json(args.config))
            plan = build_byok_plan(
                package,
                config,
                require_ready=not args.allow_blocked,
            )
            _write_json(args.output, plan)
            print(
                json.dumps(
                    {
                        "status": plan["status"],
                        "provider": plan["provider"]["name"],
                        "service_units": plan["metering"]["total_units"],
                        "output": str(args.output),
                        "live_call_performed": False,
                    },
                    sort_keys=True,
                )
            )
            return 0 if plan["status"] == "PASS" or args.allow_blocked else 1

        if args.command == "byok-authorization-request":
            package = _read_json(args.package)
            config = BYOKConfig.from_dict(_read_json(args.config))
            request = build_authorization_request(
                package,
                config,
                idempotency_key=args.idempotency_key,
            )
            _write_json(args.output, request)
            print(
                json.dumps(
                    {
                        "status": "AUTHORIZATION_REQUEST_WRITTEN",
                        "service_units": request["service_quote"]["total_units"],
                        "output": str(args.output),
                        "provider_key_included": False,
                    },
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "byok-run":
            plan = _read_json(args.plan)
            config = BYOKConfig.from_dict(_read_json(args.config))
            prompt_text = args.prompt.read_text(encoding="utf-8")
            if args.dry_run:
                from .byok_runner import _build_request, _resolve_provider_key
                key = _resolve_provider_key(config.provider_key_env, os.environ)
                req = _build_request(config, plan, prompt_text, key)
                print(json.dumps({
                    "status": "DRY_RUN",
                    "method": req.get_method(),
                    "url": req.full_url,
                    "headers": {k: ("[REDACTED]" if "auth" in k.lower() or "key" in k.lower() else v)
                                for k, v in req.headers.items()},
                    "live_call_performed": False,
                }, sort_keys=True))
                return 0
            result = run_byok_plan(
                plan,
                config,
                prompt_text,
                timeout_s=args.timeout,
                persist_output=bool(args.output_dir),
                output_dir=str(args.output_dir) if args.output_dir else None,
                authorization_id=args.authorization_id,
                settlement_id=args.settlement_id,
            )
            _write_json(args.output, result.to_dict())
            print(json.dumps({
                "status": result.status,
                "outcome": result.outcome,
                "http_status": result.http_status,
                "output_sha256": result.output_sha256,
                "receipt_sha256": result.receipt.get("receipt_sha256"),
                "output": str(args.output),
                "live_call_performed": True,
            }, sort_keys=True))
            return 0 if result.outcome == "SUCCEEDED" else 1

    except (OSError, ValueError, json.JSONDecodeError, PromptOSError, BYOKError, BYOKRunError) as exc:
        parser.exit(2, f"promptos: error: {exc}\n")

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
