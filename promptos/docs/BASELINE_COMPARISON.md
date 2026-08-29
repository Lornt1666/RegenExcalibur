# Baseline Comparison Protocol

PromptOS must be compared against at least three baselines on the same cases:

1. The v3.2 constitutional monolith.
2. A minimal direct prompt containing only the user's request and output format.
3. A target-model-specific prompt following the provider's current documented guidance.

For every case, preserve:

- source request;
- target model/version;
- model settings;
- available tools;
- output schema;
- run time;
- token counts;
- monetary cost where applicable;
- candidate outputs;
- hard-gate results;
- blinded pairwise judgments.

Candidate labels and ordering must be randomized before review. Length must be measured, and evaluators must be warned not to reward verbosity by itself.

PromptOS advances only when it improves relevant quality without violating a hard gate or imposing disproportionate context, latency, or cost.
