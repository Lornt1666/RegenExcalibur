# PromptPackage Contract

A compiled package contains:

- package and PromptOS versions;
- original-source SHA-256;
- safely encoded source;
- selected operation;
- selected modules;
- selected adapter;
- risk classification;
- routing reasons;
- Prompt Intermediate Representation;
- compiled runtime prompt;
- Foundry completion state;
- underlying-project state;
- request warnings;
- validation report.

The package is designed for inspection, persistence, comparison, and evaluation. Its existence proves prompt-package compilation only. It does not prove that a target model obeyed the prompt or that an underlying project was executed.
