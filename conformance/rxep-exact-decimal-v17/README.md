# ProofGrid v1.7 — RXEP Exact-Decimal Calculated Evidence

## Purpose

v1.7 binds the accepted, independently reproduced v1.6 environmental contribution into RXEP without losing exact Decimal authority.

The accepted calculation is:

`15559.479677163699 kg CO2 eqv.`

RXEP's legacy generic numeric `measurement.value` remains available for backward-compatible display/interoperability. For v1.7 exact calculated evidence it is explicitly **non-authoritative**.

The evidence authority is:

```text
measurement.value_decimal = "15559.479677163699"
measurement.decimal_value_is_authority = true
measurement.numeric_value_is_authority = false
```

## Backward compatibility

The base RXEP schema remains compatible with legacy envelopes that only contain numeric `measurement.value`.

When `measurement.value_decimal` is present, the schema additionally requires the authority flags above.

## Evidence-state boundary

The v1.6 calculation has been independently reproduced as software, but the environmental claim itself has not received independent scientific/professional review.

Therefore the v1.7 envelope is exactly:

```text
review.state = CALCULATED
review.reviewer = null
```

and it may not be promoted by this gate to `REVIEWED`, `INDEPENDENTLY_VERIFIED`, or `CERTIFIED`.

## Parent evidence

v1.7 pins:

- accepted v1.6 calculation record/file/receipt hashes;
- accepted v1.6.1 independent software-reproduction receipt/file hashes;
- exact indicator/module/scenario and environmental unit;
- exact source-authoritative Decimal result.

## Bounded verdict

`RXEP_EXACT_DECIMAL_CALCULATION_EVIDENCE_VERIFIABLE`

## Non-claims

v1.7 performs no new environmental arithmetic, aggregation, unit conversion, scientific validation, professional review, regulatory approval, or certification.

The envelope represents one exact mapped declared contribution, not a complete building LCA.

**Attribution:** RegenExcalibur / 1JGM
