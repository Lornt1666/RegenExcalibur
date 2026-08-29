# PromptOS v4.0 RC1 Implementation Report

## Objective

Refactor the RegenExcalibur Ω-Prime Universal Prompt Foundry v3.2 from a monolithic meta-prompt into a modular, deterministic, schema-governed prompt-compilation system.

## Implemented

- Normalized frozen constitutional baseline and requirement registry.
- Typed request model with closed operation, task-mode, and output-mode enums.
- Deterministic AUTO operation routing.
- Conditional domain-module selection.
- Model-adapter selection.
- Risk classification.
- Prompt Intermediate Representation.
- SHA-256 source provenance.
- Delimiter-safe untrusted-source serialization.
- Compact runtime-prompt compiler.
- Exact consequential-action authority list.
- Package validation.
- Four JSON Schemas.
- Command-line compile, conformance, and corpus commands.
- 120 seeded deterministic conformance cases.
- Sixteen unit tests.
- Path-scoped CI for Python 3.11 and 3.12.
- Wheel build and installed-wheel smoke procedure.
- Architecture, security, evaluation, and traceability documents.

## Architectural gains over v3.2

The runtime no longer carries the entire discipline catalogue, every operation, every professional module, and every completion clause. It compiles only:

1. the universal kernel;
2. one selected operation module;
3. materially matched domain modules;
4. one target-model adapter;
5. the PIR;
6. safely serialized source data;
7. the requested output contract.

This makes context cost measurable and allows module-level ablation.

## Deliberate limitations

The keyword router is a deterministic RC implementation, not a complete semantic classifier. It is transparent and testable, but multilingual phrasing, subtle intent, and unseen domain language require a broader corpus or a separately governed classifier.

The committed 30-case static holdout is useful for regression separation but is not independent because its generator and expectations are visible in the repository.

No external language-model benchmark or blinded human comparison is included in RC1. Therefore no claim of universal quality, category leadership, or production readiness is made.

The v3.2 constitution is normalized rather than asserted to be a verbatim export of a separate signed source artifact. That distinction is explicit in the manifest.

## Next evidence gate

1. Allow branch CI to run.
2. Inspect test and wheel-smoke receipts.
3. Build a private independent holdout.
4. Run v3.2 monolith, PromptOS runtime, and minimal baseline on the same cases.
5. Conduct randomized blinded pairwise grading.
6. Review safety-critical failures manually.
7. release only after the stated gates pass.

## Terminal state

**IMPLEMENTED — EVALUATION PENDING**
