# ProofGrid v1.4 — Source-Bound Declaration Evidence Bundle

## Purpose

v1.4 binds three already-accepted evidence dimensions for the same exact admitted declaration without performing an environmental calculation:

1. hardened v1.1.1 source-declared environmental indicators;
2. v1.3 declared reference-product/reference-basis evidence;
3. v1.3.1 reference-exchange amount semantics.

Bounded verdict:

`DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE`

## Accepted parents

- hardened v1.1.1 head `61e6f86c3c633ab8191539292f36cbb1706689f1`;
- accepted v1.3 head `77931d81ae9857eb33b3cecaf8f9180f0c2b7e4a`;
- accepted v1.3.1 head `b8d25bc7982434bf94e763d291d3be08bc9241d7`.

Hosted acceptance resolves the exact same-repository artifacts for those accepted heads and verifies their SHA-256 values before binding them.

## Identity requirements

The binder rejects unless the declared-indicator evidence, reference-basis evidence, and hardened canonical source agree on:

- source SHA-256;
- process XML SHA-256;
- process dataset UUID;
- ILCD+EPD version.

For v1.2 the hardened canonical source must preserve the exact accepted v0.9.1 validator/profile stack. For v1.3 profile validation must remain explicitly false while XSD/master-data conformance remains true.

The v1.3.1 semantics evidence must match the exact reference exchange and declared exchange amount in the v1.3 basis record, and `resultingAmount` must remain absent under policy:

`MEAN_AMOUNT_ACCEPTED_ONLY_WHEN_RESULTING_AMOUNT_ABSENT`

## Dimension separation

v1.4 deliberately preserves two different units:

- environmental-result unit: `kg CO2 eqv.`;
- product/reference-basis unit for the pinned controls: `kg`.

They are different dimensions. v1.4 does not divide, multiply, convert, or otherwise transform them.

## No-calculation boundary

A successful v1.4 record remains:

- `calculated=false`;
- `environmental_values_transformed=false`;
- `building_quantity_multiplication_performed=false`;
- `aggregation_performed=false`;
- `unit_conversion_performed=false`;
- `scientific_validation_performed=false`;
- `professional_review_performed=false`;
- `certified=false`.

The bundle can support a future separately specified calculation gate, but it is not that gate.

## Fail-closed controls

The implementation rejects source/process/version substitution, parent receipt/content tampering, forged v1.2 stack identity, v1.3 profile promotion, unresolved `resultingAmount`, amount-policy mismatch, cross-version semantics substitution, environmental/product unit conflation, certification promotion, and any attempt to treat the bundle as a building-level calculated impact.

## Provenance rule

The hosted gate consumes only accepted RegenExcalibur evidence artifacts. It retains the derived v1.4 bundle/receipt and does not retain third-party source packages or provider data.

**Tracks:** #38.

**Attribution:** RegenExcalibur / 1JGM
