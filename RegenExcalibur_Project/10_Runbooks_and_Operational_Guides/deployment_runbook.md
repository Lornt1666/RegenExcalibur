# Deployment Runbook

## Purpose

Deploy RegenExcalibur infrastructure, backend services, orchestration logic, and monitoring controls into a target GCP project.

## Preflight

1. Confirm billing is enabled on the target project.
2. Confirm `gcloud`, `terraform`, `python`, and optionally `docker` are installed.
3. Authenticate with GCP.
4. Run the master script without `--apply`.
5. Review the deployment log and Terraform plan.

## Deployment

```bash
python master_autonomous_execution_script.py --project-id YOUR_PROJECT_ID --region us-central1 --environment prod --apply
```

## Verification

1. Confirm Terraform outputs include bucket, Pub/Sub topics, service accounts, and repository.
2. Confirm Cloud Run service responds to `/healthz`.
3. Publish a test message to the agent task Pub/Sub topic.
4. Review Cloud Function logs.
5. Run the orchestrator in dry-run mode and store the result.

```bash
python 05_Agent_Orchestration/multi_agent_orchestrator.py --dry-run --output deployment_logs/orchestrator_test.json
```

## Rollback

1. Revert source changes.
2. Re-run Cloud Build from the prior known-good revision.
3. Review Terraform state before changing infrastructure.
4. Avoid destructive cleanup until audit and data retention requirements are satisfied.
