# RegenExcalibur ProofGrid / RX Evidence Fabric — Architecture v0.6

## Mission

Make built-environment claims independently inspectable without pretending that software integrity, data access, or workflow review equals scientific validity, legal authority, professional approval, regulatory approval, or certification.

## v0.6 execution kernel

```text
AUTHORIZED SOURCE-IMPORT PATH

source-import manifest
    │
    ├─ provider / source locator
    ├─ acquisition method + intended use
    ├─ synthetic/test state
    ├─ authorization status
    ├─ commercial/storage/transformation/redistribution permissions
    ├─ terms reference + terms snapshot SHA-256
    ├─ approval reference + expiry when applicable
    ├─ source path/media type/format/version/SHA-256
    ├─ parser name/version/profile
    └─ target normalized source-record ID
    ↓
Draft 2020-12 manifest validation
    ↓
fail-closed rights/use decision
    ↓
terms snapshot SHA-256 verification
    ↓
source-content SHA-256 verification
    ↓
versioned parser/profile gate
    ↓
normalized ProofGrid environmental source record
    ↓
existing v0.3 source-record schema + source-content provenance gate
    ↓
authorization/import receipt + normalized registry artifact

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
    ├─ element/material/quantity exact identities
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

NO PUBLIC-ACCESS ⇒ AUTHORIZATION ASSUMPTION
NO AUTHENTICATION OR TERMS BYPASS
NO FUZZY IFC MATERIAL → ENVIRONMENTAL SOURCE SELECTION
NO GENERAL UNIT CONVERSION
NO GEOMETRY-DERIVED QUANTITY TAKEOFF
```

The v0.6 architectural change is that **environmental source acquisition itself becomes an evidence-gated operation**. A parser being able to read bytes is not permission to acquire, store, transform, use commercially, or redistribute those bytes.

## Architectural layers

1. **Constitution** — safety, truth, authority, privacy, reversibility, accountability.
2. **Schema / Protocol** — RXEP and canonical building/material/environmental-source/IFC-extraction/mapping/import structures.
3. **Rights and acquisition evidence** — explicit authorization state, intended use, terms snapshots, approval references, expiry, and permission dimensions.
4. **Source provenance** — exact environmental source records, source-content hashes, units, boundaries, versions, verification state, and redistribution state.
5. **IFC evidence extraction** — source hash, hierarchy, units, declared quantities, material associations, and warnings.
6. **Explicit mapping evidence** — reviewed mapping records binding exact IFC identities to exact environmental source records.
7. **Adapters/parsers** — pinned IfcOpenShell plus versioned, provider/format-specific environmental parsers only when authorized.
8. **Deterministic engines** — auditable validation and calculations independent of generative AI.
9. **Evidence graph / receipts** — provenance-bearing machine-readable artifacts.
10. **Reproduction** — clean-environment known-answer reproduction with retained receipts.
11. **Orchestration** — cloud/agent systems may automate workflows without changing evidence semantics or permission boundaries.
12. **Commercial applications** — permitted only when the relevant source/use rights explicitly allow the intended use.

## Cloud-neutral rule

The protocol and reference verifier must run locally without requiring a paid cloud service. External dependencies may be pinned and audited; cloud providers remain optional adapters/deployment targets rather than protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with preparation, explanation, proposed mappings, or source research, but inferred outputs and guessed permissions must not be silently presented as deterministic facts or authorized actions.

## v0.6 authorization-before-parsing rule

The importer evaluates declared authorization and use rights **before** source normalization.

The current policy fails closed when:

- authorization is `UNKNOWN`;
- authorization is only `PUBLIC_ACCESS_ONLY`;
- `TEST_ONLY` authority is applied to non-synthetic data or outside `TEST_FIXTURE / INTERNAL_TEST` use;
- `EXPLICITLY_AUTHORIZED` lacks a non-empty approval reference;
- declared authorization is expired at the policy-evaluation date;
- source storage is not explicitly `ALLOWED`;
- transformation is not explicitly `ALLOWED`;
- `COMMERCIAL_TOOL` use is requested without `commercial_use = ALLOWED`;
- raw-source export is requested without `redistribution = ALLOWED`.

Public visibility is therefore treated as a discovery/access fact, not a rights grant.

## Terms/source integrity rule

The import manifest binds both:

- a terms/reference snapshot with SHA-256; and
- the exact source bytes with SHA-256.

Either mismatch fails before normalization. Paths are resolved inside the import package and may not escape it.

A terms hash proves which terms bytes were evaluated; it does not prove that the manifest's legal interpretation is correct. Provider-specific production adapters require their own reviewed authorization evidence.

## Parser/profile rule

The initial v0.6 parser accepts only:

```text
media type: application/xml
format: RX-SYNTHETIC-EPD-CARRIER / 1.0
parser: rx-synthetic-epd-carrier / 0.6.0
profile: rx-synthetic-epd-carrier-1.0
```

This is a RegenExcalibur synthetic conformance carrier. It is **not claimed to conform to ILCD+EPD, ECO Platform, ÖKOBAUDAT, EPD International, openEPD, or any programme-operator profile**.

Unsupported format/parser/profile declarations fail closed. DTD/entity declarations are rejected by the synthetic XML parser.

## Normalization rule

A parsed source may enter a ProofGrid normalized registry only after the generated record passes the existing environmental-source schema and source-content provenance validator.

The initial synthetic record normalizes to:

- record ID `RX-IMPORTED-SYNTH-CONCRETE-A1A3`;
- material identity `synthetic-import-concrete`;
- declared unit `kg`;
- reference quantity `1.0`;
- `GWP-total = 0.15 kgCO2e`;
- lifecycle modules `A1/A2/A3`;
- verification state `UNVERIFIED`;
- synthetic state `true`;
- source-content SHA-256 `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`;
- redistribution status `RESTRICTED` under the current test authorization.

The record carries `FORMAT_NOT_CLAIMED_ILCD_EPD_COMPLIANT` as an explicit data-quality flag.

## Raw-source redistribution rule

Normalization and redistribution are separate permissions.

The v0.6 positive fixture permits local storage/transformation for the synthetic test but prohibits raw-source redistribution. Therefore the normal successful run produces a normalized registry and receipt while recording:

```text
raw_export.requested = false
raw_export.exported  = false
redistribution_status = RESTRICTED
```

A requested raw export fails unless redistribution is explicitly allowed.

This design prevents a successful parser/import from silently converting restricted source bytes into a redistributable package.

## Environmental source-selection rule

Environmental factors may enter a calculation only through an exact source-record ID and matching environmental material identity. v0.6 changes how an authorized source record may be created; it does not weaken v0.3/v0.5 source-selection rules.

## IFC quantity and mapping rules

The v0.4/v0.5 rules remain unchanged:

- only supported explicitly declared `IfcElementQuantity` values are extracted;
- geometry-derived takeoff is outside the gate;
- a v0.5 mapping must resolve exact IFC source/element/material/quantity identities;
- a material string does not choose an environmental factor;
- only `REVIEWED` mapping records enter the v0.5 calculation gate;
- `REVIEWED` remains a workflow state, not professional/scientific authority;
- duplicate/conflicting mappings fail closed;
- the only v0.5 unit identity bridge is IFC `MASSUNIT + KILO + GRAM → kg`, with no numerical conversion.

## v0.6 import receipt rule

A successful `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE` receipt retains:

- importer name/version;
- import ID;
- manifest file SHA-256 and canonical-content SHA-256;
- evaluated authorization decision and evaluation date;
- declared intended use and permission dimensions;
- terms reference, snapshot path/hash, approval reference, and expiry;
- provider/program/source locator;
- source path/hash/media type/declared format;
- redistribution state and raw-export state;
- parser name/version/profile;
- parsed source identity;
- normalized record ID and canonical digest;
- normalized registry file SHA-256;
- verified source-content hash list;
- receipt SHA-256;
- explicit limitations and `certified = false`.

## v0.6 hosted known-answer evidence

Genesis #29 on the initial implementation proved:

- `45` hosted tests passed;
- rights decision `AUTHORIZED_FOR_DECLARED_IMPORT_ONLY`;
- authorization status `TEST_ONLY`;
- intended use `INTERNAL_TEST`;
- commercial use `PROHIBITED`;
- storage/transformation `ALLOWED`;
- redistribution `PROHIBITED`;
- terms SHA-256 `18437a5c104ffe5b26a83004300d0b47c240bcc96e09b1119b9992da819fc601`;
- source SHA-256 `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`;
- normalized record digest `c155b0c66c8372688b97abb3288c9a9ed8d4906c8793f13f2aa9dce36b1a03fc`;
- normalized registry file SHA-256 `b8c1fdc87d4e788eff5b7fc3c6c66f31e0f6264f9c3c767c8bf8fd269d018b0b`;
- import receipt SHA-256 `fe5d8e838f0b9f8ec84eb56c49c6fde219a94b4c7556016c30f95be475cc858b`;
- no raw source export.

All inherited v0.3-v0.5 gates remained green.

## v0.6 acceptance gates

All inherited gates remain required, plus:

- strict Draft 2020-12 import-manifest validation;
- authorization/use decision occurs before normalization;
- `UNKNOWN` and `PUBLIC_ACCESS_ONLY` fail;
- test-only authority cannot be reused for non-synthetic/general use;
- explicit authorization requires approval evidence;
- expired authorization fails;
- storage/transformation/commercial/redistribution dimensions are separately enforced;
- terms/source hashes are exact;
- package path escape fails;
- unsupported parser/profile fails;
- malformed/invalid normalized records fail the existing source-registry gate;
- raw-source export is independently rights-gated;
- importer receipt retains rights, source, parser, and normalized-record provenance;
- positive and adversarial tests pass in hosted CI;
- `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE` remains distinct from legal advice, scientific validation, professional LCA review, provider/programme verification, or certification.

## Next evidence gates

1. Official-format conformance against openly redistributable validation fixtures and authoritative schemas/profiles, without importing restricted provider datasets.
2. Provider-specific authorization records and adapters only after access/storage/transformation/commercial/redistribution terms are explicitly evidenced.
3. Externally reviewed mapping artifacts using properly authorized non-production source data.
4. A separately versioned deterministic unit-conversion subsystem if broader cross-unit mappings are required.
5. Independently reviewed real-project methodology before any real-building environmental claim.
6. Pilot measurement of time saved, errors detected, and reproducibility.
