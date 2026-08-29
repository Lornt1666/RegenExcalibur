# Module Ablation Plan

PromptOS must establish that each conditional module improves relevant tasks enough to justify its context cost.

For each module:

1. Select cases where the module should apply.
2. Compile Candidate A with the module.
3. Compile Candidate B without the module.
4. Hold the source, adapter, model settings, and output schema constant.
5. Randomize presentation order.
6. Evaluate hard gates first.
7. Compare task success, intent fidelity, domain correctness, safety, latency, and token use.
8. Retain the module only when the gain is material and no critical regression appears.

Modules to test:

- research;
- software;
- built_environment;
- creative;
- business;
- education;
- innovation;
- definitive_completion;
- security;
- tooling;
- professional_boundaries.

A module may remain constitutionally important while being excluded from a runtime where it is non-applicable.
