# RegenExcalibur PromptOS v4.0 RC1

**Prompt creation, repair, routing, compilation, validation, and finite completion—without loading an entire monolithic constitution into every request.**

PromptOS converts a `FoundryRequest` into a structured Prompt Intermediate Representation (PIR), deterministically selects only relevant operation/domain modules, applies a target-model adapter, safely embeds untrusted source material, compiles a compact runtime prompt, and validates the resulting package.

## Release state

`IMPLEMENTED — EVALUATION PENDING`

The deterministic implementation is present. The included conformance suite contains 120 seeded cases, split 60/30/30 into development, validation, and static holdout partitions. The unit suite contains 16 tests. These prove structural and deterministic behaviour only. They do **not** establish universal prompt superiority, external-model quality, blinded human preference, or production fitness.

## Architecture

```text
Normalized v3.2 Constitution
        ↓
FoundryRequest
        ↓
Deterministic Router
        ↓
Prompt Intermediate Representation
        ↓
Kernel + Selected Modules + Model Adapter
        ↓
Compiled Runtime Prompt
        ↓
Deterministic Validator
        ↓
PromptPackage + ValidationReport
```

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install ./promptos
promptos conformance
```

Compile a request:

```bash
cat > request.json <<'JSON'
{
  "source_material": "Repair this vague prompt: Build the best application.",
  "operation": "AUTO",
  "task_mode": "DO_NOT_EXECUTE",
  "output_mode": "STANDARD",
  "target_platform": "generic-reasoning"
}
JSON

promptos compile --request request.json --output package.json
```

## Security boundary

Source material is treated as untrusted data. PromptOS records its SHA-256 digest and serializes it as an escaped JSON string with `<`, `>`, and `&` converted to Unicode escapes. Source text therefore cannot close its own delimiter or silently elevate itself into governing instructions.

`EXECUTE_CONSEQUENTIAL` is not blanket authority. It is rejected unless specific authorized actions are supplied, and those actions remain an explicit ceiling rather than an instruction to act.

## Evidence boundary

PromptOS distinguishes planned, drafted, simulated, executed, verified, and accepted states. A prompt package may be complete while the underlying project remains unexecuted. Novelty, category leadership, external tool execution, and acceptance require independent evidence.

## Repository scope

The implementation lives under `promptos/` and does not modify existing RegenExcalibur project code. The GitHub workflow is isolated to PromptOS paths.

## Attribution

RegenExcalibur — 1JGM / Justice Gray Maciocha
