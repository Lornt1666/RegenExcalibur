# Contributing to PromptOS

PromptOS changes must be evidence-driven.

## Change protocol

1. Link the observed failure or missing requirement.
2. Add or update a deterministic or semantic evaluation case.
3. Make the smallest change that addresses the failure.
4. Run unit and conformance checks.
5. Check unrelated categories for regressions.
6. Record the result and retain or reject the change.

## Rules

- Do not add a discipline, role, or prohibition merely for prestige.
- Do not weaken the default no-execution boundary.
- Do not expand consequential authority implicitly.
- Do not claim novelty, superiority, verification, or acceptance without evidence.
- Do not optimize repeatedly against the independent holdout.
- Keep provider-neutral requirements separate from model adapters.
- Keep source data separate from governing instructions.

## Required commands

```bash
make verify
```

A release-state promotion also requires the external evaluations listed in `docs/EVALUATION.md`.
