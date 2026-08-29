# Next Milestone: Independent Evaluation

The next milestone is not another prompt section. It is evidence.

1. Confirm branch CI passes on Python 3.11 and 3.12.
2. Freeze the RC commit SHA.
3. Generate final checksums.
4. Build a private independent holdout that is not committed before testing.
5. Compile outputs from v3.2, PromptOS RC1, a minimal baseline, and a target-model-native baseline.
6. Run hard-gate validation.
7. Conduct randomized blinded model and human pairwise review.
8. Measure prompt length, output quality, latency, and cost.
9. Repair only observed failures, with regression cases.
10. Promote the state only when the evidence meets the release gates.

The milestone terminal state is `VERIFIED RELEASE CANDIDATE`, not “perfect.”
