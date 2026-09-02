#!/usr/bin/env bash
set -euo pipefail
PROJECT="${1:-demo-not-real}"
REGION="${2:-us-central1}"
HERE="$(cd "$(dirname "$0")/../../../.." && pwd)"
SCRIPT="$HERE/master_autonomous_execution_script.py"
[[ -f "$SCRIPT" ]] || { echo "missing $SCRIPT" >&2; exit 2; }
python3 "$SCRIPT" --project-id "$PROJECT" --region "$REGION"
python3 -m json.tool "$HERE/deployment_logs/latest_execution_summary.json"
