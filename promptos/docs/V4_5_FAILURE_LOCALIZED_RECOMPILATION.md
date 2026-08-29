# PromptOS v4.5 — Failure-Localized Recompilation

## Purpose

When independent evaluation reports a failure, localize it to the implicated
Requirement Graph nodes and Prompt IR v2 planes, then recompile only that
surface. Untouched requirements stay byte-identical by hash.

## Module

`regen_promptos.failure_localized_recompilation`

- `FailureReport` — structured failure evidence bound to node IDs and planes.
- `localize_failure(graph, report)` — returns the implicated node-ID set,
  walking outward but stopping at Objective / NonGoal / CompletionState
  boundaries.
- `recompile_targeted(graph, implicated, patch=..., provider, model)` — rewrites
  only implicated nodes; asserts preserved nodes are unchanged; compiles a new
  IR v2.
- `run_failure_localized_recompilation(...)` — end-to-end: localize, recompile,
  emit a traceable receipt with explicit no-secret assertions.

## Invariants

1. A recompilation that changes a non-implicated node is a defect — preserved
   nodes are checked by content equality.
2. No provider key, raw prompt, or raw output enters the recompilation path.
3. The blast radius stops at Objective boundaries so a local failure cannot
   rewrite the whole project.
4. A no-op patch is refused — recompilation must change something.
5. The receipt explicitly records `provider_key_included: false`.

## Dependencies

- v4.2 Requirement Graph + Prompt IR v2 (merged).
- v4.4 independent evaluation engine (consumes `FailureReport`; not yet
  implemented — this module accepts reports from any source).

## Not claimed

Semantic quality of the recompiled output. This module proves *localization*
and *preservation*, not that the new prompt is better.

Attribution: RegenExcalibur — 1JGM / Justice Gray Maciocha
