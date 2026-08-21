# RegenExcalibur

## ProofGrid / RX Evidence Fabric

RegenExcalibur's current flagship reference implementation is **ProofGrid**: a cloud-neutral, machine-verifiable evidence kernel for built-environment data. It keeps claims, calculations, mapping decisions, source-use authority, provenance, integrity, IFC-declared data, environmental-source boundaries, and certification boundaries explicit.

### ProofGrid v0.6 quick start

Install the locked open-source dependencies:

```bash
python -m pip install -r requirements-proofgrid.txt
python -m pip check
```

Validate the fictional Alberta environmental-source registry:

```bash
python reference/rx_cli.py lca-registry-validate evidence/examples/alberta-house
```

Verify the fictional Alberta environmental fixture:

```bash
python reference/rx_cli.py verify evidence/examples/alberta-house
```

Inspect and extract real IFC-declared data:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
python reference/ifc_extract.py path/to/model.ifc --output ifc-extraction.json
```

Validate an explicit reviewed IFC-to-environmental mapping:

```bash
python reference/ifc_lca_map.py \
  --extraction ifc-extraction.json \
  --mapping ifc-environmental-mapping.json \
  --registry evidence/examples/alberta-house/lca-sources.json \
  --output ifc-environmental-mapping-receipt.json
```

Run the v0.6 authorization-aware source-import conformance fixture:

```bash
python reference/source_import.py \
  evidence/examples/source-import-v06 \
  --output-dir source-import-output \
  --as-of 2026-08-20
```

A successful synthetic import reports:

```text
RESULT: AUTHORIZED_SOURCE_IMPORT_VERIFIABLE
NOT CERTIFIED
```

and writes:

- `normalized-registry.json` — a normalized ProofGrid environmental source record;
- `import-receipt.json` — rights, terms, source-byte, parser, normalized-record, and output provenance.

## v0.6: authorization before normalization

v0.6 treats source-use authority as executable policy input. A source being publicly visible or technically parseable does **not** authorize ProofGrid to store, transform, use commercially, or redistribute it.

The import manifest separately records:

- acquisition method and intended use;
- synthetic/test state;
- authorization status;
- commercial-use permission;
- storage permission;
- transformation permission;
- redistribution permission;
- terms reference and hashed terms snapshot;
- approval reference and expiry where applicable;
- source path/media type/declared format and SHA-256;
- parser name/version/profile;
- normalized ProofGrid record ID.

The importer fails closed for unknown/public-only authority, invalid test-only use, missing or expired explicit approval, insufficient storage/transformation/commercial/redistribution rights, terms/source tampering, path escape, unsupported parser profiles, and normalized source-record schema/provenance failure.

### Synthetic v0.6 known answer

The checked-in fixture is deliberately not a real EPD and is not claimed to conform to ILCD+EPD or a programme-operator profile.

Its policy state is:

- authorization: `TEST_ONLY`;
- intended use: `INTERNAL_TEST`;
- storage: `ALLOWED`;
- transformation: `ALLOWED`;
- commercial use: `PROHIBITED`;
- redistribution: `PROHIBITED`;
- raw source export: not requested and not performed.

The source normalizes to exactly one ProofGrid record:

- ID `RX-IMPORTED-SYNTH-CONCRETE-A1A3`;
- material `synthetic-import-concrete`;
- `1.0 kg` reference quantity;
- `GWP-total = 0.15 kgCO2e`;
- `A1/A2/A3` lifecycle boundary;
- synthetic + unverified state;
- redistribution status `RESTRICTED`.

Genesis #29 proved the initial v0.6 implementation with **45/45 hosted tests**.

Authoritative initial hashes from that run:

- manifest content SHA-256: `78fea8f1c85bb15fd4471a5fa29644f65ea69d88104e4c69b222e85f28712c21`;
- manifest file SHA-256: `b6b6634569d5b14131041c400bb8fd560d7ddde9bdb8015b85cfdd02e04f9ab5`;
- terms SHA-256: `18437a5c104ffe5b26a83004300d0b47c240bcc96e09b1119b9992da819fc601`;
- source SHA-256: `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`;
- normalized record canonical SHA-256: `c155b0c66c8372688b97abb3288c9a9ed8d4906c8793f13f2aa9dce36b1a03fc`;
- normalized registry file SHA-256: `b8c1fdc87d4e788eff5b7fc3c6c66f31e0f6264f9c3c767c8bf8fd269d018b0b`;
- import receipt SHA-256: `fe5d8e838f0b9f8ec84eb56c49c6fde219a94b4c7556016c30f95be475cc858b`.

## v0.5 mapping known answer remains intact

The hosted v0.5 conformance path still proves one explicit `IfcQuantityWeight / Mass = 1000.0` mapped to exact source record `RX-FICT-CONCRETE-A1A3`, producing:

```text
120.0 kgCO2e
```

The only v0.5 unit identity bridge remains IFC `MASSUNIT`, `KILO` + `GRAM` → identity `kg`, with no numerical conversion.

## Hard boundaries

- `VERIFIABLE` is **not** `CERTIFIED`.
- `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE` does not prove legal interpretation, scientific validity, provider verification, or professional approval.
- Public/basic web access does not automatically authorize API/tool/commercial/redistribution use.
- The v0.6 positive fixture grants no rights to any real provider dataset.
- The initial v0.6 parser accepts only the RegenExcalibur synthetic carrier and makes no ILCD+EPD compliance claim.
- Raw-source redistribution is a separate permission from normalization.
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE` is not an LCA conclusion or professional approval.
- Source integrity is not scientific validation.
- IFC extraction is not geometry-derived takeoff.
- IFC material strings do not choose environmental records.
- Mapping `REVIEWED` is a workflow state, not independent professional/scientific review.
- No code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion is produced by these gates.

Key files:

- `CONSTITUTION.md`: truth, authority, privacy, evidence, and safety invariants.
- `ARCHITECTURE.md`: ProofGrid/RX Evidence Fabric architecture and gates.
- `specs/rxep/`: RX Evidence Protocol semantics.
- `schemas/lca-source-records.schema.json`: normalized environmental-source registry schema.
- `schemas/ifc-extraction.schema.json`: IFC declared-data extraction schema.
- `schemas/ifc-lca-mapping.schema.json`: explicit IFC-to-environmental mapping schema.
- `schemas/source-import-manifest.schema.json`: v0.6 acquisition/use-rights/source/parser manifest schema.
- `reference/rx_cli.py`: environmental verifier and registry validator.
- `reference/ifc_extract.py`: IFC declared-data extractor.
- `reference/ifc_lca_map.py`: explicit mapping validator/calculator.
- `reference/source_import.py`: authorization-aware source importer.
- `adapters/ifc/`: IFC adapter documentation and implementation.
- `adapters/lca/`: environmental source/import/mapping boundaries.
- `reproduction/`: clean-environment reproduction package.
- `evidence/examples/source-import-v06/`: synthetic authorization/import fixture.
- `tests/`: fail-closed schema, provenance, IFC, mapping, rights, and import tests.

---

## Freelance / Contract Work — 1JGM

**Justice Gray Maciocha — 1JGM, Blueprint-to-Bot Systems Operator** is accepting remote, asynchronous, deliverable-based freelance work in market and competitor research, spreadsheet/listing QA, AI evaluation, prompt and workflow design, technical documentation, automation specifications, project operations, construction technology, and construction-informed CAD/visualization support.

- **Full capability and service profile:** [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md)
- **Work contact:** `justlornt95+redditwork@gmail.com`
- **Location/time zone:** Alberta, Canada — Mountain Time
- **Engagement model:** Evening/weekend asynchronous work, small paid trials, hourly or fixed-price milestones

The service profile separates demonstrated capability from learnable adjacent work and does not claim professional licensure, universal expertise, production deployment, or independent certification without supporting evidence.

---

## Existing GCP orchestration scaffold

The repository retains the earlier GCP-oriented deployment/orchestration scaffold as an optional layer. Live provisioning remains dry-run-first and can create billable resources only when explicitly applied.

## Status

ProofGrid v0.6 is a **reference implementation under evidence-gated development**. Proven stacked gates now include provenance-controlled environmental source records, real IFC declared-data extraction, clean-environment reproduction, explicit IFC→environmental mapping, and a synthetic authorization-aware source-import boundary. Real provider adapters, real EPD/database credentials, official ILCD+EPD/profile conformance, scientific source suitability, real-product identity, professional review, real-building LCA validity, and production deployment remain separate future gates.
