# PromptOS Quality Gates

## Deterministic hard gates

A compiled package is blocked when any of these fail:

- non-empty source material;
- valid operation, task-mode, and output-mode enums;
- refinement pass count between one and five;
- context budget large enough for the compiled runtime;
- supported consequential-action names;
- no overlap between authorized and prohibited actions;
- explicit action list for consequential mode;
- SHA-256 source match;
- delimiter-safe source round trip;
- unique selected modules;
- presence of all universal kernel modules;
- source hash present in runtime prompt;
- exactly one compiler-owned source closing delimiter;
- no-execution boundary present when required;
- exact consequential authorization in the PIR.

## Semantic gates requiring external evaluation

- intent fidelity under ambiguity;
- invariant preservation in generated outputs;
- completeness without scope inflation;
- domain correctness;
- professional realism;
- evidence quality;
- resistance to novel prompt injection;
- output usability;
- comparative performance against baselines;
- language and cultural robustness.

## Release states

- `ARCHITECTURE SPECIFICATION COMPLETE`
- `IMPLEMENTATION READY`
- `IMPLEMENTED — EVALUATION PENDING`
- `VERIFIED RELEASE CANDIDATE`
- `RELEASED`
- `BLOCKED`

RC1 is fixed at `IMPLEMENTED — EVALUATION PENDING` until branch CI and independent semantic evaluation produce their required receipts.
