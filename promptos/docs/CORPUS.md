# Seeded Conformance Corpus

The deterministic corpus contains 120 cases: ten variants across twelve families.

The expected result for each case contains:

- operation;
- required module subset;
- risk class;
- forbidden-behaviour categories.

The corpus is generated in code to avoid committing repetitive bulk data. `promptos corpus` materializes JSONL partitions for inspection or CI artifacts.

Partitioning uses a fixed seed:

- development: 60;
- validation: 30;
- static holdout: 30.

This is a deterministic regression corpus. It is not represented as an independent semantic holdout.
