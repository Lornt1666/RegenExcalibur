# RegenExcalibur PromptOS v4.1 RC1

PromptOS converts a prompt-creation or prompt-repair request into a structured Prompt Intermediate Representation (PIR), deterministically selects only the relevant operation and domain modules, applies a target-model adapter, safely embeds untrusted source material, compiles a compact runtime prompt, and validates the resulting package.

**Current state:** `IMPLEMENTED — EVALUATION, BYOK CONTROL PLANE, AND COMMERCIAL ACTIVATION PENDING`

This release candidate establishes deterministic compiler behaviour and a secret-safe BYOK client preflight. It does not claim universal prompt superiority, production fitness, solved prompt injection, licensed engineering authority, a deployed payment system, live provider execution, or independent semantic verification.

## BYOK: customer provider account, PromptOS orchestration

PromptOS v4.1 adds a local-direct BYOK architecture:

```text
Customer provider key          → model provider only
PromptOS access token          → PromptOS control plane only
Compiled runtime prompt        → model provider from customer device
Hashes and redacted receipt    → PromptOS control plane
Provider invoice               → customer provider account
PromptOS subscription/units    → RegenExcalibur
```

The public client now implements:

- provider profiles for OpenAI, Anthropic, Google Gemini, and reviewed custom endpoints;
- environment-variable-only credential configuration;
- official-provider HTTPS host allowlists;
- distinct provider, PromptOS, and control-plane environment variables;
- deterministic PromptOS service-unit quotes;
- secret-free authorization-request bodies;
- secret-free execution plans and completion receipts;
- fail-closed commercial preflight;
- explicit `planned ≠ authorized ≠ executed ≠ settled ≠ verified` states.

It does **not** perform a live provider or payment request yet. See:

- [BYOK architecture](BYOK_ARCHITECTURE.md)
- [BYOK control-plane contract](BYOK_CONTROL_PLANE.md)
- [OpenAPI draft](specs/byok-control-plane.openapi.yaml)

Generate a configuration template:

```bash
promptos byok-template --provider openai --output byok.openai.json
```

Set values in the local process environment—never in the JSON file or repository:

```bash
export OPENAI_API_KEY='YOUR_PROVIDER_KEY'
export PROMPTOS_ACCESS_TOKEN='YOUR_PROMPTOS_ACCESS_TOKEN'
export PROMPTOS_CONTROL_PLANE_URL='https://OWNER_APPROVED_CONTROL_PLANE_HOST'
```

Compile a PromptOS package, then run the local preflight:

```bash
promptos byok-preflight \
  --package package.json \
  --config byok.openai.json \
  --output byok-plan.json
```

Until a real control plane is deployed, use `--allow-blocked` to inspect the plan without claiming authorization:

```bash
promptos byok-preflight \
  --package package.json \
  --config byok.openai.json \
  --output byok-plan.json \
  --allow-blocked
```

Create the future control-plane authorization body:

```bash
promptos byok-authorization-request \
  --package package.json \
  --config byok.openai.json \
  --idempotency-key YOUR_UNIQUE_JOB_KEY \
  --output authorization-request.json
```

The body contains hashes and a service-unit quote—not provider credentials, source material, or the compiled prompt.

## AutoDesign / AutoEngineer

PromptOS is structured as a multidisciplinary design-and-engineering coordination layer:

- **AutoDesign** — rough objective → requirements → concept alternatives → selected system/product architecture → implementation blueprint → acceptance criteria.
- **AutoEngineer** — design basis → technical constraints → discipline routing → interfaces → failure modes → verification plan → qualified-review handoff.
- **AutoBuild Plan** — approved specification → phased work breakdown, dependencies, roles, tools, tests, evidence, rollback, and terminal conditions.
- **AutoAudit** — audit prompts, projects, technical specifications, or AI-generated designs for contradictions, missing requirements, evidence gaps, authority problems, and false completion claims.

See [AUTODESIGN_AUTOENGINEER.md](AUTODESIGN_AUTOENGINEER.md).

AI-generated engineering material is not represented as sealed, stamped, permit-approved, professionally certified, or a replacement for legally required qualified review.

## Commercial use and services

PromptOS is structured to support paid BYOK orchestration, prompt engineering, AutoDesign, AutoEngineer coordination, private PromptOS implementations, evaluation audits, enterprise integrations, specialized module packs, and future owner-approved commercial licensing.

- [Commercialization architecture](COMMERCIALIZATION.md)
- [Paid offer catalog](PAID_OFFER_CATALOG.md)
- [Current licence status](LICENSE_STATUS.md)

**Commercial inquiries:** `justlornt95+redditwork@gmail.com`

Public repository visibility does not itself grant commercial exploitation rights. Commercial embedding or redistribution must follow the effective licence terms or a separate owner-approved agreement.

## Architecture

```text
v3.2 constitutional baseline
        ↓
FoundryRequest
        ↓
request validation + deterministic routing
        ↓
Prompt Intermediate Representation
        ↓
kernel + selected modules + model adapter
        ↓
compiled runtime prompt
        ↓
package validation + BYOK preflight + release evidence
```

## Quick start

```bash
cd promptos
python -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
promptos conformance
```

Compile a request:

```bash
cat > request.json <<'JSON'
{
  "source_material": "Repair this vague prompt: Build the best application and keep improving it forever.",
  "operation": "AUTO",
  "task_mode": "DO_NOT_EXECUTE",
  "output_mode": "FULL_FOUNDRY",
  "target_platform": "openai-reasoning",
  "max_refinement_passes": 3
}
JSON

promptos compile --request request.json --output package.json
```

## Deterministic evidence included

- 37 deterministic unit tests after the BYOK addition.
- 120 generated conformance cases.
- Deterministic 60/30/30 development, validation, and static-holdout split.
- Python 3.11 and 3.12 CI.
- Wheel build and installed-wheel smoke test outside the source tree.
- SHA-256 source provenance and delimiter-safe source encoding.
- Exact consequential-action allowlist rather than blanket authority.
- Explicit separation of prompt completion, implementation, verification, and acceptance.
- BYOK key-boundary, endpoint, redaction, idempotency-body, and fail-closed tests.

The committed static holdout is a regression partition, not an independent scientific holdout. External model evaluation, blinded baseline comparison, critical human review, control-plane security testing, payment reconciliation, and owner release approval remain mandatory before promotion.

## Scope

All implementation files are isolated under `promptos/`; the GitHub workflow is path-scoped. Existing RegenExcalibur application code is not modified.

## Attribution

RegenExcalibur — 1JGM / Justice Gray Maciocha
