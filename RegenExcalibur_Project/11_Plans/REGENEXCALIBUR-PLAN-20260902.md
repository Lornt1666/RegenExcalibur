# RegenExcalibur Live Plan
**ID:** RX-PLAN-20260902  
**Owner:** Justice Gray Maciocha / Lornt1666  
**System:** RegenExcalibur GCP autonomous deploy + MRV orchestrator  
**Property:** No billable GCP resource is created unless an operator supplies a real project ID and types `--apply` after a passing dry-run.  
**Status this turn:** PLAN LIVE ON GITHUB. GCP APPLY HELD.

## Execution receipt (this environment, 2026-09-02T05:07:51Z)

| Field | Value |
|---|---|
| Entrypoint | `RegenExcalibur_Project/master_autonomous_execution_script.py` |
| Project | `demo-not-real` (dry-run only; not a live GCP project) |
| Region | `us-central1` |
| Environment | `dev` |
| Prefix | `regenexcalibur` |
| apply | false |
| python | present |
| gcloud | MISSING |
| terraform | MISSING |
| docker | MISSING |
| Orchestrator | six agents completed: Sensor → Forecast → FacadePanel → CaptureDevice → HumanReview → Governance |
| Workflow | `regenexcalibur_mrv_cycle` |
| HumanReview | `pending` (correct: a person is still the gate) |

`--apply` was refused. Missing tools would raise `RuntimeError` in apply mode. No live project ID was provided.

## Architecture (do not invent a second path)

```
operator
  → master_autonomous_execution_script.py
      → preflight (python, gcloud, terraform [, docker])
      → gcloud services enable  [13 APIs]
      → terraform init / plan / apply
      → gcloud functions deploy regenexcalibur-event-ingest
      → docker build+push + gcloud run deploy regenexcalibur-api
      → gcloud builds submit (cloudbuild.yaml)
      → gcloud monitoring dashboards create
      → multi_agent_orchestrator.py --dry-run
      → deployment_logs/latest_execution_summary.json
```

MRV agents stay in `agent_definitions.yaml`. NEXUS-PRIME is a sidecar compile card, not an MRV agent.

Network class: **Internet + WWW origin** (GCP APIs, Cloud Run URL, HTTPS). Tor is out of scope unless a later property names unlinkability.

## Holds

- AUTHORITY_HOLD: no GCP project ID from the operator
- TOOL_HOLD: gcloud, terraform, docker absent in this runtime
- BILLING_HOLD: apply creates billable resources
- SEAL_HOLD: software does not claim production certification; GovernanceAgent "SOC2/ISO27001/GDPR" in dry-run is a *prepared* record, not an audit opinion

## Live GCP go path (operator workstation only)

Preflight on a machine that has tools and billing:

```bash
gcloud auth login
gcloud config set project YOUR_REAL_PROJECT_ID
gcloud billing projects describe YOUR_REAL_PROJECT_ID
python3 RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_REAL_PROJECT_ID \
  --region us-central1 \
  --environment dev
# review deployment_logs/latest_execution_summary.json and Terraform plan text
python3 RegenExcalibur_Project/master_autonomous_execution_script.py \
  --project-id YOUR_REAL_PROJECT_ID \
  --region us-central1 \
  --environment dev \
  --apply
```

Verify from `10_Runbooks_and_Operational_Guides/deployment_runbook.md`: Terraform outputs, Cloud Run `/healthz`, Pub/Sub test publish, function logs, orchestrator dry-run stored.

Rollback: prior Cloud Build revision; do not destroy state until retention is satisfied.

## Coordination packet (standing)

1. System: RegenExcalibur deploy+MRV on GCP.
2. Property: dry-run default; apply is a person.
3. Boundary: repo `Lornt1666/RegenExcalibur`; GCP project named by operator; AutoHouse stamps stay out.
4. Assumptions: scaffold is initial; IAM and secrets need project-specific review before apply.
5. Architecture: as above.
6. First-break contracts: `--project-id`, service accounts, Pub/Sub topic names, Cloud Run unauthenticated flag.
7. Holds: listed.
8. Evidence: summary JSON `apply=false` plus six completed agents.
9. Next: operator project ID + workstation apply, or keep iterating the Gemini kernel.

## What "live" means this turn

- Live **plan** and **Gemini kernel** published to GitHub.
- Live **orchestrator** cycle executed locally (six agents).
- Live **GCP estate** not created. That is the correct high-class outcome.
