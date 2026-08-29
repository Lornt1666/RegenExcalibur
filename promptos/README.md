# RegenExcalibur PromptOS

Deterministic prompt compiler with a secret-safe BYOK client preflight, a
local provider runner, a private control-plane contract stub, and
failure-localized recompilation. Version **4.5.0-rc1**.

## What it does

- Compiles human intent into a typed **Requirement Graph** and five-plane
  **Prompt IR v2**.
- Produces a secret-free BYOK execution plan: the customer's provider key never
  enters PromptOS; the PromptOS token never enters the provider.
- Executes the plan locally against an allowlisted provider, refusing redirects,
  bounding response size, and emitting a redacted receipt.
- Reserves, settles, and cancels PromptOS service units through an
  **in-memory control plane** with an append-only, hash-chained ledger.
- **Localizes evaluation failures** to specific graph nodes and recompiles only
  the implicated surface, preserving untouched requirements by hash.

## CLI

```
promptos compile --request req.json --output pkg.json
promptos byok-template --provider openai --output byok.json
promptos byok-preflight --package pkg.json --config byok.json --output plan.json
promptos byok-authorization-request --package pkg.json --config byok.json \
    --idempotency-key job-1 --output auth.json
promptos byok-run --plan plan.json --config byok.json --prompt prompt.txt \
    --output result.json --output-dir ./out
```

## Security invariants

1. Customer provider credentials remain under customer control.
2. Provider credentials never enter the PromptOS control plane.
3. PromptOS access credentials never enter a model-provider request.
4. No secret appears in plans, logs, receipts, or telemetry.
5. Raw prompts and outputs remain local by default.
6. A failed provider request is never settled as successful.
7. Redirects are refused; destination hosts are revalidated before credential use.
8. The control plane rejects provider keys, raw prompts, and raw outputs.
9. Every commercial transition is idempotent and append-only.
10. Failure-localized recompilation preserves non-implicated nodes by hash.

## Status

- v4.2 semantic substrate: merged, CI green.
- v4.3 local runner: merged into `feat/promptos-byok-runtime`, CI green.
- v4.4 control-plane stub: merged, CI green.
- v4.5 failure-localized recompilation: this release candidate.
- Independent evaluation engine, evidence ledger, Digital Project Twin:
  not implemented.

Attribution: RegenExcalibur — 1JGM / Justice Gray Maciocha
