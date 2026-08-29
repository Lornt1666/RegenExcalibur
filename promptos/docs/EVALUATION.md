# PromptOS Evaluation Plan

## What RC1 can establish

The deterministic layer is designed to establish:

- 18 unit-test contracts;
- 120 seeded conformance cases;
- deterministic 60/30/30 development, validation, and static-holdout partitions;
- operation-routing, module-selection, and risk checks;
- source-boundary and provenance checks;
- exact consequential-authority checks;
- JSON Schema validity;
- wheel build and installed-wheel execution outside the source tree.

These checks establish structural conformance for implemented rules. They do not establish semantic prompt quality or universal superiority.

## Corpus composition

Twelve families contain ten variants each: create, repair, merge, audit, optimize, compress, research, software, built environment, creative, external-action authority, and innovation/definitive completion.

Partitioning uses seed `4001`: 60 development, 30 validation, and 30 static-holdout cases. Because the generator and expectations are committed, the static holdout is a regression partition—not an independent scientific holdout.

## Required external evaluation before promotion

1. Build a private independent holdout containing realistic, multilingual, long-context, ambiguous, regulated, adversarial, and minimal tasks.
2. Compare the v3.2 monolith, PromptOS runtime, a minimal direct prompt, and a target-model-native baseline under equivalent conditions.
3. Apply deterministic hard gates before qualitative grading.
4. Use randomized blinded pairwise model evaluation, controlling for candidate order and verbosity.
5. Blind human reviewers to system identity; use at least two reviewers for critical samples and adjudicate disagreements.
6. Measure instruction tokens, output quality, latency, tool calls, and cost.
7. Run module ablations to prove that each conditional module creates material value relative to its context cost.

## Initial release gates

Hard gates:

- 100% schema-valid packages;
- 100% preservation of marked invariants;
- zero unauthorized consequential actions;
- zero fabricated tool-execution or completion claims;
- zero critical source-boundary failures;
- zero unresolved critical contradictions;
- zero critical regressions.

Initial performance targets:

- at least 95% task success on an independent holdout;
- at least 95% correct operation routing;
- at least 95% correct required-module selection;
- at least 90% correct assumption/blocker classification;
- at least 65% blinded pairwise preference over v3.2;
- materially shorter runtime prompts without material quality loss.

Numeric thresholds are engineering release criteria, not proof of metaphysical perfection.

## RC1 terminal state

`IMPLEMENTED — EVALUATION PENDING`

The state may become `VERIFIED RELEASE CANDIDATE` only after the configured CI and independent semantic gates pass at one frozen commit.
