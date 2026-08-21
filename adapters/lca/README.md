# LCA / EPD Source Layer

Status: **provenance registry implemented; explicit IFC mapping implemented; v0.6 authorization-aware source import implemented; v0.7 authoritative ILCD+EPD v1.3 XSD/master-data conformance implemented on the development stack; real provider ingestion remains blocked pending provider-specific authorization and adapter evidence**.

ProofGrid separates five questions that must not be collapsed:

1. **Can the bytes be accessed?**
2. **Are storage/transformation/commercial/redistribution rights sufficient for the intended operation?**
3. **Do the bytes conform to the declared authoritative interchange format/master-data identities?**
4. **Can they be normalized into a provenance-controlled ProofGrid source record?**
5. **Is that source scientifically/professionally suitable for the real product/project?**

v0.6 addresses question 2 with a synthetic authorization fixture. v0.7 adds a bounded answer to question 3 using authoritative ILCD+EPD v1.3 InData upstreams. Question 5 remains outside these software gates.

## v0.6 authorization gate remains mandatory

Before normalization, `schemas/source-import-manifest.schema.json` records provider/source identity, acquisition method, intended use, authorization state, terms snapshot/hash, approval/expiry evidence, permission dimensions, source hash, parser/profile, and intended normalized record ID.

The importer rejects:

- `UNKNOWN` authorization;
- `PUBLIC_ACCESS_ONLY` as sufficient tool/import authority;
- invalid `TEST_ONLY` use;
- explicit authorization without required approval evidence;
- expired authorization;
- storage/transformation not explicitly allowed;
- commercial use without commercial permission;
- raw export without redistribution permission;
- terms/source hash mismatch;
- path escape;
- unsupported parser/profile;
- normalized source-record schema/provenance failure.

**Public visibility is not permission for API/tool/commercial/redistribution use.**

## v0.7 authoritative ILCD+EPD v1.3 conformance lane

The v0.7 validator consumes immutable local checkouts of:

- `InDataWG/ILCD-EPD-Data-Format` @ `7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`;
- `InDataWG/ILCD-EPD-Master-Data` @ `32117b6a70d6c486344247a429449755a2c7eab4`.

It verifies the exact upstream commits before validation, then verifies the selected authoritative format objects:

- `schemas/EPD_DataSet.xsd`, git blob `d2b213528adfc2baa82e37c20eef109a9084d04a`;
- official InData v1.3 example, git blob `f6bf1a4bddc7800c5c7e69e6268d0b778c6e4969`;
- selected EN 15804+A2 master-data UUID `c0016b33-8cf7-415c-ac6e-deba0d21440d`.

The XSD graph is composed from the pinned local checkout under sandbox controls. Instance location hints are not used to widen the schema graph.

A successful receipt reports:

```text
ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
profile_validation_performed = false
certified = false
```

That means the declared XSD/master-data checks passed. It does **not** mean programme-operator validation-profile compliance, provider authorization, scientific validity, product representativeness, professional LCA review, or certification.

## v1.3 profile boundary

ProofGrid intentionally does not treat v1.3 XSD conformance as validation-profile compliance. The current v0.7 receipt explicitly records `profile_validation_performed = false`.

A published ILCD+EPD v1.2/ÖKOBAUDAT validation profile is a separate compatibility lane. A v1.2 profile result must not be used to label a v1.3 dataset profile-compliant.

## XML/security boundary

The dedicated v0.7 dependency lock is isolated from the frozen reproduction lock:

```text
xmlschema==4.3.1
elementpath==5.1.2
```

The validator uses sandbox-local-only schema resources, defused XML parsing, and ignores instance location hints during validation. Unit tests prove that an attempted unpinned remote schema import is blocked.

The earlier candidate `xmlschema 4.3.2 + elementpath 5.1.2` was rejected by hosted dependency resolution because that pair was incompatible; the corrected 4.3.1 pair was adopted without weakening the gate.

## Official example + synthetic derivative

The official InData v1.3 example is a required positive control. ProofGrid then derives a synthetic local fixture by changing only dataset UUID/name fields and validates the derivative against the same authoritative XSD graph.

The first green implementation receipt established:

- 51 tests passed with the v0.7 lock installed;
- XSD SHA-256 `2cf30de74b6a9607503aa99d791b196a88c709b9975546d837789bf1bdb93d0a`;
- official example SHA-256 `78476ee519b243088a226b013beb2d7b810d824a177070fcedb43011daa21a50`;
- selected EN 15804+A2 master-data SHA-256 `56527da732b221c30cba7b1314c4ce6bae90b8804ba157927299c0193af2990f`;
- synthetic derivative SHA-256 `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- receipt SHA-256 `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`.

Adversarial hosted checks also reject malformed XML, a missing required process section, an invalid process namespace, a tampered authoritative XSD, and wrong upstream commit identities.

## Normalized environmental source records

A ProofGrid source record retains stable record/material identity, declared unit/reference quantity, indicator/value/unit, lifecycle boundary, publisher/document/version, geography/publication metadata, verification state, redistribution state, source reference/content hash, limitations, synthetic state, and data-quality flags.

A source does not enter a deterministic calculation merely because it is XSD-valid. It must still enter through the source-registry/provenance gate and later explicit mapping/calculation gates as applicable.

## IFC mapping rule remains unchanged

For IFC-derived environmental calculations, an environmental record is never selected from an IFC material name. The exact environmental `material_identity_id` and `source_record_id` must be supplied by an explicit mapping artifact and validated against the source registry.

Successful source import or format conformance is not mapping approval and does not establish scientific suitability.

## Raw-source redistribution boundary

Normalization and redistribution remain separate permission dimensions. A successful v0.6 import may produce normalized metadata/provenance while raw source bytes remain restricted and unexported.

v0.7 XSD validation does not expand those rights.

## Non-equivalence rules

- access != authorization;
- authorization != format conformance;
- format conformance != scientific validity;
- source validity != project suitability;
- mapping workflow review != professional approval;
- hash integrity != truth;
- deterministic calculation != certification.

## Production-provider boundary

A real provider adapter remains blocked until all applicable evidence is available for:

- provider-specific access/acquisition method;
- storage/transformation/commercial/redistribution permission;
- terms/approval/expiry evidence;
- authoritative source format/version handling;
- provider-specific normalization semantics;
- source scientific/product identity review where required;
- downstream mapping/project methodology.

No current v0.6/v0.7 software receipt grants those missing authorities.
