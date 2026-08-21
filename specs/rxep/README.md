# RX Evidence Protocol (RXEP) v0.3 + ProofGrid v0.5 mapping evidence

RXEP is a minimal evidence envelope for RegenExcalibur systems. ProofGrid v0.5 adds a separate explicit IFC-to-environmental mapping receipt without silently changing the meaning of RXEP review or certification states.

## Design objective

A third party should be able to answer:

- What is being claimed?
- About what subject?
- What measurement supports the claim?
- Which exact inputs and environmental source records were used?
- Which source bytes and registry version were used?
- Which method and software version produced the result?
- Which lifecycle/system boundary and indicator apply?
- Which jurisdiction or standard context applies?
- What is the review state?
- What are the limitations?
- Can the artifact's integrity be checked?

For IFC-derived environmental mappings, the reviewer should additionally be able to answer:

- Which exact IFC file/extraction was used?
- Which element/material/quantity identities were mapped?
- Who or what workflow supplied the explicit mapping decision?
- Which exact environmental source record was selected?
- Was any numerical unit conversion performed?
- Can the mapping artifact and output receipt be integrity-checked?

## Runtime structural and provenance conformance

The environmental reference verifier validates canonical inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` receipt. The reference implementation validates:

- `project.json` against `schemas/building.schema.json`;
- `materials.json` against `schemas/materials.schema.json`;
- `lca-sources.json` against `schemas/lca-source-records.schema.json`;
- generated evidence against `specs/rxep/evidence-envelope.schema.json`.

The environmental source layer additionally verifies local source-content SHA-256 values, requires exact `source_record_id` resolution, prohibits implicit environmental unit conversion, and rejects incompatible lifecycle/system boundaries or indicators inside one calculation.

ProofGrid v0.4 separately validates IFC extraction artifacts against `schemas/ifc-extraction.schema.json`.

ProofGrid v0.5 validates explicit mapping decisions against `schemas/ifc-lca-mapping.schema.json`, resolves those decisions against the exact IFC extraction and environmental source registry, and issues a separate mapping receipt when the declared gate succeeds.

Structural/provenance conformance does **not** establish source authority, scientific validity, code compliance, engineering adequacy, professional LCA review, program-operator verification, or certification.

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

The environmental reference receipt additionally records the environmental registry hash, exact source-record IDs, canonical source-record digests, lifecycle/system boundary, indicator, and exact-match unit policy.

## v0.5 mapping receipt

The v0.5 mapping receipt is a separate evidence artifact. It does not silently rewrite an RXEP envelope's review state.

A successful receipt may report:

```text
EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE
```

This means the machine checks proved that:

- a mapping artifact validated structurally;
- the mapping was in the workflow state required by the v0.5 gate;
- the source IFC hash/schema matched the extraction;
- the exact element/material/quantity identities matched;
- the mapped quantity was explicitly declared IFC data;
- the narrow v0.5 unit identity rule matched without numerical conversion;
- the selected environmental source record passed provenance validation;
- environmental material identity, indicator, and lifecycle boundary were compatible;
- the deterministic mapped calculation and receipt completed.

The receipt preserves mapping, extraction, environmental registry, source-record, and source-content provenance so later evidence can reference the exact decision path.

## `REVIEWED` mapping state is not RXEP independent verification

The mapping schema's `REVIEWED` state is a workflow gate for the mapping decision. It must not be interpreted as equivalent to RXEP `INDEPENDENTLY_VERIFIED`, professional licensure, independent scientific review, or certification.

Those stronger states require separate evidence about the reviewer, authority, method, and review process.

## Integrity is not truth

A cryptographic hash proves that bytes have not changed relative to the recorded digest. It does not prove that a source is scientifically valid, that an IFC model represents reality, that a mapping is professionally appropriate, or that a professional conclusion is correct.

Likewise:

- `SOURCE_REGISTRY_VERIFIABLE` is not environmental certification;
- `VERIFIABLE` is not certification;
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE` is not an LCA conclusion or professional approval;
- `CLEAN_ENVIRONMENT_REPRODUCED` is software/environment reproducibility evidence, not independent scientific certification.

## RXEP review-state invariant

Allowed RXEP evidence states:

- `CLAIMED`
- `CALCULATED`
- `REVIEWED`
- `INDEPENDENTLY_VERIFIED`

The environmental reference implementation emits `CALCULATED` evidence and an overall `VERIFIABLE` software result when all declared schema, provenance, source-resolution, boundary, unit, deterministic-calculation, and integrity checks succeed.

The v0.5 mapping verifier emits a separate mapping-verification state and leaves stronger RXEP review states to separate evidence-producing processes.

`VERIFIABLE` is **not** `CERTIFIED`.
