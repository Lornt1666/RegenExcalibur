# RX Evidence Protocol (RXEP) v0.3 + ProofGrid v0.6 supporting receipts

RXEP is a minimal evidence envelope for RegenExcalibur systems. Later ProofGrid gates add **separate supporting receipts** for IFC mapping, clean-environment reproduction, and authorization-aware source import without silently changing the meaning of RXEP review or certification states.

## Design objective

A third party should be able to determine:

- what is being claimed and about what subject;
- what measurement supports the claim;
- which exact inputs and environmental source records were used;
- which method/software version produced the result;
- which lifecycle/system boundary and indicator apply;
- which source bytes and registry version were used;
- what review state and limitations apply;
- whether artifact integrity can be checked.

For imported environmental data, the evidence chain should additionally answer:

- where the bytes came from;
- what acquisition method and intended use were declared;
- what authorization state was evaluated;
- which storage/transformation/commercial/redistribution dimensions were declared;
- which exact terms snapshot was evaluated;
- whether provider approval/expiry evidence was required and present;
- which exact source bytes were parsed;
- which parser/profile normalized them;
- whether raw bytes were exported;
- which normalized source record and output registry resulted.

## Core RXEP runtime conformance

The environmental reference verifier validates canonical inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` software receipt.

The environmental source layer separately validates source-record schema, exact source-content hashes, source IDs, units, indicators, and lifecycle boundaries.

ProofGrid v0.4 adds IFC extraction evidence. ProofGrid v0.5 adds an explicit IFC-to-environmental mapping receipt. ProofGrid v0.6 adds an authorization-aware environmental source-import receipt.

These supporting receipts are evidence inputs; they do **not** silently elevate an RXEP envelope's review state.

## Minimal RXEP envelope

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

## v0.5 mapping receipt

A successful mapping receipt may report:

```text
EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE
```

This means the declared machine checks proved the mapping artifact, exact IFC identities, explicit mapping state, selected source-record provenance, unit identity, lifecycle/indicator compatibility, deterministic mapped calculation, and receipt integrity.

It does not mean the mapping is independently scientifically or professionally approved.

## v0.6 authorization-aware source-import receipt

A successful source-import receipt may report:

```text
AUTHORIZED_SOURCE_IMPORT_VERIFIABLE
```

This means the declared machine checks proved that:

- the import manifest validated against the v0.6 schema;
- the declared authorization/use policy satisfied the v0.6 fail-closed rules at the recorded evaluation date;
- the exact terms snapshot hash matched;
- the exact source-content hash matched;
- the source path remained inside the import package;
- the declared parser/format/profile matched the supported implementation;
- the source was parsed under that versioned profile;
- the normalized environmental record passed the existing ProofGrid source-record schema/provenance validator;
- the normalized record/output hashes and raw-source export state were retained.

The receipt does **not** prove that:

- the manifest's legal interpretation is correct legal advice;
- public access itself granted the declared rights;
- a third-party provider authorizes any use outside the recorded manifest;
- the source is scientifically valid or representative;
- the source carrier conforms to an official EPD interchange/profile unless separately validated;
- a professional LCA, regulatory, engineering, architectural, procurement, or certification conclusion has been reached.

## Authorization state is not source validity

ProofGrid v0.6 deliberately separates permission-state evidence from data-validity evidence.

For example:

```text
TEST_ONLY + INTERNAL_TEST + storage/transformation allowed
```

can authorize a synthetic parser conformance fixture while still producing:

```text
verification.state = UNVERIFIED
certified = false
```

Likewise, a future provider source may be legally accessible yet scientifically inappropriate for a particular project, or scientifically relevant yet not licensed for the intended software workflow. Both dimensions must be evidenced separately.

## Public access is not an RXEP authority state

`PUBLIC_ACCESS_ONLY` is intentionally insufficient for v0.6 import. The fact that bytes or metadata can be viewed on the public web must not be transformed into an unstated claim of API, storage, transformation, commercial, or redistribution authority.

Provider-specific authorization requires separate evidence appropriate to the provider and use case.

## Raw-source redistribution is separate from normalization

An import receipt may be successful while recording a restricted source and no raw export.

The initial v0.6 conformance receipt records:

- `redistribution = PROHIBITED`;
- normalized source `redistribution_status = RESTRICTED`;
- `raw_export.requested = false`;
- `raw_export.exported = false`.

Thus normalized evidence does not imply permission to redistribute the source carrier.

## Integrity is not truth or authority

A cryptographic hash proves which bytes were used relative to the recorded digest. It does not prove:

- that a source is scientifically valid;
- that an IFC model represents reality;
- that a mapping is professionally appropriate;
- that a terms interpretation is legally correct;
- that a provider granted broader rights than the recorded evidence;
- that a professional conclusion is correct.

## Evidence-state vocabulary remains bounded

Allowed RXEP evidence states remain:

- `CLAIMED`
- `CALCULATED`
- `REVIEWED`
- `INDEPENDENTLY_VERIFIED`

Supporting ProofGrid software receipts currently include:

- `SOURCE_REGISTRY_VERIFIABLE`
- `VERIFIABLE`
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE`
- `CLEAN_ENVIRONMENT_REPRODUCED`
- `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE`

None of those software labels is automatically equivalent to RXEP `INDEPENDENTLY_VERIFIED` or `CERTIFIED`.

## Initial v0.6 receipt evidence

Genesis #29 established the first synthetic source-import receipt with:

- importer version `0.6.0`;
- manifest content SHA-256 `78fea8f1c85bb15fd4471a5fa29644f65ea69d88104e4c69b222e85f28712c21`;
- terms SHA-256 `18437a5c104ffe5b26a83004300d0b47c240bcc96e09b1119b9992da819fc601`;
- source SHA-256 `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`;
- normalized record `RX-IMPORTED-SYNTH-CONCRETE-A1A3`;
- normalized record digest `c155b0c66c8372688b97abb3288c9a9ed8d4906c8793f13f2aa9dce36b1a03fc`;
- normalized registry file SHA-256 `b8c1fdc87d4e788eff5b7fc3c6c66f31e0f6264f9c3c767c8bf8fd269d018b0b`;
- import receipt SHA-256 `fe5d8e838f0b9f8ec84eb56c49c6fde219a94b4c7556016c30f95be475cc858b`;
- `certified = false`.

`VERIFIABLE` and all later supporting receipt labels remain explicitly distinct from certification.
