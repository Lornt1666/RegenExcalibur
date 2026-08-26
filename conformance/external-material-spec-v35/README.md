# ProofGrid v3.5 — External Authoritative Material Specification Admission

This gate exists because the accepted real DigitalHub IFC/environmental-source suitability review ended in:

`SUITABILITY_UNRESOLVED_MISSING_SOURCE_SEMANTICS`

Public project sources were then exhausted without finding a candidate-bound concrete strength class.

v3.5 therefore admits **new authoritative source evidence** returned by a documented DigitalHub project authority.

## Exact candidate

- accepted IFC source SHA-256: `19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb`
- STEP ID: `9730`
- GlobalId: `3BmeJtEDj3AQO77Os2w7Ny`
- object/Revit ID: `2395272`
- material name: `Ortbeton - bewehrt`

## Allowed source outcomes

Exactly one of:

- `AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND`
- `AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND`
- `AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED`

A candidate-bound strength class must be explicit in the returned source and bound by exact identifier, documented material group, or explicit author confirmation. Name-only/fuzzy equivalence is not authority.

## Required provenance

The original email/reply or returned artifact bytes remain authority. The v3.5 source record binds:

- acquisition channel and source locator;
- exact content SHA-256 and byte length;
- message/thread identity when email-based;
- author name/organization/relation to DigitalHub;
- exact candidate binding method;
- exact strength-class fact or explicit absence statement.

## Authority boundary

Successful v3.5 admission does **not** itself authorize:

- IFC→environmental mapping;
- impact calculation;
- C25/30 ↔ C30/37 equivalence;
- scientific suitability;
- professional review;
- regulator acceptance;
- certification.

A separate reviewed suitability gate must consume any admitted v3.5 source before mapping/calculation can resume.

## Pre-response CI

Before any real reply exists, CI may prove only:

`V35_EXTERNAL_SOURCE_ADMISSION_ENGINE_PREFLIGHT_VERIFIABLE`

It cannot emit a real source-acquisition outcome. Real v3.5 closure requires retained external source bytes from a documented DigitalHub authority.
