# Mandatory Evaluation Gate

PromptOS v4.0 RC1 must not advance beyond `IMPLEMENTED — EVALUATION PENDING` until all of the following are evidenced at a frozen commit:

- branch CI passes on Python 3.11 and 3.12;
- all 16 unit tests pass;
- deterministic conformance passes 120/120;
- the wheel installs and runs outside the source tree;
- an independent private holdout is preserved;
- v3.2, minimal, target-native, and PromptOS baselines are run under equivalent conditions;
- hard safety/authority/evidence gates pass;
- blinded pairwise evaluation meets the selected threshold;
- critical cases receive human review;
- owner approval is recorded.

Until then, prohibited claims include `perfect`, `universally optimal`, `verified category leader`, `production ready`, and `released`.
