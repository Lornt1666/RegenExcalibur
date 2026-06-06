#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="dev"
APPLY="false"

usage() {
  cat <<'USAGE'
Usage: deploy_infra.sh --project-id PROJECT_ID [--region REGION] [--environment ENV] [--apply]

Runs Terraform init and plan. Add --apply to provision resources.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id) PROJECT_ID="${2:-}"; shift 2 ;;
    --region) REGION="${2:-}"; shift 2 ;;
    --environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --apply) APPLY="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  echo "Missing required --project-id." >&2
  usage
  exit 2
fi

for tool in gcloud terraform; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Required tool not found: $tool" >&2
    exit 1
  fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(cd "$SCRIPT_DIR/../Terraform" && pwd)"

echo "Enabling required APIs for $PROJECT_ID."
gcloud services enable \
  serviceusage.googleapis.com \
  iam.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  eventarc.googleapis.com \
  aiplatform.googleapis.com \
  --project "$PROJECT_ID"

cd "$TERRAFORM_DIR"
terraform init
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=$ENVIRONMENT" \
  -out=tfplan

if [[ "$APPLY" == "true" ]]; then
  echo "Applying Terraform plan."
  terraform apply tfplan
else
  echo "Dry run complete. Re-run with --apply to provision resources."
fi
