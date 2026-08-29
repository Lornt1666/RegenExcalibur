# Evidence Manifest

## Deterministic evidence paths

- `tests/test_promptos.py`
- `src/regen_promptos/core.py`
- `src/regen_promptos/resources/runtime.json`
- `src/regen_promptos/schemas/`
- `.github/workflows/promptos-v4.yml`
- `releases/v4.0.0-rc1/release-manifest.json`
- `releases/v4.0.0-rc1/RELEASE_CHECKLIST.md`

## Generated evidence

The workflow generates, but does not commit:

- unit-test logs;
- `conformance-report.json`;
- 60/30/30 corpus partitions and manifest;
- wheel distribution;
- installed-wheel smoke result.

## External evidence still required

- private independent holdout;
- baseline outputs;
- blinded pairwise judgments;
- human critical-case review;
- token, latency, and cost measurements;
- owner release approval.
