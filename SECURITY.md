# Security Policy

## Deployment Safety

RegenExcalibur automation defaults to dry-run mode and requires explicit `--apply` before provisioning or deployment commands are executed.

## Secrets

Do not commit credentials, service account keys, API keys, or secret values. Store runtime secrets in GCP Secret Manager and reference them by name.

## Reporting Issues

For security-sensitive findings, avoid publishing exploitable details in public issues. Coordinate privately with the repository owner before disclosure.

## Operational Controls

- Review Terraform plans before apply.
- Use least-privilege service accounts.
- Keep deployment logs for audit review.
- Rotate credentials regularly.
- Review Cloud Logging, Cloud Monitoring, and MRV audit outputs after deployment.
