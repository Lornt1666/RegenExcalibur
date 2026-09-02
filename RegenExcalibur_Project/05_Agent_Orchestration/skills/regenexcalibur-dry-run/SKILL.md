---
name: regenexcalibur-dry-run
description: Run the RegenExcalibur autonomous deploy and MRV orchestrator in dry-run, parse the execution summary, and refuse --apply unless the operator stated it and preflight tools exist. Use when the user says dry-run RegenExcalibur, deploy the scaffold, run the master script, check Terraform plan, or validate the agent cycle without provisioning GCP.
metadata:
  version: "1.0"
  type: workflow
  source_job: master_autonomous_execution_script.py
---

# RegenExcalibur dry-run

Execute the real entrypoint. Do not invent a second deploy path.

Repo: https://github.com/Lornt1666/RegenExcalibur  
Script: `RegenExcalibur_Project/master_autonomous_execution_script.py`  
Orchestrator: `RegenExcalibur_Project/05_Agent_Orchestration/multi_agent_orchestrator.py`

## Default action

1. Confirm the working tree contains `RegenExcalibur_Project/master_autonomous_execution_script.py`. If missing, clone the repo.
2. Require `--project-id`. If the user did not give one, use `demo-not-real` only for dry-run. Never use a guessed live project ID.
3. Run without `--apply` unless the user typed apply/provision/go-live in this turn.
4. Read `RegenExcalibur_Project/deployment_logs/latest_execution_summary.json`.
5. Report apply flag, project, region, environment, log path, and whether `gcloud` / `terraform` / `docker` were missing.
6. Run the orchestrator dry-run and confirm six agents completed.
7. Stop. Do not enable APIs, apply Terraform, or push images.

```bash
python3 RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id demo-not-real \
  --region us-central1
```

## Hard gates

- Default is dry-run. `--apply` is an explicit operator act.
- Refuse `--apply` if `gcloud` or `terraform` is missing.
- Do not commit credentials. Secrets go to Secret Manager by name only.
- Do not smash `agent_definitions.yaml` or insert NexusPrime into the MRV cycle.
- Deployment logs stay in `RegenExcalibur_Project/deployment_logs/`.

## Done-state

A dry-run is done when the summary JSON exists, `apply` is false, and the orchestrator wrote six completed agent results.
