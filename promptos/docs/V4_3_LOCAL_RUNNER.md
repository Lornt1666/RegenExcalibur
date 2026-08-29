# PromptOS v4.3 — Local BYOK Provider Runner

## Mission

Execute a `PASS` BYOK plan against an allowlisted provider endpoint from the
customer's device, preserving every credential invariant from v4.1.

## What this adds

- `byok_runner.py`: `run_byok_plan`, `validate_redirect_target`, `NoRedirect`.
- CLI command `promptos byok-run`.
- Deterministic tests with a local mock HTTP server: success path, transport
  failure → FAILED receipt, response byte cap, redirect refusal, host
  revalidation, key non-leakage.

## Invariants enforced at execution

- Provider key resolved from env in memory; never persisted or logged.
- Every redirect refused; candidate destination revalidated against the
  allowlist before any credential is attached.
- Response bounded by `max_response_bytes` (default 1 MiB).
- Timeout enforced (default 30s).
- Raw output persisted locally only when `--output-dir` is given.
- Receipt's `known_secrets` includes the provider key and PromptOS token;
  leakage raises `BYOKRunError`.
- A transport or HTTP error produces `outcome=FAILED` with a redacted receipt.

## What this deliberately does not do

- No control-plane settlement (v4.9).
- No payment processing.
- No multi-provider streaming.
- No persistent credential store.

## Tests

`tests/test_byok_runner.py` — 6 cases, all deterministic, no network to the
public internet (uses `127.0.0.1` mock server).
