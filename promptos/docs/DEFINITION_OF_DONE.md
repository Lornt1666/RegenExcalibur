# Definition of Done

## RC1 implementation done

- Source and package metadata exist.
- Kernel, modules, adapters, router, PIR, compiler, validator, and CLI exist.
- JSON schemas exist.
- Tests and deterministic corpus exist.
- CI and wheel-smoke procedure exist.
- Security, evaluation, migration, traceability, and status documentation exist.
- Release state is honest and bounded.

## RC1 verification done

- Branch CI passes for all configured Python versions.
- Conformance passes 120/120.
- Wheel installs and runs outside the source tree.
- No critical review defect remains.

## Release-candidate verification done

- Independent holdout is preserved.
- External model baselines are run.
- Hard gates pass.
- Blinded pairwise target is met.
- Critical human review is complete.
- Owner approves the release state.

Imagined future improvements do not prevent closure. Failed gates do.
