# PromptOS v4.0 RC1 Release Checklist

## Source and packaging

- [x] Version recorded.
- [x] Normalized v3.2 constitution recorded.
- [x] Requirement identifiers recorded.
- [x] Runtime kernel separated from conditional modules.
- [x] Package metadata present.
- [x] Runtime package data declared.
- [x] Explicit licence status present.
- [ ] Generate and commit final source checksums after review changes stop.

## Deterministic verification

- [ ] GitHub Actions Python 3.11 unit suite passes.
- [ ] GitHub Actions Python 3.12 unit suite passes.
- [ ] All 120 conformance cases pass in CI.
- [ ] Corpus output is exactly 60/30/30.
- [ ] Wheel builds without runtime dependencies.
- [ ] Installed-wheel smoke conformance passes outside source tree.

## Security and authority

- [x] Source SHA-256 recorded in each package.
- [x] Raw source angle brackets excluded from encoded source.
- [x] Source round-trip validation implemented.
- [x] Exactly one compiler-owned closing delimiter required.
- [x] Consequential mode requires specific authorized actions.
- [x] Authorized and prohibited action overlap rejected.
- [x] DO_NOT_EXECUTE remains default.
- [ ] Run multilingual and Unicode-confusable injection corpus.
- [ ] Run target-model adversarial source-boundary evaluation.

## Evaluation

- [x] Deterministic 120-case seeded corpus implemented.
- [x] Static 60/30/30 partitions implemented.
- [x] Static holdout limitation disclosed.
- [ ] Create independent private holdout.
- [ ] Run v3.2 monolith baseline.
- [ ] Run minimal direct-prompt baseline.
- [ ] Run PromptOS compiled runtime candidates.
- [ ] Randomize pairwise candidate order.
- [ ] Control for verbosity.
- [ ] Conduct blinded human review of critical samples.
- [ ] Report category-level failures and confidence intervals.

## Release truthfulness

- [x] RC state is `IMPLEMENTED — EVALUATION PENDING`.
- [x] No claim of perfection.
- [x] No claim of universal superiority.
- [x] No claim that prompt injection is solved.
- [x] No claim of production readiness.
- [ ] Promote to `VERIFIED RELEASE CANDIDATE` only after independent evaluation gates pass.
- [ ] Promote to `RELEASED` only after owner approval and final evidence review.
