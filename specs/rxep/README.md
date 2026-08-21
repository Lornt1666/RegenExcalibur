# RX Evidence Protocol (RXEP) v0.2

RXEP is a minimal evidence envelope for RegenExcalibur systems.

## Design objective

A third party should be able to answer:

- What is being claimed?
- About what subject?
- What measurement supports the claim?
- Which inputs and sources were used?
- Which method and software version produced it?
- Which jurisdiction or standard context applies?
- What is the review state?
- What are the limitations?
- Can the artifact's integrity be checked?

## Runtime structural conformance

ProofGrid v0.2 validates canonical inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` receipt. The reference implementation currently validates:

- `project.json` against `schemas/building.schema.json`;
- `materials.json` against `schemas/materials.schema.json`;
- generated evidence against `specs/rxep/evidence-envelope.schema.json`.

Unknown project/material properties and invalid quantities fail closed under the current schemas.

Structural conformance does **not** establish source authority, scientific validity, code compliance, engineering adequacy, or professional certification.

## Minimal envelope

See `evidence-envelope.schema.json`.

Core fields:

- `id`
- `subject`
- `claim`
- `measurement`
- `methodology`
- `sources`
- `software`
- `jurisdiction`
- `review`
- `limitations`
- `integrity`

## Integrity is not truth

A cryptographic hash proves that bytes have not changed relative to the recorded digest. It does not prove that a source is scientifically valid or that a professional conclusion is correct.

## Review-state invariant

Allowed values:

- `CLAIMED`
- `CALCULATED`
- `REVIEWED`
- `INDEPENDENTLY_VERIFIED`

The reference implementation currently emits `CALCULATED` evidence and an overall `VERIFIABLE` result when structural validation and integrity generation succeed.

`VERIFIABLE` is **not** `CERTIFIED`.
