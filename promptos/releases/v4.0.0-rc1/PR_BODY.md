## Summary

This pull request introduces **RegenExcalibur PromptOS v4.0 RC1**, refactoring the v3.2 Ω-Prime Universal Prompt Foundry from a monolithic meta-prompt into a modular, deterministic prompt-compilation system.

## What changed

- Added a normalized frozen v3.2 constitutional baseline and requirement registry.
- Added typed FoundryRequest, PIR, PromptPackage, and ValidationReport contracts.
- Added deterministic operation routing, conditional module selection, risk classification, and target-model adapters.
- Added SHA-256 source provenance and delimiter-safe untrusted-source serialization.
- Added exact consequential-action authorization rather than blanket autonomy.
- Added a compact runtime compiler and structural validator.
- Added a 120-case seeded conformance corpus with 60/30/30 partitions.
- Added 16 unit tests.
- Added Python 3.11/3.12 CI, wheel build, and installed-wheel smoke procedure.
- Added architecture, security, evaluation, migration, traceability, and release documentation.

## Scope boundary

All product code is isolated under `promptos/`. The workflow is path-scoped. This PR does not modify existing RegenExcalibur application code and does not write directly to `main`.

## Security boundary

Source material is hashed and encoded as one escaped JSON string. Raw angle brackets cannot be contributed by the source block. The validator checks source fidelity, delimiter count, kernel presence, and exact action authority.

`EXECUTE_CONSEQUENTIAL` requires a specific authorized-action list. The compiler does not connect to or operate external services.

## Evidence state

The deterministic test and conformance machinery is included. GitHub Actions is the branch receipt for unit, conformance, corpus, wheel, and installed-wheel checks.

External-model quality, blinded pairwise preference over v3.2, independent human review, production fitness, and universal superiority are explicitly **not** claimed.

## Terminal state

**IMPLEMENTED — EVALUATION PENDING**
