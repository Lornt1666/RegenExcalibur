# PromptOS Evaluation Plan

## What RC1 proves

The included deterministic layer can be evaluated without an external model:

- 16 unit tests;
- 120 seeded conformance cases;
- deterministic 60/30/30 development, validation, and static holdout partitions;
- operation-routing checks;
- required-module checks;
- risk-classification checks;
- source-boundary and provenance checks;
- consequential-authority checks;
- package-data and installed-wheel smoke checks in CI.

These tests establish structural conformance for the implemented rules. They do not prove semantic prompt quality or universal superiority.

## Corpus composition

Twelve families contain ten variants each:

1. create;
2. repair;
3. merge;
4. audit;
5. optimize;
6. compress;
7. research;
8. software;
9. built environment;
10. creative;
11. external-action authority;
12. innovation and definitive completion.

The corpus is generated deterministically and then shuffled with seed `4001` into 60 development, 30 validation, and 30 static holdout cases.

Because the generator and expected outcomes are committed in the same repository, the static holdout is a regression partition—not an independent scientific holdout. A credible external holdout must be authored or retained outside the optimization loop.

## Required external evaluation before release

### 1. Representative task corpus

Expand to real prompts from diverse domains, lengths, languages, risk classes, and failure conditions. Remove private data and preserve provenance.

### 2. Baselines

Compare:

- original v3.2 monolith;
- compact PromptOS runtime;
- a minimal direct prompt;
- target-model native best practice;
- ablations without individual modules.

### 3. Independent model grading

Use pass/fail and blinded pairwise judgments for intent fidelity, completeness, clarity, scope discipline, tool truthfulness, evidence integrity, safety, and usability. Randomize candidate order and control for verbosity.

### 4. Human review

Blind reviewers to system identity. Require at least two reviewers for critical samples and adjudicate disagreements. Report inter-rater agreement and category-level failures.

### 5. Efficiency

Measure runtime instruction characters/tokens, latency, tool calls, and monetary cost. PromptOS must not claim improvement if quality gains depend on disproportionate context or cost.

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

Numeric thresholds are engineering release criteria, not metaphysical proof of perfection.

## RC1 terminal state

`IMPLEMENTED — EVALUATION PENDING`

The next evidence-producing milestone is an external baseline and blinded evaluation run. RC1 must not be called `VERIFIED RELEASE CANDIDATE` until that evidence exists.
