# RegenExcalibur

## ProofGrid / RX Evidence Fabric

RegenExcalibur's current flagship reference implementation is **ProofGrid**: a cloud-neutral, machine-verifiable evidence kernel for built-environment data. It is designed to keep claims, calculations, mapping decisions, review states, provenance, integrity, environmental-source boundaries, IFC-declared data, and certification boundaries explicit.

### ProofGrid v0.5 quick start

Install the locked open-source dependencies:

```bash
python -m pip install -r requirements-proofgrid.txt
python -m pip check
```

Validate the fictional Alberta environmental-source registry and its source-content hashes:

```bash
python reference/rx_cli.py lca-registry-validate evidence/examples/alberta-house
```

Verify the fictional Alberta environmental fixture:

```bash
python reference/rx_cli.py verify evidence/examples/alberta-house
```

Inspect a real IFC STEP file structurally:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

Extract IFC-declared quantities, material associations, unit context, hierarchy, warnings, and source provenance:

```bash
python reference/ifc_extract.py path/to/model.ifc --output ifc-extraction.json
```

Validate an **explicit reviewed** IFC-to-environmental mapping artifact and calculate only the mapped declared quantities:

```bash
python reference/ifc_lca_map.py \
  --extraction ifc-extraction.json \
  --mapping ifc-environmental-mapping.json \
  --registry evidence/examples/alberta-house/lca-sources.json \
  --output ifc-environmental-mapping-receipt.json
```

ProofGrid v0.5 preserves the provenance-controlled environmental-source path and the evidence-controlled IFC extraction path, then adds a deliberately narrow mapping bridge between them. The bridge does **not** infer a factor from an IFC material name. A mapping artifact must explicitly name the exact IFC identities and exact environmental source record, and the verifier checks those identities before any calculation proceeds.

### v0.5 known-answer gate

The hosted conformance path uses a synthetic real-IFC fixture with:

- one `IfcWall`;
- one exact `IfcMaterial` association named `Concrete`;
- one declared `IfcQuantityWeight` named `Mass` = `1000.0`;
- IFC project mass unit `KILO` + `GRAM`;
- an explicit `REVIEWED` mapping to material identity `concrete` and source record `RX-FICT-CONCRETE-A1A3`;
- synthetic factor `0.12 kgCO2e/kg`;
- lifecycle boundary `A1/A2/A3`.

The v0.5 unit gate recognizes that specific IFC mass-unit declaration as the identity `kg` while leaving the numerical value unchanged. The expected synthetic mapped result is:

```text
120.0 kgCO2e
```

This is a software/provenance known answer, not a real-building LCA conclusion.

### Hard boundaries

- `VERIFIABLE` is **not** `CERTIFIED`.
- `EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE` is **not** professional approval or environmental certification.
- Source integrity is not scientific validation.
- IFC extraction is not a geometry-derived takeoff.
- IFC material strings do not choose environmental records.
- The mapping target must be supplied explicitly and resolve to an exact source-record ID.
- A mapping must match the exact source IFC hash/schema and exact element/material/quantity identities.
- v0.5 performs no general unit conversion.
- The only v0.5 unit bridge is IFC `MASSUNIT`, `KILO` + `GRAM` → identity `kg`, with `numerical_conversion_applied = false`.
- `REVIEWED` is a mapping workflow state, not a claim of professional licensure or independent scientific review.
- Conflicting/duplicate mappings fail closed rather than being auto-resolved.
- No code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion is produced by the mapping verifier.

Key files:

- `CONSTITUTION.md`: evidence, safety, authority, privacy, interoperability, and truth-before-promotion invariants.
- `ARCHITECTURE.md`: ProofGrid/RX Evidence Fabric architecture and evidence gates.
- `specs/rxep/`: RX Evidence Protocol specification and evidence-envelope schema.
- `schemas/building.schema.json`: canonical project/building fixture schema.
- `schemas/materials.schema.json`: material quantities with exact environmental source-record references.
- `schemas/lca-source-records.schema.json`: environmental-source registry schema.
- `schemas/ifc-extraction.schema.json`: IFC declared-data extraction schema.
- `schemas/ifc-lca-mapping.schema.json`: v0.5 explicit IFC-to-environmental mapping schema.
- `reference/rx_cli.py`: deterministic environmental verifier, registry validator, and structural IFC inspection CLI.
- `reference/ifc_extract.py`: declared IFC quantity/material extraction CLI.
- `reference/ifc_lca_map.py`: v0.5 explicit mapping validator/calculator.
- `adapters/ifc/`: structural inspection and declared-data extraction adapters.
- `adapters/lca/`: environmental-source provenance and mapping-boundary rules.
- `reproduction/`: clean-environment reproduction manifest, harness, and external worksheet.
- `evidence/examples/`: fictional test fixtures and hashed synthetic source content.
- `tests/`: fail-closed provenance, schema, determinism, real IFC, extraction, mapping, and portability conformance tests.

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

The repository also retains the earlier GCP-oriented autonomous deployment and orchestration scaffold. It coordinates infrastructure-as-code, Cloud Run, Cloud Functions, Pub/Sub, Vertex AI pipeline scaffolding, multi-agent MRV workflows, security controls, observability, and operational runbooks.

This is treated as an **optional deployment/orchestration layer**, not the identity of the ProofGrid core.

### Existing scaffold contents

- [RegenExcalibur_Project.zip](RegenExcalibur_Project.zip): packaged project archive.
- [RegenExcalibur_Project](RegenExcalibur_Project): expanded project source and deployment scaffold.
- [RegenExcalibur_Project/01_Documentation_and_Readme/README.md](RegenExcalibur_Project/01_Documentation_and_Readme/README.md): detailed operational instructions.
- [RegenExcalibur_Project/master_autonomous_execution_script.py](RegenExcalibur_Project/master_autonomous_execution_script.py): dry-run-first deployment entry point.

### Safety notice

The GCP deployment automation defaults to dry-run mode. Live provisioning requires the explicit `--apply` flag and can create billable GCP resources. Review Terraform, IAM, Cloud Build, and runtime configuration before applying.

### GCP quick start

```bash
python RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_PROJECT_ID \
  --region us-central1
```

To deploy only after reviewing the dry run:

```bash
python RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_PROJECT_ID \
  --region us-central1 \
  --apply
```

## Status

ProofGrid v0.5 is a **reference implementation under evidence-gated development**. The source registry, real IFC declared-data extraction, clean-environment reproduction package, and narrow explicit IFC→environmental mapping path have hosted conformance evidence on stacked development branches. The current v0.5 gate allows only explicit reviewed mapping records and one narrowly declared mass-unit identity bridge; it does not authorize fuzzy mapping, general unit conversion, production EPD/database ingestion, geometry-derived takeoff, professional code/compliance conclusions, real-building environmental validity, or production deployment.
