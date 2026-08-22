# ProofGrid v2.3 — Declared Source Inventory Gap Ledger

This gate introduces an explicit inventory-gap layer **before any whole-building completeness claim is possible**.

It inventories exactly three deterministic synthetic source entries:

1. first accepted evidence-covered IFC contribution;
2. second accepted evidence-covered IFC contribution;
3. one deterministic inventory-only IFC element with **no accepted environmental contribution**.

The positive control therefore reports:

- inventory entries: `3`
- evidence-covered: `2`
- evidence-uncovered: `1`
- exact coverage ratio: rational `2/3`

The uncovered entry is never assigned an environmental value and `assumed_zero=false`.

`DECLARED_SOURCE_INVENTORY_GAP_LEDGER_VERIFIABLE` does **not** mean:

- whole-building completeness;
- whole-model inventory completeness;
- regulatory LCA completeness;
- scientific validation;
- professional review;
- certification.
