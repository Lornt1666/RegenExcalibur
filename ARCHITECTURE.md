# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.7

## Mission

Make built-environment claims independently inspectable without pretending that software integrity, source access, format conformance, workflow review, or deterministic calculation equals scientific validity, legal authority, professional approval, regulatory approval, or certification.

## v0.7 execution model

ProofGrid separates five evidence questions that must remain independent:

```text
1. SOURCE AUTHORITY
   Can these exact bytes be acquired/stored/transformed/used/redistributed
   for the declared purpose?
                ↓
   v0.6 authorization-aware import gate

2. FORMAT CONFORMANCE
   Do the exact XML bytes conform to the pinned authoritative interchange
   schema/master-data identities?
                ↓
   v0.7 ILCD+EPD v1.3 XSD/master-data gate

3. NORMALIZED SOURCE PROVENANCE
   Does the ProofGrid environmental source record preserve exact source,
   unit, boundary, indicator, verification, and content-hash provenance?
                ↓
   v0.3 source-registry gate

4. BUILDING EVIDENCE + EXPLICIT MAPPING
   Which exact IFC-declared material/quantity identities are mapped to which
   exact environmental source record, through an explicit reviewed decision?
                ↓
   v0.4 extraction + v0.5 mapping gates

5. DETERMINISTIC RESULT / RECEIPT
   Can the declared calculation be reproduced and integrity-checked without
   promoting it to certification or professional judgment?
                ↓
   RXEP / ProofGrid receipts + clean-environment reproduction
```

A later gate may depend on an earlier one, but **success in one dimension never supplies missing evidence in another**. XSD validity does not grant source rights. Authorization does not prove scientific suitability. A reviewed mapping does not establish professional licensure. A deterministic number does not establish certification.

## v0.7 authoritative format-conformance layer

### Immutable upstream pins

The v0.7 gate uses local checkouts of exact upstream commits:

- `InDataWG/ILCD-EPD-Data-Format` @ `7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`;
- `InDataWG/ILCD-EPD-Master-Data` @ `32117b6a70d6c486344247a429449755a2c7eab4`.

The gate does not trust a moving branch name as sufficient evidence. Before XSD validation it checks `git rev-parse HEAD` against the expected commit.

The selected authoritative format objects include:

- `schemas/EPD_DataSet.xsd` — expected git blob `d2b213528adfc2baa82e37c20eef109a9084d04a`;
- InData official v1.3 example `sample_data/processes/EPDv1.3_example_57a4ae65-d305-421e-b21f-a3f0c35b8abe.xml` — expected git blob `f6bf1a4bddc7800c5c7e69e6268d0b778c6e4969`;
- selected EN 15804+A2 master-data UUID `c0016b33-8cf7-415c-ac6e-deba0d21440d`.

The upstream repositories are consumed in place. ProofGrid does not vendor the authoritative schema graph into the repository or rewrite inherited file notices.

### Version/profile boundary

The v0.7 result is deliberately:

```text
ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
profile_validation_performed = false
certified = false
```

This gate proves the declared XML Schema and selected master-data identity checks against pinned InData v1.3 upstreams. It does **not** claim validation-profile compliance.

The published ILCD+EPD v1.2/ÖKOBAUDAT validation-profile lane is a separate future compatibility gate. It must not be used to retroactively label a v1.3 dataset profile-compliant.

## XML security boundary

Authoritative schema composition uses:

- `xmlschema==4.3.1`;
- `elementpath==5.1.2`;
- `allow = sandbox`;
- `defuse = always`;
- a base URL rooted in the pinned local schema checkout;
- instance location hints disabled for validation.

Unpinned remote schema imports are therefore not permitted to silently expand the validation graph.

Adversarial local XML fixtures are each wrapped in a sandboxed `XMLResource` rooted in their local test directory. This permits malformed/schema-invalid local instances to be tested without granting them authority to fetch remote resources or weakening the authoritative schema sandbox.

## Dependency isolation rule

`requirements-proofgrid.txt` remains frozen for the earlier reproduction evidence.

v0.7 uses a separate exact lock in `requirements-proofgrid-v07.txt`.

The first candidate pair—`xmlschema 4.3.2` plus `elementpath 5.1.2`—was impossible to resolve because xmlschema 4.3.2 required elementpath 5.1.3 or later while the runner package index did not provide a compatible release. The corrected exact pair is:

```text
xmlschema==4.3.1
elementpath==5.1.2
```

The failure is retained as evidence of dependency-resolution behavior; the acceptance rule was not weakened to make the build green.

## Positive v0.7 control path

The validator performs the following sequence:

1. load `conformance/ilcd-epd-v13/upstream.json`;
2. reject any attempt to set `profile_validation_performed = true` in the current v1.3 gate;
3. verify exact format and master-data checkout commits;
4. verify expected upstream license evidence;
5. verify the selected authoritative XSD and official-example git blobs;
6. resolve the selected EN 15804+A2 master-data UUID from the pinned master-data checkout;
7. compose the XSD graph locally under sandbox controls;
8. validate the official InData v1.3 example as the upstream positive control;
9. derive a deterministic synthetic fixture by changing only dataset UUID/name fields in the pinned example;
10. validate the synthetic derivative against the same XSD graph;
11. emit a machine-readable receipt with exact hashes, versions, security state, limitations, and `certified = false`.

## Fail-closed v0.7 checks

The hosted and unit-test layers reject or test:

- format commit mismatch;
- master-data commit mismatch;
- authoritative XSD git-object mismatch/tampering;
- official-example git-object mismatch;
- selected master-data UUID mismatch;
- malformed XML;
- missing required process information;
- invalid process namespace;
- unpinned remote schema import;
- false v1.3 validation-profile assertion.

The official InData example itself is a required positive control. If it fails under the pinned schema graph, the gate stops instead of changing the fixture or schema silently.

## v0.7 receipt semantics

A successful conformance receipt retains:

- validator name/version;
- Python/xmlschema/elementpath versions;
- exact upstream repository commits;
- exact authoritative XSD git blob and SHA-256;
- official-example git blob, SHA-256, dataset identity, and XSD result;
- selected authoritative master-data UUID/path/SHA-256;
- synthetic derivative identity/SHA-256/XSD result;
- security controls;
- `profile_validation_performed = false`;
- limitations;
- canonical receipt SHA-256;
- `certified = false`.

The first green implementation receipt established:

- 51 tests passed;
- XSD SHA-256 `2cf30de74b6a9607503aa99d791b196a88c709b9975546d837789bf1bdb93d0a`;
- official example SHA-256 `78476ee519b243088a226b013beb2d7b810d824a177070fcedb43011daa21a50`;
- selected EN 15804+A2 master-data SHA-256 `56527da732b221c30cba7b1314c4ce6bae90b8804ba157927299c0193af2990f`;
- synthetic derivative SHA-256 `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- receipt SHA-256 `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`.

These values describe the proven implementation lane. A documentation-complete exact-head run is still required before issue #14 is completed.

## Inherited v0.6 authorization gate

v0.7 does not replace v0.6. Real source acquisition remains independently rights-gated.

The importer fails closed for, among other cases:

- `UNKNOWN` or `PUBLIC_ACCESS_ONLY` authority;
- invalid test-only use;
- missing/expired explicit approval;
- storage/transformation permission not explicitly allowed;
- commercial-tool use without commercial permission;
- raw export without redistribution permission;
- terms/source hash mismatch;
- path escape;
- unsupported parser profile.

A real EPD can be perfectly XSD-valid and still be prohibited from the intended ProofGrid operation. Conversely, authorization to access bytes does not establish XSD validity or scientific suitability.

## Inherited environmental source-registry gate

Environmental factors enter deterministic calculations only through exact environmental source-record IDs with preserved units, reference quantities, indicators, lifecycle boundaries, verification state, source metadata, and content hashes.

No fuzzy source selection or implicit environmental unit conversion is authorized.

## Inherited IFC/mapping gates

The v0.4/v0.5 rules remain unchanged:

- only supported explicitly declared `IfcElementQuantity` values are treated as declared quantities;
- no geometry-derived quantity is silently substituted;
- IFC source hash/schema and element/material/quantity identities remain exact evidence inputs;
- material strings do not choose environmental records;
- mapping targets are explicit;
- mapping state `REVIEWED` is a workflow gate, not professional/scientific authority;
- duplicate/conflicting mappings fail;
- the narrow mass unit identity remains `MASSUNIT + KILO + GRAM → kg` with no numerical conversion.

## Architectural layers

1. **Constitution** — truth, safety, authority, privacy, reversibility, accountability.
2. **Rights/acquisition evidence** — provider, intended use, terms, approvals, permission dimensions.
3. **Format-conformance evidence** — immutable upstream format/master-data identity, parser/security state, schema result.
4. **Source provenance** — normalized environmental source records and exact source-content hashes.
5. **IFC evidence extraction** — source IFC identity, hierarchy, units, declared quantities/materials.
6. **Explicit mapping evidence** — reviewed exact IFC→environmental source decisions.
7. **Deterministic engines** — calculations and validators independent of generative AI.
8. **Evidence receipts** — integrity-checkable artifacts with bounded semantics.
9. **Reproduction** — clean-environment known-answer runs.
10. **Orchestration** — automation may coordinate gates but cannot manufacture missing authority/evidence.
11. **Commercial applications** — permitted only when all relevant evidence and source-use rights support the intended use.

## Non-equivalence invariants

```text
ACCESS != AUTHORIZATION
AUTHORIZATION != FORMAT CONFORMANCE
FORMAT CONFORMANCE != SCIENTIFIC VALIDITY
SCIENTIFIC RELEVANCE != LEGAL USE RIGHTS
WORKFLOW REVIEW != PROFESSIONAL APPROVAL
HASH INTEGRITY != TRUTH
DETERMINISTIC RESULT != CERTIFICATION
```

## Next evidence gates

1. A separate published-profile compatibility lane for ILCD+EPD v1.2 / ÖKOBAUDAT profile 3.8.0, without mislabeling v1.3.
2. Provider-specific authorization records and adapters only after access/storage/transformation/commercial/redistribution terms are explicitly evidenced.
3. Externally reviewed mapping artifacts using properly authorized non-production source data.
4. A separately versioned deterministic unit-conversion subsystem if broader cross-unit mappings are required.
5. Independently reviewed real-project methodology before any real-building environmental claim.
6. Pilot measurement of time saved, errors detected, and reproducibility.
