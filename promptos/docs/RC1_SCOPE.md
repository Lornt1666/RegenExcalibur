# RC1 Scope

## In scope

- Deterministic prompt request model.
- Deterministic operation and module router.
- Compact runtime compiler.
- Prompt Intermediate Representation.
- Source provenance and isolation.
- Authority and completion-state controls.
- JSON contracts.
- Deterministic tests and conformance corpus.
- CI and package smoke procedure.
- Documentation and release evidence structure.

## Out of scope

- Calling a language-model API.
- Executing an underlying project.
- Browser or account automation.
- Storing credentials.
- Production deployment.
- Automatic prompt mutation based on live results.
- Claims of AGI, perfection, universal superiority, or solved prompt injection.
- Independent semantic holdout and human evaluation.

## Completion criterion

RC1 reaches `IMPLEMENTED — EVALUATION PENDING` when source, tests, schemas, CI, and evidence-bound documentation are present on a review branch. It reaches `VERIFIED RELEASE CANDIDATE` only after branch CI and independent semantic release gates pass.
