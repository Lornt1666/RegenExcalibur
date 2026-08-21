# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.5

## Mission

Make built-environment claims independently inspectable without pretending that software integrity equals scientific validity, professional review, regulatory approval, or certification.

## v0.5 execution kernel

```text
ENVIRONMENTAL SOURCE PATH

lca-sources.json + referenced source bytes
    ↓
Draft 2020-12 validation
    ↓
source identity/conflict checks
    ↓
source-content SHA-256 verification
    ↓
provenance-controlled source-record index

IFC DECLARED-DATA PATH

IFC (.ifc)
    ↓
pinned IfcOpenShell parser
    ↓
source IFC SHA-256 + IFC schema + project unit context
    ↓
project/site/building/storey/space hierarchy
    ↓
IfcMaterial associations + supported IfcElementQuantity values
    ↓
conflict / ambiguity / missing-data warnings
    ↓
Draft 2020-12 IFC extraction artifact

EXPLICIT v0.5 MAPPING PATH

reviewer-authored mapping artifact
    │
    ├─ source IFC SHA-256 + schema
    ├─ element GlobalId + STEP ID + IFC type
    ├─ material association/material STEP IDs + exact declared name
    ├─ quantity-set/quantity STEP IDs + type + name + exact value
    ├─ exact extracted unit declaration
    ├─ explicit target material_identity_id
    ├─ explicit target source_record_id
    └─ mapping state + author + rationale
    ↓
Draft 2020-12 mapping validation
    ↓
exact resolution against IFC extraction
    ↓
REVIEWED mapping-state gate
    ↓
exact environmental source-record validation
    ↓
v0.5 unit-identity gate
    ↓
compatible indicator + lifecycle boundary
    ↓
deterministic mapped subtotal / total
    ↓
provenance-bearing mapping receipt

NO FUZZY IFC MATERIAL → ENVIRONMENTAL SOURCE SELECTION
NO GENERAL UNIT CONVERSION
NO GEOMETRY-DERIVED QUANTITY TAKEOFF
```

The key architectural change in v0.5 is that the IFC and environmental paths may now meet, but the bridge is an **explicit evidence artifact**, not an inference engine. A string such as `Concrete` never chooses an environmental factor by itself.

## Architectural layers

1. **Constitution** — safety, truth, authority, privacy, reversibility, accountability.
2. **Schema / Protocol** — RXEP and canonical building/material/environmental-source/IFC-extraction/mapping structures.
3. **Source provenance** — exact environmental source records, source-content hashes, units, boundaries, versions, verification state, and licensing metadata.
4. **IFC evidence extraction** — source hash, spatial hierarchy, units, declared quantities, material associations, and warnings.
5. **Explicit mapping evidence** — reviewed mapping records that bind exact IFC identities to exact environmental source-record identities.
6. **Adapters** — pinned IfcOpenShell plus future authorized EPD/LCA database connectors.
7. **Deterministic engines** — auditable calculations and mapping validation independent of generative AI.
8. **Evidence graph / receipts** — provenance-bearing machine-readable artifacts.
9. **Reproduction** — clean-environment known-answer reproduction with retained receipts.
10. **Orchestration** — cloud/agent systems may automate workflows without changing evidence semantics or approval boundaries.
11. **Commercial applications** — hosted collaboration, jurisdiction packs, integrations, and services.

## Cloud-neutral rule

The protocol and reference verifier must run locally without requiring a paid cloud service. External open-source dependencies may be pinned and audited; cloud providers remain optional adapters/deployment targets rather than protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with preparation, explanation, or proposed mappings, but an inferred output must never be silently promoted to a deterministic fact or approved mapping.

## Environmental source-selection rule

Environmental factors may enter a deterministic calculation only through an exact source-record ID and matching environmental material identity. ProofGrid does not perform fuzzy factor selection.

In v0.5, the target source-record ID is supplied by the mapping artifact and then validated. The engine does not derive that ID from the IFC material name.

## IFC quantity rule

ProofGrid extracts only quantities explicitly declared through supported `IfcElementQuantity` subtypes. Geometry-derived values are not produced by the v0.4/v0.5 conformance path.

Each supported declared quantity retains:

- quantity-set name and STEP ID;
- quantity name and STEP ID;
- IFC quantity type;
- declared numerical value;
- explicit quantity unit or project unit context when available;
- `value_source = declared_ifc_element_quantity`.

A v0.5 mapping must resolve the exact declared quantity identity and value. A changed STEP ID, type, name, value, or unit declaration fails closed.

## v0.5 unit-identity rule

v0.5 does **not** add a general unit-conversion subsystem.

The initial conformance gate recognizes exactly one IFC unit declaration as one environmental unit identity:

```text
IfcSIUnit
  UnitType = MASSUNIT
  Prefix   = KILO
  Name     = GRAM
          ↓
unit identity = kg
numerical conversion = none
```

The declared numerical quantity is unchanged. Any other IFC unit identity fails this v0.5 mapping gate unless a later separately versioned conversion/identity subsystem explicitly supports it.

## Mapping identity rule

Every mapping record must bind the source IFC and exact extracted identities needed to prevent stale or accidental remapping:

- source IFC SHA-256 and IFC schema;
- element GlobalId, STEP ID, and IFC type;
- material association STEP ID;
- material STEP ID, exact declared material name, and material source type;
- quantity-set STEP ID;
- quantity STEP ID, name, IFC quantity type, numerical value, and extracted unit declaration;
- explicit target `material_identity_id`;
- explicit target `source_record_id`;
- mapping review state, author, rationale, and optional reference.

A source IFC hash mismatch, identity mismatch, value mismatch, unit mismatch, blank/ambiguous material name, missing source record, or failed source-provenance check stops calculation.

## Mapping review-state rule

The current mapping schema permits `DRAFT` and `REVIEWED` states. The v0.5 calculation gate accepts only `REVIEWED` mappings.

`REVIEWED` is a **workflow/evidence state**, not a claim of professional licensure, scientific validation, program-operator verification, engineering approval, or regulatory approval. Those stronger authorities require separate evidence.

## Duplicate/conflict rule

- duplicate mapping IDs fail;
- duplicate mappings for one IFC material/quantity identity fail;
- conflicting environmental targets for one IFC identity fail;
- ProofGrid does not choose a winner automatically.

## Lifecycle/indicator rule

Mapped environmental source records used in one v0.5 calculation must share a compatible lifecycle/system boundary and indicator. The initial synthetic conformance path uses `GWP-total` and `A1/A2/A3`.

## Provenance receipt rule

A successful v0.5 mapping receipt retains, at minimum:

- mapping artifact version;
- mapping file SHA-256 and canonical-content SHA-256;
- IFC extraction artifact SHA-256;
- source IFC SHA-256 and IFC schema;
- IfcOpenShell adapter/version;
- environmental registry SHA-256;
- verified environmental source-content hashes;
- exact environmental source-record digest;
- mapping review metadata;
- exact mapped element/material/quantity identities;
- IFC unit declaration and canonical v0.5 unit identity;
- explicit `numerical_conversion_applied = false`;
- indicator and lifecycle boundary;
- mapped subtotal/total;
- receipt SHA-256;
- explicit limitations and `certified = false`.

## v0.5 known-answer conformance

The initial real-IFC synthetic conformance case is intentionally narrow:

- IFC4;
- one `IfcWall`;
- exact `IfcMaterial` association `Concrete`;
- declared `IfcQuantityWeight` named `Mass` = `1000.0`;
- project `MASSUNIT` = `KILO` + `GRAM`;
- explicit reviewed mapping target `concrete` / `RX-FICT-CONCRETE-A1A3`;
- synthetic factor `0.12 kgCO2e / kg`;
- lifecycle boundary `A1/A2/A3`;
- expected subtotal/total `120.0 kgCO2e`;
- no numerical unit conversion.

The known answer proves the declared software path, not real-project environmental validity.

## v0.5 acceptance gates

All inherited v0.3, v0.4, and clean-environment reproduction gates remain required, plus:

- strict Draft 2020-12 mapping schema;
- exact source IFC hash/schema matching;
- exact element/material/quantity identity matching;
- mapping state must be `REVIEWED`;
- blank/ambiguous material names cannot be inferred into environmental targets;
- no fuzzy material-name selection;
- only the declared v0.5 `KILO+GRAM → kg` identity bridge is accepted;
- no numerical unit conversion occurs in that bridge;
- environmental target material identity must match the chosen source record;
- chosen source record must pass the existing provenance/content-hash gate;
- duplicate/conflicting mappings fail;
- lifecycle boundary/indicator conflicts fail;
- mapping/extraction/source-record provenance is retained in the receipt;
- positive and adversarial real-IFC conformance tests pass;
- hosted CI reproduces the `120.0 kgCO2e` known answer;
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE` remains distinct from certification, professional approval, or real-building LCA validity.

## Evidence already established before v0.5

The prior stacked gates established:

- provenance-controlled environmental source records;
- read-only real IFC declared-data extraction;
- exact-head hosted CI receipts;
- clean-environment Linux/Windows reproduction of the synthetic environmental known answer;
- bit-identical primary environmental artifacts across the declared hosted runtime matrix.

These are software/provenance evidence layers, not substitutes for domain authority.

## Next evidence gates

1. Authorized production EPD/database connectors with explicit licensing, import provenance, and source-version controls.
2. Externally reviewed mapping artifacts using openly redistributable or properly authorized non-production source data.
3. A separately versioned deterministic unit-conversion subsystem if cross-unit mappings are required.
4. Broader IFC/material/quantity conformance packs without weakening exact mapping identity.
5. Independently reviewed real-project methodology before any real-building environmental claim.
6. Pilot measurement of time saved, errors detected, and reproducibility.
