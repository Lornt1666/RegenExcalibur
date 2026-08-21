# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.4

## Mission

Make built-environment claims independently inspectable without pretending that software integrity equals scientific validity, professional review, or certification.

## v0.4 execution kernel

```text
ENVIRONMENTAL EVIDENCE PATH

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

IFC DECLARED-DATA PATH

IFC (.ifc)
   ↓
IfcOpenShell parser
   ↓
source SHA-256 + IFC schema + project unit context
   ↓
project/site/building/storey/space hierarchy
   ↓
IfcMaterial associations + IfcElementQuantity values
   ↓
conflict / ambiguity / missing-data warnings
   ↓
Draft 2020-12 IFC extraction artifact

NO IFC→LCA LINK EXISTS IN v0.4
```

The environmental and IFC extraction paths remain deliberately separated. The next integration gate must connect extracted quantities/material identities to exact environmental source records without fuzzy matching, hidden unit conversion, or silent ambiguity resolution.

## Architectural layers

1. **Constitution** — safety, truth, authority, privacy, reversibility, accountability.
2. **Schema / Protocol** — RXEP and canonical building/material/environmental-source/IFC-extraction structures.
3. **Source provenance** — exact source records, source-content hashes, units, boundaries, versions, verification state, licensing metadata.
4. **IFC evidence extraction** — source hash, spatial hierarchy, units, declared quantities, material associations, warnings.
5. **Adapters** — IfcOpenShell plus future authorized EPD/LCA database connectors.
6. **Deterministic engine** — auditable calculations independent of generative AI.
7. **Evidence graph** — provenance-bearing machine-readable artifacts.
8. **Orchestration** — existing cloud/agent systems may automate workflows without changing evidence semantics.
9. **Commercial applications** — hosted collaboration, jurisdiction packs, integrations, services.

## Cloud-neutral rule

The protocol and reference verifier must run locally without requiring a paid cloud service. External open-source dependencies may be pinned and audited; cloud providers remain optional adapters/deployment targets rather than protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with extraction, mapping, and explanation, but inferred outputs must not be silently presented as deterministic facts.

## Environmental source-selection rule

Environmental factors may enter the deterministic GWP calculation only through an exact source-record ID and exact material-identity match. ProofGrid does not perform fuzzy factor selection.

## Environmental unit rule

The v0.3/v0.4 environmental calculation performs no implicit unit conversion. A material quantity unit must exactly match the selected environmental source record's declared unit.

## IFC quantity rule

ProofGrid v0.4 extracts only quantities explicitly declared through supported `IfcElementQuantity` subtypes. Geometry-derived values are not produced in this slice.

Each declared quantity retains:

- quantity-set name and STEP ID;
- quantity name and STEP ID;
- IFC quantity type;
- declared numerical value;
- explicit quantity unit or project unit context when available;
- `value_source = declared_ifc_element_quantity`.

## IFC unit rule

IFC values remain in their declared context. No conversion is performed. Alternate prefixes such as `MILLI` are retained in the extraction artifact rather than normalized silently.

## IFC material rule

Supported material relationships are preserved as IFC evidence inputs. Material names—including blank or ambiguous names—are not mapped to environmental source records by name. Ambiguity generates warnings.

## Conflict rule

Duplicate or conflicting declared quantities remain visible. ProofGrid emits deterministic warnings and does not choose a preferred value automatically.

## v0.4 acceptance gates

The inherited v0.3 gates remain required, plus:

- a strict Draft 2020-12 IFC extraction schema exists;
- source IFC SHA-256 and IFC schema are retained;
- project/site/building/storey/space hierarchy preserves STEP IDs, GlobalIds, and parent identifiers;
- project unit context is retained;
- explicit quantity units override project unit context when present;
- declared IFC length/area/volume/weight/count/time quantity types are supported;
- no geometry-derived quantity is mislabeled as declared data;
- material associations and supported material layer/constituent/profile/list structures are preserved;
- millimetre-prefixed values remain millimetre-prefixed without hidden conversion;
- absent quantities emit warnings;
- duplicate/conflicting quantities emit warnings and remain in the artifact;
- ambiguous material names emit warnings and remain unmapped;
- extraction output validates before success is reported;
- hosted CI exercises known-answer IFC4 hierarchy/unit/material/quantity fixtures;
- the environmental registry and known-answer GWP path remain green;
- no IFC→LCA factor linkage exists in this slice;
- `VERIFIABLE` remains distinct from `CERTIFIED`.

## Next evidence gates

1. Evidence-controlled mapping between extracted IFC quantities/material identities and exact environmental source records.
2. An explicitly versioned unit-conversion subsystem if cross-unit mapping is required.
3. Authorized production EPD/database connectors with explicit licensing and import provenance.
4. Independently reproduced non-production building example.
5. Pilot measurement of time saved, errors detected, and reproducibility.
