# RegenExcalibur

## ProofGrid / RX Evidence Fabric

RegenExcalibur's current flagship reference implementation is **ProofGrid**: a cloud-neutral, machine-verifiable evidence kernel for built-environment data. It is designed to keep claims, calculations, review states, provenance, integrity, environmental-source boundaries, and certification boundaries explicit.

### ProofGrid v0.3 quick start

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

Inspect a real IFC STEP file through the read-only IfcOpenShell adapter:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

ProofGrid v0.3 validates canonical project/material/environmental-source inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` receipt. Environmental quantities reference exact source-record IDs rather than embedding free-floating GWP factors. Source-content SHA-256, exact unit matching, material identity, lifecycle/system boundary compatibility, and source-record digests are checked before the deterministic calculation proceeds.

`VERIFIABLE` is **not** `CERTIFIED`. Source integrity is not scientific validation. IFC ingestion remains structural only and does not establish quantity takeoff, LCA, code compliance, engineering adequacy, or professional certification.

Key files:

- `CONSTITUTION.md`: evidence, safety, authority, privacy, interoperability, and truth-before-promotion invariants.
- `ARCHITECTURE.md`: ProofGrid/RX Evidence Fabric architecture and evidence gates.
- `specs/rxep/`: RX Evidence Protocol specification and evidence-envelope schema.
- `schemas/building.schema.json`: canonical project/building fixture schema.
- `schemas/materials.schema.json`: v0.3 material quantities with exact source-record references.
- `schemas/lca-source-records.schema.json`: v0.3 environmental-source registry schema.
- `reference/rx_cli.py`: deterministic verifier, registry validator, and IFC inspection CLI.
- `adapters/ifc/`: read-only IFC ingestion adapter.
- `adapters/lca/`: environmental-source provenance rules and future connector boundary.
- `evidence/examples/`: fictional test fixtures and hashed synthetic source content.
- `tests/`: fail-closed provenance, schema, determinism, and IFC tests.

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

ProofGrid v0.3 is a **reference implementation under evidence-gated development**. Runtime Draft 2020-12 schema validation, deterministic evidence generation, source-content hashing, exact environmental source-record resolution, no-implicit-conversion policy, lifecycle-boundary compatibility checks, and read-only real IFC ingestion are implemented on the stacked v0.3 development branch. Production EPD/database ingestion, IFC quantity/material extraction, professional code/compliance conclusions, independent domain reproduction, and production deployment remain separate future gates.
