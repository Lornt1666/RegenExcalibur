# Operation Modes

- `AUTO` — apply deterministic operation precedence.
- `CREATE` — construct a new prompt from an objective or rough request.
- `REPAIR` — preserve valid intent and correct defects in an existing prompt.
- `MERGE` — reconcile multiple prompts into one architecture.
- `AUDIT` — report strengths, defects, gaps, and remediation without automatic rewriting.
- `OPTIMIZE` — improve a named objective under constraints and regression checks.
- `ADAPT` — port a prompt to another model, environment, audience, or context budget.
- `COMPRESS` — reduce context while preserving critical controls.
- `EXPAND` — add only materially missing detail.
- `TRANSLATE` — preserve semantics, modality, variables, and priority across languages.
- `REVERSE_ENGINEER` — reconstruct an underlying specification with uncertainty labels.
- `STANDARDIZE` — map content into a defined schema or standard without false certification.

Exactly one operation module is loaded into a runtime prompt.
