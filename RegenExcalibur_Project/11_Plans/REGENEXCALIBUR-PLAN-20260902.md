# RegenExcalibur Live Plan
**ID:** RX-PLAN-20260902  
**Owner:** Justice Gray Maciocha / Lornt1666  
**Seat of operations:** Edmonton, Alberta, Canada  
**Governing law:** laws of the Province of Alberta and the applicable laws of Canada  
**Forum:** courts of Alberta (Court of King's Bench of Alberta; Court of Appeal of Alberta), preferably sitting in Edmonton  
**Time standard:** America/Edmonton  
**System:** RegenExcalibur GCP autonomous deploy + MRV orchestrator  
**Property:** No billable GCP resource is created unless an Alberta-resident operator supplies a real project ID and types `--apply` after a passing dry-run. Personal information, if any, is handled under Alberta private-sector privacy law, not under a foreign default.  
**Status this turn:** PLAN LIVE ON GITHUB. GCP APPLY HELD. ALBERTA-GOVERNED.

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

## Alberta governance (explicit)

This plan, the coordination packet, the Gemini Plan Officer kernel, agent outputs, and any vendor brief issued under them are **governed by the laws of Alberta and the applicable laws of Canada**. They are not governed by California, Delaware, Iowa, or “wherever the model is hosted.”

| Layer | Rule |
|---|---|
| Seat | Edmonton, Alberta. Operator is ordinarily in Alberta. |
| Clock | America/Edmonton. Logs may be UTC; operator decisions use Alberta local time. |
| Governing law | Alberta law + applicable federal Canadian law. |
| Forum | Alberta courts. No silent shift to a foreign exclusive forum. |
| Language | Canadian English. |
| Privacy (private-sector personal information) | Alberta *Personal Information Protection Act* (PIPA). Consent and a reasonable purpose are required except where PIPA allows otherwise. Safeguard against loss and unauthorized access. Breach notice if there is a real risk of significant harm. Complaints: Office of the Information and Privacy Commissioner of Alberta. |
| Federal overlay | PIPEDA may also apply to federal works or interprovincial commercial activity. Name the statute; do not pick one and hide the other. |
| Public-sector / health | If a public body or health information appears, stop and load the correct Alberta statute (public-sector privacy / access regime, or *Health Information Act*). Do not treat PIPA as universal. |
| Professional authority | This software does not create an APEGA stamp, an Alberta Building Code approval, an AHJ permit, or an OIPC certification. AutoHouse / Part 9 remains a separate Alberta construction system. |
| Cloud location | Default Terraform region `us-central1` is **not** Alberta and **not** Canadian residency. Hosting in Iowa does not move governing law to Iowa. It does create a **DATA_RESIDENCY_HOLD** until the operator accepts cross-border processing or names a Canadian region. |
| Provider contracts | Google Cloud terms still bind the GCP account. Alberta governance binds the *operator plan and work product*. Conflict: name it; do not pretend one swallows the other. |
| Agents | Grok, Gemini, and other models are tools. They do not choose a foreign governing law. HumanReview stays with the Alberta operator. |

PIPA is the named private-sector privacy statute. This clause is an operating rule. It is not a legal opinion and not a claim that the scaffold is PIPA-certified.

## Holds

- AUTHORITY_HOLD: no GCP project ID from the operator
- TOOL_HOLD: gcloud, terraform, docker absent in this runtime
- BILLING_HOLD: apply creates billable resources
- SEAL_HOLD: software does not claim production certification; GovernanceAgent "SOC2/ISO27001/GDPR" in dry-run is a *prepared* record, not an audit opinion
- JURISDICTION: Alberta + Canada. Do not retitle the plan under a foreign law.
- DATA_RESIDENCY_HOLD: `us-central1` is outside Canada. Lift only by operator acceptance or a Canadian region choice
- PRIVACY_HOLD: no personal information into Pub/Sub, logs, GCS, or model context until a PIPA purpose and safeguard note exists

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
3. Boundary: repo `Lornt1666/RegenExcalibur`; seat Edmonton, Alberta; GCP project named by operator; AutoHouse stamps stay out; governing law Alberta + Canada.
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
