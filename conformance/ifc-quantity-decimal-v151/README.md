# ProofGrid v1.5.1 — Exact-Decimal IFC Declared Quantity Evidence

## Purpose

v1.5.1 hardens accepted v1.5 before the first environmental calculation by rebinding the mapped IFC quantity to the **exact numeric token in the hashed STEP source**.

Accepted parent:

- v1.5 PR #46;
- exact accepted head `37f097851c4d9b66c48c4b95a9552dbc80996bb3`;
- verdict `IFC_DECLARATION_PRODUCT_MAPPING_VERIFIABLE`;
- exact accepted artifact `9451317205`.

Bounded verdict:

`IFC_DECLARED_QUANTITY_EXACT_DECIMAL_VERIFIABLE`

## Authority rule

The raw STEP numeric token is calculation-preparation evidence authority.

The IfcOpenShell/JSON numeric value retained by v1.5 is used only as a consistency check:

- `source_token_is_authority=true`;
- `parser_numeric_value_is_authority=false`.

The gate does not use Python binary floating point to create the canonical quantity.

## STEP binding

The parser scans STEP statements with awareness of quoted strings, escaped quotes, nested argument parentheses, comments, and statement terminators. It resolves the exact mapped quantity STEP ID and requires exactly one matching entity definition.

Initial scope is deliberately narrow:

- entity type `IFCQUANTITYWEIGHT`;
- exact mapped quantity name;
- source lexical numeric token;
- finite canonical Decimal;
- accepted mapped unit identity `kg`.

The exact hosted source token is frozen from the deterministic accepted v1.5 IFC fixture at CI time rather than guessed here.

## Source integrity

The hosted gate reconstructs the accepted deterministic synthetic IFC4 source and requires its SHA-256 to equal the final accepted v1.5 source:

`23046f33df40fae4354fd085c2d72c6c9eaab3a45b2d46e77d8f9531041954c6`

Only the synthetic fixture's generated STEP `FILE_NAME` timestamp is canonicalized. Real user/provider IFC source bytes must never be rewritten by this gate.

## No-calculation boundary

Successful v1.5.1 evidence remains:

- `calculation_performed=false`;
- `environmental_calculation_performed=false`;
- `building_quantity_multiplication_performed=false`;
- `unit_conversion_performed=false`;
- `scientific_validation_performed=false`;
- `professional_review_performed=false`;
- `certified=false`.

No environmental result is scaled by this gate.

## Fail-closed controls

Reject source-hash mismatch, mapping record/receipt tamper, missing or duplicate quantity STEP IDs, wrong entity type/name, malformed or non-finite numeric tokens, parser/source numeric disagreement, non-kg mapped unit, implicit conversion, and calculation/certification promotion.

## Downstream boundary

v1.5.1 is the blocking prerequisite for #47. Only after this exact-decimal quantity evidence is accepted may a later calculation gate use the mapped quantity as Decimal authority.

**Tracks:** #49. Blocks #47.

**Attribution:** RegenExcalibur / 1JGM
