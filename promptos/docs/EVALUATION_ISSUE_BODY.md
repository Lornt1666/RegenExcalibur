# Suggested Evaluation Tracking Issue

## Objective

Advance PromptOS v4.0 RC1 from `IMPLEMENTED — EVALUATION PENDING` to `VERIFIED RELEASE CANDIDATE` using evidence rather than additional prompt expansion.

## Required work

- [ ] Confirm branch CI at exact head.
- [ ] Remove or squash nonfunctional marker documents before merge.
- [ ] Generate final checksums.
- [ ] Freeze an independent private holdout.
- [ ] Run v3.2, minimal, target-native, and PromptOS baselines.
- [ ] Run hard-gate validators.
- [ ] Conduct randomized blinded pairwise grading.
- [ ] Conduct human review for critical samples.
- [ ] Measure token length, latency, and cost.
- [ ] Record regressions and exact-head evidence.
- [ ] Obtain owner approval before state promotion.

## Completion condition

All mandatory release gates pass at one immutable commit and the owner approves promotion.
