# RegenExcalibur Project

RegenExcalibur is a cloud-native automation scaffold for provisioning, deploying, orchestrating, and operating a GCP-based AI/video/agent ecosystem. The project is packaged so it can be unzipped into a secure terminal, configured with a GCP project, and run through a single audited entry point.

## What Is Included

- Terraform for foundational GCP infrastructure.
- Bash and PowerShell deployment helpers.
- Cloud Build pipeline for CI/CD deployment.
- Cloud Function and Cloud Run service skeletons.
- Multi-agent orchestration logic for SensorAgent, ForecastAgent, FacadePanelAgent, CaptureDeviceAgent, HumanReviewAgent, GovernanceAgent.
- Vertex AI and FFmpeg pipeline scaffolding.
- IAM, security, monitoring, alerting, and operational runbooks.

## Safety Model

The master script defaults to dry-run mode. It prints and logs the actions it would take without mutating cloud resources. To perform live deployment, pass `--apply`.

Live deployment can create billable GCP resources. Review all Terraform, IAM, and Cloud Build files before running with `--apply`.

## Prerequisites

- Python 3.10 or newer.
- Google Cloud SDK authenticated to the target project.
- Terraform 1.6 or newer.
- Docker, if deploying Cloud Run locally or building container images.
- FFmpeg, if running local video rendering scripts.
- A GCP project with billing enabled.

Recommended authentication:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## Quick Start

From the unzipped project root:

```bash
python master_autonomous_execution_script.py --project-id YOUR_PROJECT_ID --region us-central1
```

This performs preflight checks and shows the planned deployment actions.

To deploy:

```bash
python master_autonomous_execution_script.py --project-id YOUR_PROJECT_ID --region us-central1 --apply
```

Optional flags:

```bash
python master_autonomous_execution_script.py \
  --project-id YOUR_PROJECT_ID \
  --region us-central1 \
  --environment prod \
  --apply \
  --skip-cloud-build
```

## Manual Infrastructure Deployment

Bash:

```bash
cd 02_Infrastructure_as_Code/IaC_Scripts
./deploy_infra.sh --project-id YOUR_PROJECT_ID --region us-central1 --apply
```

PowerShell:

```powershell
cd 02_Infrastructure_as_Code/IaC_Scripts
.\deploy_infra.ps1 -ProjectId YOUR_PROJECT_ID -Region us-central1 -Apply
```

## Cloud Build Deployment

```bash
cd 03_CI_CD_Pipelines
./deploy_trigger_script.sh --project-id YOUR_PROJECT_ID --region us-central1
```

## Configuration Notes

- Terraform variables are defined in `02_Infrastructure_as_Code/Terraform/variables.tf`.
- Runtime secrets should be stored in GCP Secret Manager after Terraform creates the secret placeholders.
- The Cloud Run service exposes `/healthz`, `/tasks`, and `/render`.
- The Cloud Function consumes Pub/Sub events and writes structured logs.
- The orchestrator can run locally in dry-run mode:

```bash
python 05_Agent_Orchestration/multi_agent_orchestrator.py --dry-run
```

## Logs

The master script writes deployment logs under:

```text
deployment_logs/
```

Keep these logs for audit review and incident investigations.

## Recommended First Deployment Sequence

1. Run the master script without `--apply`.
2. Review the generated log and Terraform plan.
3. Confirm the target project, region, and service account permissions.
4. Run with `--apply`.
5. Verify `/healthz` on the Cloud Run service.
6. Send a test Pub/Sub event to the agent task topic.
7. Review Cloud Logging and Monitoring alerts.

## Cleanup

No destructive cleanup is automated. To remove resources, inspect Terraform state and run a controlled Terraform destroy from the Terraform directory:

```bash
terraform plan -destroy
terraform destroy
```

Only run cleanup after confirming backups, audit requirements, and retention policies.
