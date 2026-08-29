# RegenExcalibur PromptOS v4.2 RC1

PromptOS converts human intent into a typed Requirement Graph, compiles it to a
five-plane Prompt IR v2, and validates fail-closed. BYOK client preflight
(v4.1) is preserved: provider keys never enter PromptOS.

**Current state:** `ARCHITECTURE SPECIFICATION COMPLETE — CI VERIFICATION PENDING`

## v4.2 semantic substrate

- Requirement Graph: 20 node types, 16 edge types, 10 invariants
- Prompt IR v2: semantic / execution / model / verification / commercial planes
- Vertical slice: source -> graph -> IR -> traceability receipt
- 5 JSON Schemas, 6 examples, 7 deterministic tests

## BYOK (v4.1, preserved)

Customer provider key -> model provider only. PromptOS token -> control plane only.
No live provider calls, no payments, no control plane in this release.

## Quick start

```bash
cd promptos
python -m venv .venv && . .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

Attribution: RegenExcalibur — 1JGM / Justice Gray Maciocha
