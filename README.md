# RegenExcalibur

## ProofGrid / RX Evidence Fabric

RegenExcalibur's current flagship reference implementation is **ProofGrid**: a cloud-neutral, machine-verifiable evidence kernel for built-environment data. It is designed to keep claims, calculations, review states, provenance, integrity, and certification boundaries explicit.

### ProofGrid v0.2 quick start

Install the pinned open-source dependencies:

```bash
python -m pip install -r requirements-proofgrid.txt
```

Verify the fictional Alberta fixture:

```bash
python reference/rx_cli.py verify evidence/examples/alberta-house
```

Inspect a real IFC STEP file through the read-only IfcOpenShell adapter:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

ProofGrid v0.2 validates canonical project/material inputs and generated evidence with JSON Schema Draft 2020-12 before issuing a `VERIFIABLE` receipt. `VERIFIABLE` is **not** `CERTIFIED`. IFC ingestion is structural only and does not establish quantity takeoff, LCA, code compliance, engineering adequacy, or professional certification.

Key files:

- `CONSTITUTION.md`: evidence, safety, authority, privacy, interoperability, and truth-before-promotion invariants.
- `ARCHITECTURE.md`: ProofGrid/RX Evidence Fabric genesis architecture.
- `specs/rxep/`: RX Evidence Protocol specification and evidence-envelope schema.
- `schemas/`: canonical project and material schemas.
- `reference/rx_cli.py`: deterministic verifier and IFC inspection CLI.
- `adapters/ifc/`: read-only IFC ingestion adapter.
- `evidence/examples/`: fictional test fixtures.
- `tests/`: fail-closed conformance and determinism tests.

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

This is now treated as an **optional deployment/orchestration layer**, not the identity of the ProofGrid core.

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

ProofGrid v0.2 is a **reference implementation under evidence-gated development**. The JSON evidence kernel and hosted genesis CI are implemented; runtime Draft 2020-12 schema validation and read-only real IFC ingestion are now included on the active draft PR branch. Production LCA/EPD ingestion, professional code/compliance conclusions, independent domain validation, and production deployment remain separate future gates.
