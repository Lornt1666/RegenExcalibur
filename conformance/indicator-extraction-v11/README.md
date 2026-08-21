# ProofGrid v1.1 — Declared Environmental Indicator Extraction Research

ProofGrid v1.1 is stacked on accepted v1.0 head:

`60ae4cdde4121a1eed656c40b4699e255b72d22f`

The implementation is intentionally **research-gated**. No environmental-value parser may be represented as accepted until the hosted research lane freezes the exact upstream catalogue and XML structure used to bind declared values.

## What is already established

Pinned InData ILCD+EPD v1.3 upstream:

`InDataWG/ILCD-EPD-Data-Format@7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`

The upstream repository publishes machine-readable EN 15804+A2 indicator identifier tables, including:

`doc/identifiers/EN15804+A2_EF3.0_indicators.csv`

That table explicitly carries:

- indicator UUID;
- indicator version where defined;
- English/German names;
- canonical unit;
- unit-group UUID.

Example from the pinned table:

- GWP-total UUID: `6a37f984-a4b3-458a-a20a-64418c145fa2`
- version: `04.00.016`
- name: `Global Warming Potential - total (GWP-total)`
- unit: `kg CO2 eqv.`
- unit-group UUID: `1ebf3012-d0db-4de2-aefd-ef30cedb0be1`

This identifier tuple—not a fuzzy label—is the starting point for v1.1 identity mapping.

## What is *not* yet accepted

The following must be discovered and frozen by hosted research before extractor semantics are implemented:

- exact v1.2/v1.3 XML path from process dataset → exchange/indicator → module/scenario → declared amount;
- whether amount semantics use `meanAmount`, extension attributes/elements, or another exact field for each supported version;
- how module groups and scenarios are represented and scoped;
- exact relationship between exchange references and indicator catalogue UUID/version;
- whether the declared exchange unit already equals the catalogue unit;
- treatment of not-declared/not-applicable/missing modules;
- structural differences between v1.2 and v1.3.

## Non-negotiable extraction rules

A future accepted extractor must:

- match indicator identity by exact UUID/version against a pinned catalogue;
- preserve the source lexical number and parse it with `Decimal`;
- bind every output value to an exact module and scenario identity;
- require exact declared/canonical unit identity or fail closed;
- never convert units implicitly;
- never treat missing modules as zero;
- never derive values from validator warnings;
- never aggregate modules without a separately specified calculation method;
- never turn extraction into scientific validity, professional review, provider authority, programme-operator/BBSR approval, or certification.

## Research verdict

The research lane may emit only a bounded research verdict such as:

`DECLARED_INDICATOR_STRUCTURE_RESEARCH_VERIFIABLE`

That verdict means the exact upstream files and observed structural paths were recorded reproducibly. It does **not** mean environmental indicator extraction has been implemented or accepted.

**Attribution:** RegenExcalibur / 1JGM
