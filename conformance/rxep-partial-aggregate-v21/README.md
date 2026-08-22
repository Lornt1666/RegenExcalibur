# ProofGrid v2.1 — RXEP exact-Decimal PARTIAL aggregate evidence

v2.1 binds the accepted v2.0 two-member partial-set total into RXEP without changing the arithmetic or promoting completeness/review/certification state.

Accepted parent:

- v2.0 head `2fc2c450b1f37cb2c355ff12d09622ad5f094eec`
- artifact `9464376763`
- artifact ZIP SHA-256 `9b63ae70c4db86e2b01577bcc433471ad705a3aedcc590cf028fd874d95e677b`
- aggregate record content `8b47dfb87f1be4e1979666f85f7da58c41c00e48c92b7cd4a2f3c9fdd62e8ed0`
- aggregate receipt `991de0efd5c71c067391c8e5fa7bbf81fd55febb72a4cfe8cf5a10f09ac238d4`
- independent comparison receipt `74f5ef72a9f1fdd6c8145bc3291e0bfbb9373c94cbf1b048822e291266b7f839`
- exact value `23339.2195157455485 kg CO2 eqv.`

## Evidence authority

`measurement.value_decimal` is the exact evidence authority. The generic JSON `measurement.value` exists only as a non-authoritative display/interoperability number and is explicitly marked `numeric_value_is_authority=false`.

## State boundary

The envelope remains:

- `review.state=CALCULATED`
- `completeness_status=PARTIAL`
- `aggregation_scope=ADMITTED_SET_MEMBERS_ONLY`
- `whole_building_lca_claimed=false`
- `declared_scope_complete_claimed=false`
- `missing_contributions_are_zero=false`
- `missing_modules_are_zero=false`
- `unit_conversion_performed=false`
- `scenario_inference_performed=false`
- `scientific_validation_performed=false`
- `professional_review_performed=false`
- `certified=false`

The RXEP binder performs no new sum. It only verifies and binds the already accepted v2.0 aggregate.

## Acceptance

Two independent hosted replicas must independently download/SHA-verify the accepted v2.0 artifact, construct byte-identical RXEP records/receipts, and a comparison job must reject a tampered v2.0 parent.

Bounded verdict:

`RXEP_EXACT_DECIMAL_PARTIAL_AGGREGATE_EVIDENCE_VERIFIABLE`

This is not a complete building LCA or a certified environmental declaration.

**Attribution:** RegenExcalibur / 1JGM
