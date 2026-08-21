# ProofGrid v1.0 — Admission-Bound Canonical Environmental Source Identity

ProofGrid v1.0 sits **after** the v0.9 environmental-declaration admission state machine.

It answers one bounded question:

> Once the exact ILCD+EPD source has been admitted for normalization, can ProofGrid deterministically normalize the document's identity/provenance metadata while preserving the independent authority, conformance, scientific-review, and certification dimensions?

## Required parent state

The normalizer requires a complete, canonical receipt chain:

1. v0.9 preflight receipt;
2. applicable v1.2 or v1.3 conformance receipt;
3. v0.9 final admission receipt with `ADMITTED_FOR_NORMALIZATION` and `normalization_permitted=true`;
4. the exact admitted source bytes.

The v0.9 final admission receipt must reproduce exactly from the supplied preflight and conformance receipts. The source bytes and, for ZIP packages, the deterministic ILCD package-manifest digest are reverified before normalization.

## Supported routes

### ILCD+EPD v1.2

Required route:

`OEKOBAUDAT_V12_PROFILE_3_8_0`

The admitted v1.2 source is a ZIP package. v1.0 preserves the v0.8/v0.9 profile-compatibility evidence binding but does not reinterpret it as certification or scientific validity.

### ILCD+EPD v1.3

Required route:

`INDATA_V13_XSD_MASTERDATA_ONLY`

The admitted v1.3 control is an XML process dataset. v1.0 requires `profile_validation_performed=false` and does not silently substitute the v1.2 ÖKOBAUDAT profile.

## Canonicalized fields

v1.0 extracts only deterministic identity/provenance metadata:

- ILCD+EPD version;
- source SHA-256;
- ZIP package-manifest SHA-256 where applicable;
- container/media type;
- process dataset UUID;
- process XML SHA-256;
- available process base names/languages;
- available dataset version;
- available registration number;
- authority decision/status/transformation/redistribution state bound from admission;
- selected route;
- conformance receipt binding;
- preflight/admission receipt bindings.

## Deliberate non-normalization

The v1.0 record hard-codes:

```text
impact_values_normalized = false
scientific_validation_performed = false
professional_review_performed = false
certified = false
```

No warning text, unsupported field, missing module, or profile success is converted into an environmental impact value.

The existing ProofGrid LCA source registry remains a separate later-stage structure for environmental factors with explicit material identity, units, lifecycle boundary, and indicator provenance. v1.0 does not populate that registry from ILCD+EPD automatically.

## RXEP relationship

The v1.0 canonicalization receipt is **supporting evidence only**.

It cannot automatically elevate an RX Evidence Protocol envelope to `REVIEWED` or `INDEPENDENTLY_VERIFIED`.

Document identity integrity is not scientific truth, professional judgment, provider authority, programme-operator/BBSR approval, code compliance, engineering/architectural approval, procurement approval, regulatory approval, or certification.

## Verdict

A successful gate emits:

`ADMITTED_ENVIRONMENTAL_SOURCE_IDENTITY_VERIFIABLE`

This means the admitted document identity/provenance metadata was deterministically normalized and bound to exact source/admission/conformance receipts under the v1.0 software gate.

It means nothing more.

**Attribution:** RegenExcalibur / 1JGM
