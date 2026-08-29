# RegenExcalibur PromptOS v4.0 RC1

PromptOS converts a prompt-creation or prompt-repair request into a structured Prompt Intermediate Representation (PIR), deterministically selects only the relevant operation and domain modules, applies a target-model adapter, safely embeds untrusted source material, compiles a compact runtime prompt, and validates the resulting package.

**Current state:** `IMPLEMENTED — EVALUATION PENDING`

This release candidate establishes deterministic compiler behaviour. It does not claim universal prompt superiority, production fitness, solved prompt injection, or independent semantic verification.

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

- 16 unit tests.
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
