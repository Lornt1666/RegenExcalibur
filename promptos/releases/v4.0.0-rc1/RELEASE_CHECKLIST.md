# PromptOS v4.0 RC1 Release Checklist

## Clean implementation

- [x] Package source, metadata, and explicit licence state present.
- [x] Normalized v3.2 constitution and requirement IDs present.
- [x] Kernel separated from conditional operation/domain modules.
- [x] Deterministic router, PIR, compiler, validator, and CLI present.
- [x] Four JSON Schemas present.
- [x] Eighteen deterministic unit tests present.
- [x] A 120-case corpus generator and 60/30/30 split present.
- [x] Python 3.11/3.12 CI, schema validation, wheel build, and installed-wheel smoke procedure present.
- [x] No accidental marker-document sequence included.
- [x] `FOUNDRY_OPERATION` label corrected.

## Hosted verification

- [ ] GitHub Actions Python 3.11 job passes at exact head.
- [ ] GitHub Actions Python 3.12 job passes at exact head.
- [ ] All 18 tests pass in hosted CI.
- [ ] Deterministic conformance passes 120/120 in hosted CI.
- [ ] All four schemas and compiled instances validate.
- [ ] Corpus materializes as exactly 60/30/30.
- [ ] Wheel builds.
- [ ] Installed-wheel conformance passes outside source tree.

## Independent evaluation

- [ ] Independent private holdout frozen.
- [ ] v3.2 monolith baseline run.
- [ ] Minimal direct-prompt baseline run.
- [ ] Target-model-native baseline run.
- [ ] PromptOS candidate run under equivalent conditions.
- [ ] Hard gates applied before preference grading.
- [ ] Pairwise candidate order randomized and blinded.
- [ ] Verbosity bias controlled.
- [ ] Critical samples reviewed by humans.
- [ ] Token, latency, and cost effects reported.
- [ ] Category-level failures and confidence documented.

## Release truthfulness

- [x] Current state remains `IMPLEMENTED — EVALUATION PENDING`.
- [x] No claim of perfection, universal superiority, solved injection, production readiness, or release.
- [ ] Owner reviews repository location and licence choice.
- [ ] Promote to `VERIFIED RELEASE CANDIDATE` only after all required evidence passes at one frozen commit.
- [ ] Promote to `RELEASED` only after explicit owner approval.
