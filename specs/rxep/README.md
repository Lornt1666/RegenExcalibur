# RX Evidence Protocol (RXEP) v0.3

RXEP is a minimal evidence envelope for RegenExcalibur systems.

## Design objective

A third party should be able to answer:

- What is being claimed?
- About what subject?
- What measurement supports the claim?
- Which exact inputs and source records were used?
- Which source bytes and registry version were used?
- Which method and software version produced the result?
- Which lifecycle/system boundary and indicator apply?
- Which jurisdiction or standard context applies?
- What is the review state?
- What are the limitations?
- Can the artifact's integrity be checked?

## Runtime structural and provenance conformance

ProofGrid v0.3 validates canonical inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` receipt. The reference implementation validates:

- `project.json` against `schemas/building.schema.json`;
- `materials.json` against `schemas/materials.schema.json`;
- `lca-sources.json` against `schemas/lca-source-records.schema.json`;
- generated evidence against `specs/rxep/evidence-envelope.schema.json`.

The environmental source layer additionally verifies local source-content SHA-256 values, requires exact `source_record_id` resolution, prohibits implicit unit conversion, and rejects incompatible lifecycle/system boundaries or indicators inside one v0.3 calculation.

Structural/provenance conformance does **not** establish source authority, scientific validity, code compliance, engineering adequacy, professional LCA review, program-operator verification, or certification.

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

The v0.3 reference receipt additionally records the environmental registry hash, exact source-record IDs, canonical source-record digests, lifecycle/system boundary, indicator, and exact-match unit policy.

## Integrity is not truth

A cryptographic hash proves that bytes have not changed relative to the recorded digest. It does not prove that a source is scientifically valid or that a professional conclusion is correct.

Likewise, `SOURCE_REGISTRY_VERIFIABLE` means the registry structure, identities, references, and source-content hashes passed the declared machine checks. It is not environmental certification.

## Review-state invariant

Allowed RXEP evidence states:

- `CLAIMED`
- `CALCULATED`
- `REVIEWED`
- `INDEPENDENTLY_VERIFIED`

The reference implementation emits `CALCULATED` evidence and an overall `VERIFIABLE` result when all declared schema, provenance, source-resolution, boundary, unit, deterministic-calculation, and integrity checks succeed.

`VERIFIABLE` is **not** `CERTIFIED`.
