# Incident Response Runbook

## Severity Levels

- SEV1: Production outage, data exposure, or unauthorized access.
- SEV2: Major degradation, broken deployment, or failed governance workflow.
- SEV3: Partial workflow issue, delayed processing, or non-critical alert.

## First Response

1. Assign an incident owner.
2. Capture alert details, deployment logs, and recent Cloud Logging entries.
3. Freeze risky deployment activity until the owner approves.
4. Check Cloud Run health, Cloud Function errors, Pub/Sub backlog, and IAM changes.

## Evidence Collection

- `deployment_logs/` from the master script.
- Cloud Build execution history.
- Cloud Logging entries for Cloud Run and Cloud Functions.
- Terraform plan and state metadata.
- MRV audit records emitted by GovernanceAgent.

## Containment

- Disable external traffic only if necessary.
- Revoke suspicious credentials.
- Pause Pub/Sub consumers if they amplify the issue.
- Roll back to a known-good Cloud Run revision when appropriate.

## Recovery

1. Apply the smallest corrective change.
2. Validate health checks.
3. Confirm alerts return to normal.
4. Resume workflow processing.
5. Write a post-incident report.

## Post-Incident Review

Document root cause, blast radius, timeline, detection gaps, and follow-up actions. Map actions to SOC2, ISO27001, and GDPR controls when relevant.
