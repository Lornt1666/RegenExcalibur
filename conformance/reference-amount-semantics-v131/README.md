# ProofGrid v1.3.1 — Reference Exchange Amount Semantics

## Purpose

v1.3.1 hardens the accepted v1.3 declared-reference-basis extractor against a future ILCD process exchange that contains both `meanAmount` and `resultingAmount`.

The accepted v1.3 head remains immutable:

`77931d81ae9857eb33b3cecaf8f9180f0c2b7e4a`

For the pinned InData v1.2/v1.3 wood-panel controls, hosted research has frozen:

- quantitative reference: `Reference flow(s)`;
- reference exchange internal ID: `42`;
- `meanAmount`: lexical `1.0`, Decimal `1`;
- `resultingAmount`: absent/null in both controls.

Therefore the accepted v1.3 fixture did not choose between competing source amount values.

## v1.3.1 policy

The explicit policy is:

`MEAN_AMOUNT_ACCEPTED_ONLY_WHEN_RESULTING_AMOUNT_ABSENT`

The gate:

1. verifies the exact RXEP v0.2 parent and admitted source bytes;
2. resolves the single quantitative-reference exchange by exact internal ID;
3. preserves `meanAmount` lexical + canonical Decimal evidence;
4. preserves `resultingAmount` lexical + canonical Decimal evidence when present;
5. fails closed whenever `resultingAmount` is present, pending a separately specified format-semantic policy;
6. permits the accepted v1.3 basis path only when `resultingAmount` is absent.

## Bounded verdict

A successful absence case may emit:

`REFERENCE_EXCHANGE_AMOUNT_SEMANTICS_RESOLVED_VERIFIABLE`

with:

- `basis_selection_permitted=true` for the already-proven reference-basis gate;
- `building_quantity_multiplication_permitted=false`;
- `calculated=false`;
- `environmental_values_transformed=false`;
- `unit_conversion_performed=false`;
- `scientific_validation_performed=false`;
- `professional_review_performed=false`;
- `certified=false`.

## Fail-closed boundary

A non-null `resultingAmount` does **not** become an alternate basis automatically, even if it numerically equals `meanAmount`. Equality is not treated as semantic authority.

Malformed, non-finite, duplicate, or competing `resultingAmount` evidence is rejected before the accepted v1.3 basis extractor is allowed to proceed.

This gate does not authorize building-level quantity multiplication, LCA conclusions, professional review, regulatory approval, provider/programme-operator authority, or certification.

**Tracks:** #35 and semantic hardening in #27.

**Attribution:** RegenExcalibur / 1JGM
