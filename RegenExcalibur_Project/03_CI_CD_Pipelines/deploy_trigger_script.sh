#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="dev"
RESOURCE_PREFIX="regenexcalibur"

usage() {
  cat <<'USAGE'
Usage: deploy_trigger_script.sh --project-id PROJECT_ID [--region REGION] [--environment ENV] [--resource-prefix PREFIX]

Submits the repository root to GCP Cloud Build using cloudbuild.yaml.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id) PROJECT_ID="${2:-}"; shift 2 ;;
    --region) REGION="${2:-}"; shift 2 ;;
    --environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --resource-prefix) RESOURCE_PREFIX="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  echo "Missing required --project-id." >&2
  usage
  exit 2
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Required tool not found: gcloud" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

gcloud builds submit "$PROJECT_ROOT" \
  --project "$PROJECT_ID" \
  --config "$SCRIPT_DIR/cloudbuild.yaml" \
  --substitutions "_REGION=$REGION,_ENVIRONMENT=$ENVIRONMENT,_RESOURCE_PREFIX=$RESOURCE_PREFIX"
