# ProofGrid v1.3 — Declared Reference-Basis Research

This directory freezes the exact ILCD quantitative-reference chain used by the pinned public InData wood-panel fixtures before ProofGrid accepts a general reference-basis extractor.

Research path:

```text
process quantitativeReference
  → referenceToReferenceFlow (internal ID)
  → process exchange
  → referenceToFlowDataSet (UUID/version)
  → exchange meanAmount
  → product flow dataset
  → referenceToReferenceFlowProperty (internal ID)
  → flowProperty
  → referenceToFlowPropertyDataSet (UUID/version)
  → flow-property meanValue
  → flow-property master data
  → referenceToReferenceUnitGroup (UUID)
  → unit-group master data
  → referenceToReferenceUnit (internal ID)
  → unit name + meanValue factor
```

For the initial pinned v1.2/v1.3 fixtures, the current hypothesis is that this complete chain resolves to `1 kg` of the referenced wood-panel product flow. The hosted research workflow must prove every identity and lexical Decimal component before that bounded statement is accepted.

This is **not** a universal rule that EPDs are per kg. No environmental indicator values are transformed in this research gate. No implicit unit conversion, scientific validation, professional review, provider-rights expansion, programme-operator/BBSR approval, or certification is performed.

Reference dependencies for future real/provider declarations must come from the same authorized source closure or a separately authorized provenance-controlled reference store. UUID/name search on an ungoverned network is not an admissible substitution mechanism.

**Attribution:** RegenExcalibur / 1JGM
