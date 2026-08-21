# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.3

## Mission

Make built-environment claims independently inspectable without pretending that software integrity equals scientific validity, professional review, or certification.

## v0.3 execution kernel

```text
project.json ───────────────┐
materials.json ─────────────┼─ Draft 2020-12 schema validation ─┐
lca-sources.json ───────────┘                                   │
source content files ─ SHA-256 provenance validation ───────────┤
                                                                │
exact material identity + source_record_id resolution ──────────┤
exact unit match + compatible lifecycle boundary/indicator ─────┤
                                                                ↓
                                                deterministic GWP calculation
                                                                ↓
                                                     RX evidence envelope
                                                                ↓
                                         registry/source/evidence integrity receipt
                                                                ↓
                                             human-readable / JSON outputs

IFC (.ifc) ─ IfcOpenShell read-only adapter ─ separate structural-ingestion path
```

The IFC path remains intentionally separate from the environmental calculation. Connecting IFC quantities/material identities to environmental source records requires its own conformance gate.

## Architectural layers

1. **Constitution** — safety, truth, authority, privacy, reversibility, accountability.
2. **Schema / Protocol** — RXEP and canonical building/material/environmental-source structures.
3. **Source provenance** — exact source records, source-content hashes, units, boundaries, versions, verification state, licensing metadata.
4. **Adapters** — read-only IFC ingestion plus future authorized EPD/LCA database connectors.
5. **Deterministic engine** — auditable calculations independent of generative AI.
6. **Evidence graph** — provenance-bearing machine-readable artifacts.
7. **Orchestration** — existing cloud/agent systems may automate workflows without changing evidence semantics.
8. **Commercial applications** — hosted collaboration, jurisdiction packs, integrations, services.

## Cloud-neutral rule

The protocol and reference verifier must run locally without requiring a paid cloud service. External open-source dependencies may be pinned and audited; cloud providers remain optional adapters/deployment targets rather than protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with extraction, mapping, and explanation, but inferred outputs must not be silently presented as deterministic facts.

## Source-selection rule

Environmental factors may enter the deterministic calculation only through an exact source-record ID and exact material-identity match. ProofGrid v0.3 does not perform fuzzy factor selection.

## Unit rule

v0.3 performs no implicit unit conversion. A material quantity unit must exactly match the selected source record's declared unit. Explicit conversion infrastructure, if added later, requires a separately versioned and tested method.

## Lifecycle-boundary rule

A single v0.3 calculation may not silently mix incompatible lifecycle/system boundaries or indicators. All selected records must share the same canonical module set and indicator name.

## v0.3 acceptance gates

- canonical project, material, environmental-source, and generated RXEP evidence documents validate against Draft 2020-12 schemas;
- material rows cannot contain free-floating GWP factors under the v0.3 schema;
- environmental source content is SHA-256 checked before calculation;
- duplicate record IDs fail;
- duplicate/conflicting records for the same source/document/material/boundary identity fail;
- exact material identity and source-record references are required;
- implicit unit conversion fails closed;
- incompatible lifecycle boundaries or indicators fail closed;
- registry/source-record provenance is recorded in downstream receipts;
- identical inputs/method versions generate identical numerical results and evidence digests;
- the existing real IFC parser path remains green;
- hosted CI exercises the registry, calculation, and IFC paths;
- `VERIFIABLE` remains distinct from `CERTIFIED`.

## Next evidence gates

1. IFC quantity/property/material extraction conformance fixtures.
2. Evidence-controlled mapping between extracted IFC quantities/material identities and exact environmental source records.
3. Authorized production EPD/database connectors with explicit licensing and import provenance.
4. Independently reproduced non-production building example.
5. Pilot measurement of time saved, errors detected, and reproducibility.
