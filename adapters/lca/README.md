# LCA / EPD Source Layer

Status: **provenance registry implemented; v0.5 explicit mapping consumption implemented; production external-dataset ingestion not yet implemented**.

ProofGrid's environmental source layer uses a versioned environmental-factor registry. Environmental quantities do not carry free-floating GWP factors; calculations resolve exact `source_record_id` values in `lca-sources.json`.

Each source record retains:

- stable record ID and environmental material identity;
- declared unit and reference quantity;
- indicator name, value, and unit;
- lifecycle modules / system boundary;
- publisher, source document ID, and version;
- geography/publication metadata when declared;
- verification state and evidence reference when applicable;
- redistribution status;
- local source reference and SHA-256 content hash;
- limitations, synthetic state, and data-quality flags.

## Source-registry fail-closed rules

- no fuzzy material-to-factor matching;
- no implicit environmental unit conversion;
- environmental material identity and exact source-record ID must agree;
- all factors in one calculation must use compatible indicator and lifecycle/system boundaries;
- duplicate source IDs fail;
- duplicate/conflicting records for the same source/document/material/boundary identity fail;
- source-content hash mismatches fail;
- a source cannot claim a verified state without the evidence required by the current schema;
- synthetic fixtures remain explicitly non-production.

## v0.5 mapping consumption rule

For an IFC-derived calculation, the source layer does **not** select a record from an IFC material name.

The exact environmental `material_identity_id` and `source_record_id` must be supplied by an explicit mapping artifact. The v0.5 verifier then checks that:

1. the mapping is in the accepted mapping workflow state;
2. the mapped IFC source/element/material/quantity identities match the extraction exactly;
3. the selected source record exists;
4. the target environmental material identity matches the selected source record;
5. the source record passes the existing registry/source-content provenance gate;
6. the IFC unit identity matches the source record's declared unit under the narrow versioned v0.5 unit policy;
7. indicator and lifecycle boundaries remain compatible.

The mapping artifact therefore supplies a **selection decision to validate**. It is not evidence, by itself, that the selected EPD/factor is scientifically or professionally appropriate for a real project.

## v0.5 unit boundary

The initial mapping gate recognizes only IFC `MASSUNIT` with `KILO` + `GRAM` as the unit identity `kg`, without changing the numerical quantity.

This is not a general conversion library. Any broader unit conversion or normalization requires a separately versioned deterministic subsystem, conversion provenance, known-answer tests, and its own acceptance gate.

## Mapping review-state boundary

A v0.5 mapping must be in `REVIEWED` state before calculation. That state records workflow authorization under the mapping schema. It does **not** assert licensed-professional review, independent scientific verification, program-operator verification, regulatory approval, or certification unless those authorities are separately evidenced.

## Provenance retained downstream

A successful mapping receipt records the exact source-record digest and registry/source-content provenance alongside the exact mapping artifact and IFC extraction hashes. This permits a later reviewer to determine which environmental record was selected and which IFC evidence it was bound to.

## Boundary

A valid registry and mapping receipt can prove structural/provenance integrity of the selected records and the deterministic software path. They do **not** establish that an environmental declaration is scientifically correct, professionally reviewed, legally usable, representative of the actual installed product, or appropriate for a real building.

Production EPD/database connectors, licensing decisions, broad unit-conversion libraries, jurisdiction-specific LCA methodology, real-product identity validation, and professional review remain later evidence gates.
