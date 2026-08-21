# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.2

## Mission

Make built-environment claims independently inspectable without pretending that software integrity equals professional certification.

## v0.2 execution kernel

```text
project.json ─┐
              ├─ Draft 2020-12 schema validation ─┐
materials.json┘                                    │
                                                   ├─ deterministic calculation
IFC (.ifc) ─ IfcOpenShell read-only adapter ──────┤  (separate ingestion path)
                                                   ↓
                                             RX evidence envelope
                                                   ↓
                                   provenance + integrity receipt
                                                   ↓
                                     human-readable / JSON outputs
```

The IFC path is intentionally not wired into the material-GWP calculation yet. Connecting BIM quantities/material identities to environmental factors requires its own unit, mapping, source-authority, and conformance evidence gates.

## Architectural layers

1. **Constitution** — safety, truth, authority, privacy, reversibility, accountability.
2. **Schema / Protocol** — RXEP and canonical building/material structures.
3. **Adapters** — IFC first; LCA/EPD remains a separate future gate.
4. **Deterministic engine** — auditable calculations independent of generative AI.
5. **Evidence graph** — provenance-bearing machine-readable artifacts.
6. **Orchestration** — existing cloud/agent systems may automate workflows without changing evidence semantics.
7. **Commercial applications** — hosted collaboration, jurisdiction packs, integrations, services.

## Cloud-neutral rule

The protocol and reference verifier must run locally without requiring a paid cloud service. External open-source dependencies may be pinned and audited; cloud providers remain optional adapters/deployment targets rather than protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with extraction, mapping, and explanation, but inferred outputs must not be silently presented as deterministic facts.

## v0.2 acceptance gates

- canonical JSON inputs validate against Draft 2020-12 schemas;
- generated RXEP evidence validates before receipt issuance;
- unknown/invalid material inputs fail closed;
- identical inputs/method versions generate identical evidence digests;
- a real IFC model can be parsed with IfcOpenShell through a bounded read-only adapter;
- IFC ingestion emits no LCA, code, engineering, or certification conclusion;
- hosted CI exercises both JSON evidence and IFC paths;
- `VERIFIABLE` remains distinct from `CERTIFIED`.

## Next evidence gates

1. Versioned LCA/EPD source records with declared system boundaries and units.
2. IFC quantity/property extraction conformance fixtures.
3. Explicit mapping between IFC material/quantity data and authorized environmental factors.
4. Independently reproduced non-production building example.
5. Pilot measurement of time saved, errors detected, and reproducibility.
