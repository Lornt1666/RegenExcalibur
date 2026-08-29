# Prompt Intermediate Representation

The PIR is the machine-readable contract between request interpretation and prompt compilation.

Core fields:

- source provenance;
- selected operation;
- objective;
- deliverable;
- hard requirements;
- preferences;
- constraints;
- non-goals;
- invariants;
- confirmed and unconfirmed tools;
- prohibited actions;
- permissions;
- assumptions;
- blockers;
- selected modules;
- model adapter;
- risk;
- completion target;
- Foundry state;
- underlying-project state;
- maximum refinement passes;
- acceptance criteria.

The PIR is included in each PromptPackage so routing and authority decisions are inspectable rather than hidden inside prose.
