# ProofGrid v2.0 — exact-Decimal two-member PARTIAL total

v2.0 is the first ProofGrid gate that performs arithmetic across more than one admitted environmental contribution.

It consumes only the exact accepted v1.9 two-member contribution set and calculates:

`15559.479677163699 + 7779.7398385818495 = 23339.2195157455485 kg CO2 eqv.`

## Authority and ordering

- the accepted v1.9 set record/file/receipt identities are hard-pinned;
- both member semantic identities must be the exact accepted distinct identities;
- member `value_decimal` strings are the only numeric authority;
- members are ordered by semantic-identity SHA-256 before receipt emission;
- generic JSON floats are not used for arithmetic.

## Completeness boundary

The source set is `PARTIAL`, therefore the total remains `PARTIAL`.

v2.0 does not claim:

- a whole-building LCA;
- declared-scope completeness;
- missing contributions/modules are zero;
- unit conversion;
- scenario inference;
- scientific validation;
- professional review;
- regulatory approval;
- certification.

## Reproducibility

Two independent GitHub-hosted replicas download and SHA-verify the exact v1.9 artifact, produce the same canonical total/receipt bytes, and a third job byte-compares those outputs.

**Attribution:** RegenExcalibur / 1JGM
