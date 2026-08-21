# RegenExcalibur

## ProofGrid / RX Evidence Fabric v0.1

RegenExcalibur is now developing **ProofGrid**, an open, local-first reference implementation for turning built-environment data into traceable, machine-readable evidence.

The genesis slice deliberately stays narrow:

```text
project + declared materials
        ↓
deterministic calculation
        ↓
RX Evidence Envelope
        ↓
knowledge-graph artifact + integrity receipt
```

Run the fictional Alberta fixture locally with no cloud account or paid service:

```bash
python reference/rx_cli.py verify evidence/examples/alberta-house
```

Expected semantic result:

```text
RESULT: VERIFIABLE
NOT CERTIFIED
```

The sample material factors are fictional and must not be used for real environmental, engineering, permitting, procurement, LCA, audit, or certification claims.

Key ProofGrid artifacts:

- [CONSTITUTION.md](CONSTITUTION.md): evidence, safety, authority, privacy, interoperability, and truth-before-promotion rules.
- [ARCHITECTURE.md](ARCHITECTURE.md): genesis architecture and acceptance criteria.
- [specs/rxep/README.md](specs/rxep/README.md): RX Evidence Protocol v0.1.
- [specs/rxep/evidence-envelope.schema.json](specs/rxep/evidence-envelope.schema.json): machine-readable evidence-envelope schema.
- [reference/rx_cli.py](reference/rx_cli.py): standard-library reference verifier.
- [tests/test_rx_cli.py](tests/test_rx_cli.py): deterministic and fail-closed tests.

---

## Freelance / Contract Work — 1JGM

**Justice Gray Maciocha — 1JGM, Blueprint-to-Bot Systems Operator** is accepting remote, asynchronous, deliverable-based freelance work in market and competitor research, spreadsheet/listing QA, AI evaluation, prompt and workflow design, technical documentation, automation specifications, project operations, construction technology, and construction-informed CAD/visualization support.

- **Full capability and service profile:** [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md)
- **Work contact:** `justlornt95+redditwork@gmail.com`
- **Location/time zone:** Alberta, Canada — Mountain Time
- **Engagement model:** Evening/weekend asynchronous work, small paid trials, hourly or fixed-price milestones

The service profile separates demonstrated capability from learnable adjacent work and does not claim professional licensure, universal expertise, production deployment, or independent certification without supporting evidence.

---

The legacy RegenExcalibur cloud scaffold is a GCP-oriented autonomous deployment and orchestration package. It coordinates infrastructure-as-code, Cloud Run, Cloud Functions, Pub/Sub, Vertex AI pipeline scaffolding, multi-agent MRV workflows, security controls, observability, and operational runbooks.

## Repository Description

RegenExcalibur combines a cloud-neutral ProofGrid evidence kernel with a GCP deployment/orchestration scaffold for automation, MRV, compliance, observability, and AI-agent workflows.

Suggested GitHub topics:

```text
clean-tech, evidence, provenance, digital-twin, construction-tech, gcp, terraform, cloud-run, pubsub, automation, mrv, compliance, observability, ai-agents
```

## Contents

- [CONSTITUTION.md](CONSTITUTION.md): RegenExcalibur evidence and safety constitution.
- [ARCHITECTURE.md](ARCHITECTURE.md): ProofGrid genesis architecture.
- [specs/rxep](specs/rxep): RX Evidence Protocol specification and schema.
- [reference/rx_cli.py](reference/rx_cli.py): local ProofGrid reference verifier.
- [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md): public 1JGM freelance capability, service, evidence, rate, and engagement profile.
- [RegenExcalibur_Project.zip](RegenExcalibur_Project.zip): packaged project archive.
- [RegenExcalibur_Project](RegenExcalibur_Project): expanded GCP project source and deployment scaffold.
- [RegenExcalibur_Project/01_Documentation_and_Readme/README.md](RegenExcalibur_Project/01_Documentation_and_Readme/README.md): detailed cloud operational instructions.
- [RegenExcalibur_Project/master_autonomous_execution_script.py](RegenExcalibur_Project/master_autonomous_execution_script.py): dry-run-first deployment entry point.

## Safety Notice

ProofGrid v0.1 is a reference implementation and does not provide professional certification. The included Alberta house fixture and material factors are fictional demonstration data.

The cloud deployment automation defaults to dry-run mode. Live provisioning requires the explicit `--apply` flag and can create billable GCP resources. Review Terraform, IAM, Cloud Build, and runtime configuration before applying.

## ProofGrid Quick Start

```bash
python -m unittest discover -s tests -v
python reference/rx_cli.py verify evidence/examples/alberta-house
```

## Legacy Cloud Quick Start

```bash
python RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_PROJECT_ID \
  --region us-central1
```

To deploy after reviewing the dry run:

```bash
python RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_PROJECT_ID \
  --region us-central1 \
  --apply
```

## Architecture

RegenExcalibur now separates:

- a local-first ProofGrid/RXEP evidence kernel;
- open adapter contracts for future IFC and LCA/EPD integration;
- evidence/provenance and knowledge-graph artifacts;
- Terraform-managed GCP foundations;
- Cloud Run API services;
- Cloud Functions event ingestion;
- Pub/Sub task and MRV event streams;
- Cloud Storage artifact retention;
- Artifact Registry container storage;
- Vertex AI pipeline scaffolding;
- multi-agent workflow execution;
- security and compliance policy documents;
- monitoring, alerting, deployment, incident-response, and scaling runbooks.

## Status

ProofGrid v0.1 is a tested genesis reference slice using fictional data. The IFC and LCA/EPD adapters are declared but not yet implemented. The legacy cloud package remains an initial generated scaffold intended for local review, dry-run validation, and controlled deployment after project-specific configuration.
