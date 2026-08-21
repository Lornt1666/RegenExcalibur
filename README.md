# RegenExcalibur

## ProofGrid / RX Evidence Fabric

RegenExcalibur's current flagship reference implementation is **ProofGrid**: a cloud-neutral, machine-verifiable evidence kernel for built-environment data. It is designed to keep claims, calculations, review states, provenance, integrity, environmental-source boundaries, IFC-declared data, and certification boundaries explicit.

### ProofGrid v0.4 quick start

Install the locked open-source dependencies:

```bash
python -m pip install -r requirements-proofgrid.txt
python -m pip check
```

Validate the fictional Alberta environmental-source registry and its source-content hashes:

```bash
python reference/rx_cli.py lca-registry-validate evidence/examples/alberta-house
```

Verify the fictional Alberta fixture:

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

ProofGrid v0.4 preserves the v0.3 provenance-controlled environmental-source path and adds a separate evidence-controlled IFC extraction path. It retains source IFC SHA-256, IFC schema, project unit assignments, spatial identifiers, supported material associations, and supported `IfcElementQuantity` values. The extraction artifact validates against JSON Schema Draft 2020-12 before the CLI reports success.

### Hard boundaries

- `VERIFIABLE` is **not** `CERTIFIED`.
- Source integrity is not scientific validation.
- IFC extraction is not a geometry-derived takeoff.
- IFC quantity values are not silently converted between units.
- Material names are not fuzzy-matched to environmental factors.
- Conflicting declared quantities are retained and warned about rather than silently resolved.
- The v0.4 IFC path is **not connected to the LCA/GWP calculation path**.
- No code-compliance, engineering, architectural, procurement, LCA, regulatory, or certification conclusion is produced by the IFC extractor.

Key files:

- `CONSTITUTION.md`: evidence, safety, authority, privacy, interoperability, and truth-before-promotion invariants.
- `ARCHITECTURE.md`: ProofGrid/RX Evidence Fabric architecture and evidence gates.
- `specs/rxep/`: RX Evidence Protocol specification and evidence-envelope schema.
- `schemas/building.schema.json`: canonical project/building fixture schema.
- `schemas/materials.schema.json`: material quantities with exact environmental source-record references.
- `schemas/lca-source-records.schema.json`: environmental-source registry schema.
- `schemas/ifc-extraction.schema.json`: v0.4 IFC declared-data extraction schema.
- `reference/rx_cli.py`: deterministic environmental verifier, registry validator, and structural IFC inspection CLI.
- `reference/ifc_extract.py`: v0.4 declared IFC quantity/material extraction CLI.
- `adapters/ifc/`: structural inspection and declared-data extraction adapters.
- `adapters/lca/`: environmental-source provenance rules and future connector boundary.
- `evidence/examples/`: fictional test fixtures and hashed synthetic source content.
- `tests/`: fail-closed provenance, schema, determinism, real IFC, and IFC conformance tests.

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

ProofGrid v0.4 is a **reference implementation under evidence-gated development**. The environmental-source registry path has an exact-head hosted v0.3 receipt, and the v0.4 branch adds IFC-declared quantity/material/unit/hierarchy extraction behind a separate conformance schema and test suite. Automatic IFC→environmental-source mapping, unit conversion, geometry-derived takeoff, production EPD/database ingestion, professional code/compliance conclusions, independent domain reproduction, and production deployment remain separate future gates.
