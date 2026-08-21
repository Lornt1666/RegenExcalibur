# ProofGrid v1.4.1 — Declaration Product Identity Closure

## Purpose

v1.4.1 hardens accepted v1.4 evidence fusion by preserving the complete declaration product/reference identity needed before any IFC material can be explicitly mapped to the declaration.

Accepted parents:

- v1.4 head `9066ab770afab6d639708c12c669184a23afa575`;
- v1.3 head `77931d81ae9857eb33b3cecaf8f9180f0c2b7e4a`.

Bounded verdict:

`DECLARATION_PRODUCT_IDENTITY_CLOSURE_BOUND_VERIFIABLE`

## Preserved closure

The v1.4.1 record binds and carries forward the exact accepted v1.3 identity graph:

- process quantitative-reference type;
- reference exchange internal ID;
- exchange amount lexical + Decimal;
- product-flow UUID **and version**;
- product-flow multilingual names;
- product-flow source SHA-256;
- product-flow reference flow-property internal ID;
- flow-property UUID/version/names/master SHA-256;
- flow-property mean lexical + Decimal;
- reference unit-group UUID;
- unit-group UUID/version/master SHA-256;
- reference unit internal ID/name;
- reference-unit factor lexical + Decimal;
- accepted declared reference basis.

For the exact pinned public controls, the closure remains an identity chain resolving to:

`1 kg of the referenced wood-panel product flow`

No universal EPD rule is inferred.

## Parent binding

v1.4.1 independently verifies:

- v1.4 record + receipt integrity;
- v1.3 reference-basis record + receipt integrity;
- the exact v1.4 parent basis hashes against the supplied v1.3 files;
- source SHA, process XML SHA, process UUID, and ILCD+EPD version equality;
- product UUID/version closure;
- flow-property → unit-group closure;
- reference-unit identity;
- v1.4 amount-semantics agreement with the v1.3 process reference.

## No-calculation boundary

Successful evidence remains:

- `calculated=false`;
- `environmental_values_transformed=false`;
- `building_quantity_multiplication_performed=false`;
- `aggregation_performed=false`;
- `unit_conversion_performed=false`;
- `scientific_validation_performed=false`;
- `professional_review_performed=false`;
- `certified=false`.

The first gate accepts only the proven identity factors (`1`, `1`, `1`). Any non-identity amount/flow-property/unit factor requires a later separately specified calculation/conversion gate.

v1.4.1 performs no IFC/material mapping. It exists to make the exact declaration product identity complete enough for v1.5 to reference without weakening the mapping contract to UUID-only matching.

**Tracks:** #43. Blocks #42.

**Attribution:** RegenExcalibur / 1JGM
