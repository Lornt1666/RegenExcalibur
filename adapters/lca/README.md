# LCA / EPD Source Layer

Status: **provenance registry implemented; explicit IFC mapping implemented; v0.6 authorization-aware synthetic source import implemented; real provider ingestion remains blocked pending explicit authorization and format-specific conformance**.

ProofGrid's environmental source layer separates four questions that must not be collapsed into one another:

1. **Can the source bytes be accessed?**
2. **Are the declared storage/transformation/use/redistribution rights sufficient for the intended operation?**
3. **Can the bytes be parsed and normalized deterministically?**
4. **Is the resulting environmental record scientifically/professionally suitable for the real project?**

v0.6 proves only a bounded software path through questions 1–3 using synthetic local data. Question 4 remains outside this gate.

## Normalized environmental source records

Each ProofGrid source record retains:

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

## v0.6 source-import manifest

Before normalization, `schemas/source-import-manifest.schema.json` binds:

- provider/program/source locator;
- acquisition method, synthetic state, and intended use;
- authorization status;
- commercial-use permission;
- storage permission;
- transformation permission;
- redistribution permission;
- terms/reference identifier and local terms snapshot SHA-256;
- approval reference and validity date where applicable;
- source path, media type, format/version, and SHA-256;
- parser name/version/profile;
- intended normalized ProofGrid record ID.

The manifest is evidence about the declared permission decision. It does not itself expand rights granted by a third party.

## Authorization fail-closed rules

The v0.6 importer rejects:

- `UNKNOWN` authorization;
- `PUBLIC_ACCESS_ONLY` as sufficient import authority;
- `TEST_ONLY` authority on non-synthetic data or outside the declared internal test-fixture use;
- `EXPLICITLY_AUTHORIZED` without a non-empty approval reference;
- expired authorization;
- storage not explicitly allowed;
- transformation not explicitly allowed;
- commercial-tool use without explicit commercial-use permission;
- raw-source export without explicit redistribution permission.

**Public visibility is not treated as permission for API/tool/commercial/redistribution use.**

## Terms and source-byte integrity

Both the terms/reference snapshot and source bytes are independently SHA-256 checked before parsing. A mismatch fails closed.

Package references are resolved under the import-package directory; path escape attempts fail.

A hash proves the exact bytes evaluated. It does not prove that a legal interpretation of those bytes is correct; production provider integrations require a provider-specific reviewed authorization record.

## Initial v0.6 parser scope

The only accepted parser/profile in the initial gate is the RegenExcalibur synthetic XML carrier:

- format `RX-SYNTHETIC-EPD-CARRIER / 1.0`;
- parser `rx-synthetic-epd-carrier / 0.6.0`;
- profile `rx-synthetic-epd-carrier-1.0`.

This carrier is **not claimed to conform to ILCD+EPD, ECO Platform, ÖKOBAUDAT, EPD International, openEPD, or any programme-operator profile**. Unsupported format/parser/profile declarations fail.

The synthetic parser also rejects DTD/entity declarations.

## Normalization gate

Parsed data does not enter ProofGrid merely because XML parsing succeeded. The generated environmental record must then pass the existing `lca-source-records.schema.json` and exact source-content hash validation through the v0.3 registry validator.

The positive v0.6 fixture normalizes to:

- `RX-IMPORTED-SYNTH-CONCRETE-A1A3`;
- material identity `synthetic-import-concrete`;
- `1 kg` reference quantity;
- `GWP-total = 0.15 kgCO2e`;
- boundary `A1/A2/A3`;
- source verification state `UNVERIFIED`;
- synthetic state `true`;
- redistribution state `RESTRICTED`;
- explicit `FORMAT_NOT_CLAIMED_ILCD_EPD_COMPLIANT` quality flag.

## Raw-source redistribution boundary

Normalization and redistribution are different permissions.

The positive fixture allows synthetic local storage/transformation but prohibits raw-source redistribution. Therefore a successful import records `RESTRICTED` and does not copy the source into a redistributable output bundle.

If `--export-source` is requested while redistribution is prohibited, the importer fails before export.

A later production architecture may need an authorized source store separate from portable normalized receipts when provider terms prohibit redistributing raw data.

## v0.5 mapping consumption rule remains unchanged

For an IFC-derived calculation, an environmental record is never chosen from an IFC material name. The exact environmental `material_identity_id` and `source_record_id` must be supplied by an explicit mapping artifact and validated against the registry.

A v0.6-imported record may become a future mapping target only after its import provenance/rights state and subsequent mapping evidence satisfy the relevant gate. Successful import alone is not mapping approval or scientific suitability.

## Source-registry fail-closed rules remain unchanged

- no fuzzy material-to-factor matching;
- no implicit environmental unit conversion;
- material identity and exact source-record ID must agree;
- lifecycle/system boundary and indicator compatibility is enforced;
- duplicate/conflicting records fail;
- source-content hash mismatches fail;
- verified source states require their declared evidence;
- synthetic fixtures remain explicitly non-production.

## v0.6 hosted evidence

Initial Genesis #29 evidence:

- 45 tests passed;
- terms SHA-256 `18437a5c104ffe5b26a83004300d0b47c240bcc96e09b1119b9992da819fc601`;
- source SHA-256 `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`;
- normalized record digest `c155b0c66c8372688b97abb3288c9a9ed8d4906c8793f13f2aa9dce36b1a03fc`;
- normalized registry file SHA-256 `b8c1fdc87d4e788eff5b7fc3c6c66f31e0f6264f9c3c767c8bf8fd269d018b0b`;
- import receipt SHA-256 `fe5d8e838f0b9f8ec84eb56c49c6fde219a94b4c7556016c30f95be475cc858b`;
- rights decision `AUTHORIZED_FOR_DECLARED_IMPORT_ONLY` under synthetic `TEST_ONLY` authority;
- raw source export `false`.

## Boundary

A valid import receipt and source record can prove the declared software, permission-state, terms-byte, source-byte, parser, and normalization path. They do **not** establish:

- that the rights interpretation is legal advice;
- that a real provider authorizes use outside the manifest;
- official digital EPD format/profile conformance;
- scientific correctness or representativeness;
- real-product identity;
- professional LCA review;
- code, engineering, architecture, procurement, regulatory, or certification conclusions.

Real provider adapters remain blocked until provider-specific authorization, access method, storage/transformation/commercial/redistribution rights, and official format/profile handling are separately evidenced.
