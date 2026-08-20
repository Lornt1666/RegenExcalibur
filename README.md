# RegenExcalibur

## Freelance / Contract Work — 1JGM

**Justice Gray Maciocha — 1JGM, Blueprint-to-Bot Systems Operator** is accepting remote, asynchronous, deliverable-based freelance work in market and competitor research, spreadsheet/listing QA, AI evaluation, prompt and workflow design, technical documentation, automation specifications, project operations, construction technology, and construction-informed CAD/visualization support.

- **Full capability and service profile:** [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md)
- **Work contact:** `justlornt95+redditwork@gmail.com`
- **Location/time zone:** Alberta, Canada — Mountain Time
- **Engagement model:** Evening/weekend asynchronous work, small paid trials, hourly or fixed-price milestones

The service profile separates demonstrated capability from learnable adjacent work and does not claim professional licensure, universal expertise, production deployment, or independent certification without supporting evidence.

---

RegenExcalibur is a GCP-oriented autonomous deployment and orchestration scaffold packaged as both source files and a ready ZIP artifact. It coordinates infrastructure-as-code, Cloud Run, Cloud Functions, Pub/Sub, Vertex AI pipeline scaffolding, multi-agent MRV workflows, security controls, observability, and operational runbooks.

## Repository Description

Cloud-native RegenExcalibur automation package for secure GCP provisioning, Terraform IaC, CI/CD, AI/video pipeline scaffolding, multi-agent orchestration, compliance, observability, and runbook-driven operations.

Suggested GitHub topics:

```text
gcp, terraform, cloud-run, cloud-functions, pubsub, vertex-ai, cloud-build, automation, mrv, compliance, observability, ai-agents
```

## Contents

- [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md): public 1JGM freelance capability, service, evidence, rate, and engagement profile.
- [RegenExcalibur_Project.zip](RegenExcalibur_Project.zip): packaged project archive.
- [RegenExcalibur_Project](RegenExcalibur_Project): expanded project source and deployment scaffold.
- [RegenExcalibur_Project/01_Documentation_and_Readme/README.md](RegenExcalibur_Project/01_Documentation_and_Readme/README.md): detailed operational instructions.
- [RegenExcalibur_Project/master_autonomous_execution_script.py](RegenExcalibur_Project/master_autonomous_execution_script.py): dry-run-first deployment entry point.

## Safety Notice

The deployment automation defaults to dry-run mode. Live provisioning requires the explicit `--apply` flag and can create billable GCP resources. Review Terraform, IAM, Cloud Build, and runtime configuration before applying.

## Quick Start

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

RegenExcalibur coordinates:

- Terraform-managed GCP foundations.
- Cloud Run API service.
- Cloud Functions event ingestion.
- Pub/Sub task and MRV event streams.
- Cloud Storage artifact retention.
- Artifact Registry container storage.
- Vertex AI pipeline scaffolding.
- Multi-agent workflow execution.
- Security and compliance policy documents.
- Monitoring dashboard and alert policy definitions.
- Deployment, incident response, and scaling runbooks.

## Status

This repository contains an initial generated scaffold. It is ready for local review, dry-run validation, and controlled GCP deployment after project-specific configuration.
