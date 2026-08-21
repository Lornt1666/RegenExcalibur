# RX Evidence Protocol (RXEP) v0.1

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
