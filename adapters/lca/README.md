# LCA / EPD Source Layer

Status: **v0.3 provenance registry implemented; production external-dataset ingestion not yet implemented**.

ProofGrid v0.3 introduces a versioned environmental-factor source registry. Material quantities no longer carry free-floating GWP factors; they reference an exact `source_record_id` in `lca-sources.json`.

Each source record retains:

- stable record ID and material identity;
- declared unit and reference quantity;
- indicator name, value, and unit;
- lifecycle modules / system boundary;
- publisher, source document ID, and version;
- geography/publication metadata when declared;
- verification state and evidence reference when applicable;
- redistribution status;
- local source reference and SHA-256 content hash;
- limitations, synthetic state, and data-quality flags.

## Fail-closed rules

- no fuzzy material-to-factor matching;
- no implicit unit conversion;
- material identity and exact source-record ID must agree;
- all factors in one v0.3 calculation must use the same indicator and lifecycle/system boundary;
- duplicate source IDs fail;
- duplicate/conflicting records for the same source/document/material/boundary identity fail;
- source-content hash mismatches fail;
- a source cannot claim a verified state without an evidence reference under the current schema;
- synthetic fixtures remain explicitly non-production.

## Boundary

A valid registry proves structural and provenance integrity of the imported records and referenced source bytes. It does **not** establish that an environmental declaration is scientifically correct, professionally reviewed, program-operator verified, legally usable, or appropriate for a real project.

Production EPD/database connectors, licensing decisions, unit-conversion libraries, and jurisdiction-specific LCA methodology remain later evidence gates.
