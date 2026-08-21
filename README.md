# RegenExcalibur

## ProofGrid / RX Evidence Fabric

ProofGrid is RegenExcalibur's cloud-neutral, machine-verifiable evidence kernel for built-environment data. It keeps source-use authority, format conformance, provenance, IFC-declared data, mapping decisions, deterministic calculations, review state, and certification boundaries explicit.

## ProofGrid v0.7 quick start

Install the frozen inherited ProofGrid dependency lock and the isolated v0.7 XML-schema lock:

```bash
python -m pip install -r requirements-proofgrid.txt
python -m pip install -r requirements-proofgrid-v07.txt
python -m pip check
```

The proven v0.7 XML validation pair is:

- `xmlschema==4.3.1`
- `elementpath==5.1.2`

The earlier `xmlschema==4.3.2` candidate was rejected by hosted CI because it required `elementpath>=5.1.3`, which was not available from the runner's package index. The gate was repaired by using the compatible 4.3.1 patch release; no validation or security rule was weakened.

### Authoritative ILCD+EPD v1.3 conformance

v0.7 validates against immutable InData upstream commits rather than vendoring or silently following moving branches:

- `InDataWG/ILCD-EPD-Data-Format` @ `7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`;
- `InDataWG/ILCD-EPD-Master-Data` @ `32117b6a70d6c486344247a429449755a2c7eab4`.

With those repositories checked out locally, run:

```bash
python reference/ilcd_epd_v13_conformance.py \
  --format-root .proofgrid-upstream/ilcd-epd-format \
  --master-root .proofgrid-upstream/ilcd-epd-master-data \
  --output-dir ilcd-v13-output
```

A successful run reports:

```text
RESULT: ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
PROFILE VALIDATION: NOT PERFORMED
NOT CERTIFIED
```

The v0.7 gate proves:

- exact upstream commit identity;
- exact authoritative `schemas/EPD_DataSet.xsd` git-object identity;
- XSD validation of InData's official v1.3 example;
- XSD validation of a deterministic ProofGrid synthetic derivative;
- selected authoritative EN 15804+A2 master-data identity resolution;
- local/sandbox-only schema composition;
- defused XML parsing;
- rejection of malformed/schema-invalid inputs, tampered XSD bytes, wrong upstream commits, and unpinned remote schema resolution.

It **does not** claim v1.3 validation-profile compliance. InData currently identifies v1.3 as the current format while v1.3 validation profiles remain a separate developing layer. Published v1.2 profile validation is therefore a different compatibility gate.

### v0.7 hosted known answer

The first green dedicated v0.7 run established:

- 51/51 tests with the v0.7 lock installed;
- Python `3.11.16`;
- `xmlschema 4.3.1`;
- `elementpath 5.1.2`;
- authoritative XSD SHA-256 `2cf30de74b6a9607503aa99d791b196a88c709b9975546d837789bf1bdb93d0a`;
- official InData v1.3 example SHA-256 `78476ee519b243088a226b013beb2d7b810d824a177070fcedb43011daa21a50`;
- selected EN 15804+A2 master-data file SHA-256 `56527da732b221c30cba7b1314c4ce6bae90b8804ba157927299c0193af2990f`;
- synthetic derivative SHA-256 `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- conformance receipt SHA-256 `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`.

The retained workflow artifact is evidence of that run; the documentation-complete branch must still receive its own exact-head receipt before issue #14 is closed.

## Inherited evidence gates

v0.7 sits on top of, and does not weaken, the existing gates:

- **v0.3** — provenance-controlled environmental source registry;
- **v0.4** — real IFC declared-data extraction;
- **R5 reproduction** — clean-environment Linux/Windows known-answer reproduction;
- **v0.5** — explicit reviewed IFC→environmental source mapping, including the `1000 kg → 120.0 kgCO2e` synthetic known answer with no numerical conversion;
- **v0.6** — authorization-aware source import, where access/use rights are evaluated before normalization.

Run the v0.6 synthetic authorization fixture with:

```bash
python reference/source_import.py \
  evidence/examples/source-import-v06 \
  --output-dir source-import-output \
  --as-of 2026-08-20
```

Its successful state remains `AUTHORIZED_SOURCE_IMPORT_VERIFIABLE`, not certification or permission to use a real provider dataset.

## Hard boundaries

- `VERIFIABLE` is **not** `CERTIFIED`.
- `ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT` means the declared format/master-data checks passed against pinned upstreams; it is not validation-profile compliance, scientific validation, provider approval, or professional LCA review.
- A format being parseable or XSD-valid does not establish permission to acquire, store, transform, commercially use, or redistribute source data.
- v0.6 authorization evidence remains required independently of v0.7 format conformance.
- Real provider EPD ingestion remains blocked until provider-specific access/use authority and an appropriate provider/format adapter are separately evidenced.
- IFC extraction is not geometry-derived takeoff.
- IFC material strings do not select environmental records.
- Mapping `REVIEWED` is a workflow state, not independent professional/scientific review.
- No code-compliance, engineering, architectural, procurement, regulatory, environmental-certification, or product-representativeness conclusion is produced by these software gates.

## Key files

- `CONSTITUTION.md` — truth, authority, privacy, evidence, and safety invariants.
- `ARCHITECTURE.md` — ProofGrid architecture and evidence gates.
- `specs/rxep/README.md` — RXEP and supporting-receipt semantics.
- `requirements-proofgrid.txt` — frozen inherited ProofGrid lock.
- `requirements-proofgrid-v07.txt` — isolated v0.7 XML validation lock.
- `schemas/lca-source-records.schema.json` — normalized environmental source records.
- `schemas/source-import-manifest.schema.json` — v0.6 source-use/rights manifest.
- `schemas/ifc-extraction.schema.json` — IFC declared-data extraction.
- `schemas/ifc-lca-mapping.schema.json` — explicit IFC→environmental mapping.
- `reference/source_import.py` — v0.6 authorization-aware importer.
- `reference/ilcd_epd_v13_conformance.py` — v0.7 authoritative XSD/master-data conformance validator.
- `conformance/ilcd-epd-v13/upstream.json` — immutable upstream pins and profile boundary.
- `.github/workflows/proofgrid-v07-ilcd-epd.yml` — dedicated v0.7 hosted gate.
- `reproduction/` — clean-environment reproduction package.
- `tests/` — fail-closed schema, provenance, IFC, mapping, rights, import, and official-format conformance tests.

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

ProofGrid v0.7 is a **reference implementation under evidence-gated development**. The authoritative v1.3 XSD/master-data lane has a green implementation receipt on the current development stack; the documentation-complete head must receive a final exact-head receipt before the v0.7 issue is completed. Real provider ingestion, v1.3 validation-profile compliance, v1.2 published-profile compatibility, real-product identity, scientific source suitability, professional review, real-building LCA validity, and production deployment remain separate gates.
