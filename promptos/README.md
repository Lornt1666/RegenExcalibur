# RegenExcalibur PromptOS v4.0 RC1

PromptOS converts a prompt-creation or prompt-repair request into a structured Prompt Intermediate Representation (PIR), deterministically selects only the relevant operation and domain modules, applies a target-model adapter, safely embeds untrusted source material, compiles a compact runtime prompt, and validates the resulting package.

**Current state:** `IMPLEMENTED — EVALUATION PENDING`

This release candidate establishes deterministic compiler behaviour. It does not claim universal prompt superiority, production fitness, solved prompt injection, licensed engineering authority, or independent semantic verification.

## AutoDesign / AutoEngineer

PromptOS is being extended as a multidisciplinary design-and-engineering coordination layer:

- **AutoDesign** — rough objective → requirements → concept alternatives → selected system/product architecture → implementation blueprint → acceptance criteria.
- **AutoEngineer** — design basis → technical constraints → discipline routing → interfaces → failure modes → verification plan → qualified-review handoff.
- **AutoBuild Plan** — approved specification → phased work breakdown, dependencies, roles, tools, tests, evidence, rollback, and terminal conditions.
- **AutoAudit** — audit prompts, projects, technical specifications, or AI-generated designs for contradictions, missing requirements, evidence gaps, authority problems, and false completion claims.

See [AUTODESIGN_AUTOENGINEER.md](AUTODESIGN_AUTOENGINEER.md).

AI-generated engineering material is not represented as sealed, stamped, permit-approved, professionally certified, or a replacement for legally required qualified review.

## Commercial use and services

PromptOS is structured to support paid prompt engineering, AutoDesign, AutoEngineer coordination, private PromptOS implementations, evaluation audits, enterprise integrations, specialized module packs, and future owner-approved commercial licensing.

- [Commercialization architecture](COMMERCIALIZATION.md)
- [Paid offer catalog](PAID_OFFER_CATALOG.md)
- [Current licence status](LICENSE_STATUS.md)

**Commercial inquiries:** `justlornt95+redditwork@gmail.com`

Public repository visibility does not itself grant commercial exploitation rights. Any commercial embedding or redistribution must follow the effective licence terms or a separate owner-approved agreement.

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
package validation + release evidence
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

- Deterministic unit tests.
- 120 generated conformance cases.
- Deterministic 60/30/30 development, validation, and static-holdout split.
- Python 3.11 and 3.12 CI.
- Wheel build and installed-wheel smoke test outside the source tree.
- SHA-256 source provenance and delimiter-safe source encoding.
- Exact consequential-action allowlist rather than blanket authority.
- Explicit separation of prompt completion, implementation, verification, and acceptance.

The committed static holdout is a regression partition, not an independent scientific holdout. External model evaluation, blinded baseline comparison, critical human review, and owner release approval remain mandatory before promotion.

## Scope

All implementation files are isolated under `promptos/`; the GitHub workflow is path-scoped. Existing RegenExcalibur application code is not modified.

## Attribution

RegenExcalibur — 1JGM / Justice Gray Maciocha
