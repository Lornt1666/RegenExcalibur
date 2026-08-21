# ProofGrid v1.6 — Exact-Decimal Mapped Declared Result Scaling

## Purpose

This gate performs ProofGrid's first bounded environmental multiplication.

It scales exactly **one source-declared environmental result row** using exactly **one source-authoritative IFC quantity Decimal** and exactly **one identity-verified declaration reference basis**.

The accepted evidence chain is:

`v1.5.1 exact STEP quantity Decimal → v1.5 explicit mapping → v1.4.1 v1.3 product/reference closure → v1.4 v1.3 declaration bundle → one exact selected row → Decimal-only result`

## First bounded control

- IFC quantity source token: `1000.`
- IFC quantity canonical Decimal: `1000`
- quantity unit: `kg`
- declaration reference basis: `1 kg`
- indicator: `GWP-total`
- indicator UUID: `6a37f984-a4b3-458a-a20a-64418c145fa2`
- module: `A1-A3`
- scenario: `null`
- declared result: `15.559479677163699 kg CO2 eqv.`

Formula:

`(1000 / 1) × 15.559479677163699 = 15559.479677163699 kg CO2 eqv.`

The v1.5 JSON/parser value `1000.0` is never calculation authority.

## Exact-parent policy

The first v1.6 implementation is intentionally pinned to the exact accepted parent content/file/receipt digests. Merely recomputing internally consistent hashes is not sufficient to create new accepted parent evidence.

This prevents self-consistent forged or cross-version parent records from silently becoming calculation authority.

## Deliberately absent capabilities

v1.6 has no:

- module aggregation;
- scenario inference;
- missing-module zeroing;
- unit-conversion table;
- fuzzy/name mapping;
- multi-element building aggregation;
- scientific validation;
- professional LCA review;
- certification.

A successful result is one software-scaled declared contribution, **not a complete building LCA**.

## Bounded verdict

`MAPPED_DECLARED_RESULT_SCALED_VERIFIABLE`

Required non-claim flags remain:

- `aggregation_performed=false`
- `missing_modules_are_zero=false`
- `unit_conversion_performed=false`
- `scenario_inference_performed=false`
- `fuzzy_mapping_performed=false`
- `scientific_validation_performed=false`
- `professional_review_performed=false`
- `certified=false`

**Attribution:** RegenExcalibur / 1JGM
