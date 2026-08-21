# ProofGrid v1.8 — Contribution-Set Admission

v1.8 creates a canonical membership container for exact RXEP environmental contributions **before any multi-contribution arithmetic is introduced**.

Bounded verdict:

`ENVIRONMENTAL_CONTRIBUTION_SET_ADMISSION_VERIFIABLE`

## First accepted scope

The first control is intentionally a one-member `PARTIAL` set containing the accepted v1.7 exact-Decimal RXEP contribution.

This is deliberate. ProofGrid does not fabricate a second environmental contribution merely to demonstrate addition.

## Member binding

Every member must bind both:

1. an exact `CALCULATED` RXEP envelope + receipt; and
2. the exact mapped declared-result calculation + receipt referenced by that envelope.

The semantic member identity includes:

- IFC source SHA-256;
- element GlobalId;
- product-flow UUID/version;
- quantity-record content SHA-256;
- mapping-record content SHA-256;
- declaration-closure content SHA-256;
- declaration-bundle content SHA-256;
- indicator code/UUID;
- module;
- explicit scenario;
- exact Decimal result;
- environmental unit.

This rejects the same calculation even if someone rewraps it under another RXEP ID or set-member ID.

## Compatibility policy

The v1.8 request declares one exact compatibility tuple:

- indicator code/UUID;
- environmental unit;
- module;
- scenario.

Every admitted member must match it exactly. No unit conversion, module aggregation, scenario inference, or name/fuzzy matching is available.

## Completeness policy

v1.8 supports only:

`completeness_status=PARTIAL`

A later gate must separately define and prove any stronger completeness state. Member count cannot imply whole-building or declared-scope completeness.

## Deliberate absences

- `aggregation_performed=false`
- `sum_performed=false`
- `missing_contributions_are_zero=false`
- `missing_modules_are_zero=false`
- `unit_conversion_performed=false`
- `scenario_inference_performed=false`
- `duplicate_members_permitted=false`
- `scientific_validation_performed=false`
- `professional_review_performed=false`
- `certified=false`

v1.8 admits evidence membership only. It does not calculate a set total and does not claim a complete building LCA.

**Attribution:** RegenExcalibur / 1JGM
