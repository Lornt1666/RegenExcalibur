#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_manifest(project_id: str, region: str, prompt: str, output_bucket: str) -> dict:
    return {
        "project_id": project_id,
        "region": region,
        "pipeline": "regenexcalibur-ai-video",
        "created_at": utc_now(),
        "prompt": prompt,
        "output_bucket": output_bucket,
        "stages": [
            {"name": "forecast_context", "service": "vertex-ai", "status": "planned"},
            {"name": "storyboard", "service": "vertex-ai", "status": "planned"},
            {"name": "render_manifest", "service": "cloud-storage", "status": "planned"},
            {"name": "ffmpeg_render", "service": "local-or-cloud-run", "status": "planned"},
        ],
    }


def run_gcloud_custom_job(project_id: str, region: str, manifest_path: Path) -> None:
    command = [
        "gcloud",
        "ai",
        "custom-jobs",
        "create",
        "--project",
        project_id,
        "--region",
        region,
        "--display-name",
        "regenexcalibur-ai-video-pipeline",
        "--worker-pool-spec",
        "machine-type=e2-standard-4,replica-count=1,container-image-uri=python:3.12-slim",
        "--args",
        f"manifest={manifest_path}",
    ]
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or launch a RegenExcalibur Vertex AI video pipeline manifest.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--output-bucket", required=True)
    parser.add_argument("--prompt", default="Generate a privacy-preserving RegenExcalibur operations render.")
    parser.add_argument("--manifest", default="ai_video_manifest.json")
    parser.add_argument("--apply", action="store_true", help="Create a Vertex AI custom job.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = build_manifest(args.project_id, args.region, args.prompt, args.output_bucket)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote manifest to {manifest_path}")

    if args.apply:
        run_gcloud_custom_job(args.project_id, args.region, manifest_path)
    else:
        print("Dry run complete. Add --apply to submit a Vertex AI custom job.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
