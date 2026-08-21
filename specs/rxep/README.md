# RX Evidence Protocol (RXEP) v0.3 + ProofGrid v0.7 supporting receipts

RXEP is a minimal evidence envelope for RegenExcalibur systems. Later ProofGrid gates add **separate supporting receipts** for IFC extraction/mapping, clean-environment reproduction, authorization-aware source import, and authoritative format conformance without silently changing the meaning of RXEP review or certification states.

## Design objective

A third party should be able to determine:

- what is being claimed and about what subject;
- what measurement supports the claim;
- which exact inputs/source records were used;
- which method/software versions produced the result;
- which lifecycle/system boundary and indicator apply;
- which source bytes and registry version were used;
- what review state and limitations apply;
- whether artifact integrity can be checked.

For externally obtained environmental data, supporting evidence should additionally answer:

- what source/provider/acquisition method was involved;
- what authorization/use state was evaluated;
- which terms/approval/expiry evidence applied;
- which exact bytes were parsed;
- which interchange format/schema/master-data versions were tested;
- whether remote/unpinned validation resources were permitted;
- whether raw bytes were exported;
- which normalized source record resulted;
- whether any validation-profile check was actually performed.

## Core RXEP state remains separate

Allowed RXEP evidence states remain:

- `CLAIMED`
- `CALCULATED`
- `REVIEWED`
- `INDEPENDENTLY_VERIFIED`

Supporting ProofGrid software receipts do **not** automatically elevate an RXEP envelope to a stronger review state.

Current supporting software labels include:

- `SOURCE_REGISTRY_VERIFIABLE`
- `VERIFIABLE`
- `DECLARED_IFC_DATA_EXTRACTED`
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE`
- `CLEAN_ENVIRONMENT_REPRODUCED`
- `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE`
- `ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT`

None of these is equivalent to `CERTIFIED` or automatically equivalent to RXEP `INDEPENDENTLY_VERIFIED`.

## v0.6 authorization-aware source-import receipt

`AUTHORIZED_SOURCE_IMPORT_VERIFIABLE` means the declared software checks proved the recorded import-manifest structure, authorization/use decision, terms/source hashes, path boundary, parser/profile identity, normalized source-record validation, and raw-export state.

It does **not** prove legal advice, broader provider permission, scientific validity, official EPD format conformance, professional LCA review, or certification.

A source may be legally accessible but scientifically inappropriate, scientifically relevant but not licensed for the intended workflow, or both. These dimensions remain separate evidence requirements.

## v0.7 ILCD+EPD v1.3 conformance receipt

A successful v0.7 supporting receipt reports:

```text
ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
profile_validation_performed = false
certified = false
```

This means the declared machine checks proved that:

- the InData ILCD+EPD format checkout matched exact commit `7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`;
- the InData master-data checkout matched exact commit `32117b6a70d6c486344247a429449755a2c7eab4`;
- the selected authoritative XSD git object matched the pinned identity;
- the official InData v1.3 example matched its pinned git object and validated against the authoritative XSD graph;
- the deterministic ProofGrid synthetic derivative validated against the same XSD graph;
- the selected EN 15804+A2 master-data UUID resolved from the pinned master-data checkout;
- XML schema composition was restricted to sandbox/local resources with defused parsing;
- instance location hints were not used to widen the validation graph;
- dependency versions, upstream hashes, fixture hashes, limitations, and receipt integrity were retained.

The first green implementation receipt records:

- validator version `0.7.0`;
- Python `3.11.16`;
- `xmlschema 4.3.1`;
- `elementpath 5.1.2`;
- authoritative XSD SHA-256 `2cf30de74b6a9607503aa99d791b196a88c709b9975546d837789bf1bdb93d0a`;
- official example SHA-256 `78476ee519b243088a226b013beb2d7b810d824a177070fcedb43011daa21a50`;
- selected EN 15804+A2 master-data SHA-256 `56527da732b221c30cba7b1314c4ce6bae90b8804ba157927299c0193af2990f`;
- synthetic derivative SHA-256 `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- receipt SHA-256 `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`;
- `profile_validation_performed = false`;
- `certified = false`.

## v1.3 profile validation is a different claim

An XSD/master-data receipt must not be interpreted as validation-profile compliance.

The v0.7 evidence explicitly records that no authoritative v1.3 validation profile is being applied in this gate. A separate published v1.2/ÖKOBAUDAT profile-compatibility result, when implemented, will remain a separate receipt and will not retroactively validate a v1.3 dataset against a v1.2 profile.

## Source authorization and format conformance are independent

A source can satisfy v0.7 format conformance while failing v0.6 source-use authority. Conversely, an authorized source can fail the declared format schema.

Therefore:

```text
AUTHORIZED_SOURCE_IMPORT_VERIFIABLE
```

and

```text
ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
```

are independent evidence statements. Neither implies the other.

## Mapping receipt remains separate

`EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE` proves the declared exact IFC identity/mapping/source-record/calculation path. It does not prove independent scientific/professional approval.

A format-conformant environmental source is not automatically an accepted mapping target. The explicit mapping and source-provenance gates still apply.

## Integrity is not truth or authority

A cryptographic hash proves which bytes were used relative to the recorded digest. It does not prove:

- that a terms interpretation is legally correct;
- that an EPD/source is scientifically valid or representative;
- that a product/material identity matches the real installation;
- that an IFC model represents reality;
- that an explicit mapping is professionally appropriate;
- that a validation profile was applied unless the receipt says so;
- that a professional conclusion is correct.

## Evidence composition rule

Higher-stakes claims should compose the relevant independent receipts instead of collapsing them into a single overloaded status.

For example, a future real-project environmental claim may require separate evidence for:

1. source acquisition/use authority;
2. authoritative interchange-format/profile conformance;
3. source-record provenance;
4. real-product/material identity;
5. IFC/source quantity provenance;
6. explicit mapping/reviewer authority;
7. deterministic calculation methodology;
8. jurisdiction/methodology applicability;
9. professional/independent review;
10. final claim/evidence integrity.

ProofGrid currently proves only selected software/provenance layers of that chain.

`VERIFIABLE` remains **not** `CERTIFIED`.
