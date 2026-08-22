# ProofGrid v2.1 — RXEP evidence for the exact PARTIAL set total

v2.1 performs **no new environmental arithmetic**. It binds the accepted v2.0 two-member exact-Decimal total into RXEP while preserving the source set's `PARTIAL` completeness and the environmental evidence state `CALCULATED`.

Accepted parent value:

`23339.2195157455485 kg CO2 eqv.`

## Exact Decimal authority

The RXEP envelope uses:

```text
measurement.value_decimal = "23339.2195157455485"
measurement.decimal_value_is_authority = true
measurement.numeric_value_is_authority = false
```

The generic JSON numeric value is display/interoperability data only.

## Evidence state

The envelope remains:

```text
review.state = CALCULATED
review.reviewer = null
completeness_status = PARTIAL
```

v2.0 was independently reproduced as software. That does **not** make the environmental claim independently scientifically verified.

## Parent pinning

v2.1 hard-pins accepted v2.0 head/artifact and the aggregation record, receipt, and independent-comparison receipt identities before RXEP binding.

## Non-claims

- not a whole-building LCA;
- not declared-scope complete;
- missing contributions/modules are not zero;
- no unit conversion;
- no scenario inference;
- no independent environmental-claim verification;
- no scientific validation;
- no professional review;
- no regulatory approval;
- no certification.

Two separate hosted replicas must produce byte-identical RXEP record and receipt files.

Bounded verdict:

`RXEP_PARTIAL_SET_EXACT_DECIMAL_TOTAL_EVIDENCE_VERIFIABLE`

**Attribution:** RegenExcalibur / 1JGM
