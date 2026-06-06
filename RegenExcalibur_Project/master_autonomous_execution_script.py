#!/usr/bin/env python3
import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "deployment_logs"
TERRAFORM_DIR = ROOT / "02_Infrastructure_as_Code" / "Terraform"
CLOUD_FUNCTION_DIR = ROOT / "04_Backend_Services" / "cloud_functions"
CLOUD_RUN_DIR = ROOT / "04_Backend_Services" / "cloud_run_services"
ORCHESTRATOR = ROOT / "05_Agent_Orchestration" / "multi_agent_orchestrator.py"
DASHBOARD_JSON = ROOT / "09_Observability" / "monitoring_dashboard.json"

REQUIRED_APIS = [
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "eventarc.googleapis.com",
    "aiplatform.googleapis.com",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Runner:
    def __init__(self, apply: bool):
        self.apply = apply

    def run(self, command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
        printable = " ".join(command)
        location = str(cwd or ROOT)
        logging.info("Command [%s]: %s", location, printable)

        if not self.apply:
            print(f"[dry-run] {printable}")
            return

        subprocess.run(command, cwd=str(cwd or ROOT), env=env, check=True)


def setup_logging() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("RegenExcalibur deployment log started at %s", utc_now())
    return log_path


def require_tool(name: str) -> bool:
    path = shutil.which(name)
    if path:
        logging.info("Found %s at %s", name, path)
        return True
    logging.warning("Tool not found: %s", name)
    return False


def preflight(args: argparse.Namespace) -> None:
    logging.info("Running preflight checks.")
    missing = [tool for tool in ["python", "gcloud", "terraform"] if not require_tool(tool)]
    if not args.skip_cloud_run:
        require_tool("docker")

    if missing and args.apply:
        raise RuntimeError(f"Missing required tools for apply mode: {', '.join(missing)}")

    if not args.project_id:
        raise RuntimeError("--project-id is required.")

    logging.info("Project: %s", args.project_id)
    logging.info("Region: %s", args.region)
    logging.info("Environment: %s", args.environment)
    logging.info("Apply mode: %s", args.apply)


def enable_apis(runner: Runner, project_id: str) -> None:
    runner.run(["gcloud", "services", "enable", *REQUIRED_APIS, "--project", project_id])


def run_terraform(runner: Runner, args: argparse.Namespace) -> None:
    runner.run(["terraform", "init", "-input=false"], cwd=TERRAFORM_DIR)
    runner.run(
        [
            "terraform",
            "plan",
            "-input=false",
            f"-var=project_id={args.project_id}",
            f"-var=region={args.region}",
            f"-var=environment={args.environment}",
            f"-var=resource_prefix={args.resource_prefix}",
            "-out=tfplan",
        ],
        cwd=TERRAFORM_DIR,
    )
    runner.run(["terraform", "apply", "-input=false", "tfplan"], cwd=TERRAFORM_DIR)


def terraform_output(name: str, fallback: str) -> str:
    try:
        completed = subprocess.run(
            ["terraform", "output", "-raw", name],
            cwd=str(TERRAFORM_DIR),
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or fallback
    except Exception:
        return fallback


def deploy_cloud_function(runner: Runner, args: argparse.Namespace) -> None:
    service_account = terraform_output(
        "function_service_account_email",
        f"{args.resource_prefix}-function@{args.project_id}.iam.gserviceaccount.com",
    )
    runner.run(
        [
            "gcloud",
            "functions",
            "deploy",
            f"{args.resource_prefix}-event-ingest",
            "--gen2",
            "--runtime=python312",
            f"--region={args.region}",
            f"--project={args.project_id}",
            f"--source={CLOUD_FUNCTION_DIR}",
            "--entry-point=ingest_event",
            f"--trigger-topic={args.resource_prefix}-agent-tasks",
            f"--service-account={service_account}",
            f"--set-env-vars=ENVIRONMENT={args.environment},MRV_TOPIC={args.resource_prefix}-mrv-events",
        ]
    )


def deploy_cloud_run(runner: Runner, args: argparse.Namespace) -> None:
    image = (
        f"{args.region}-docker.pkg.dev/{args.project_id}/"
        f"{args.resource_prefix}-containers/{args.resource_prefix}-api:local"
    )
    service_account = terraform_output(
        "runtime_service_account_email",
        f"{args.resource_prefix}-runtime@{args.project_id}.iam.gserviceaccount.com",
    )
    runner.run(["gcloud", "auth", "configure-docker", f"{args.region}-docker.pkg.dev", "--quiet"])
    runner.run(["docker", "build", "-t", image, "."], cwd=CLOUD_RUN_DIR)
    runner.run(["docker", "push", image])
    runner.run(
        [
            "gcloud",
            "run",
            "deploy",
            f"{args.resource_prefix}-api",
            f"--image={image}",
            f"--region={args.region}",
            f"--project={args.project_id}",
            "--platform=managed",
            "--allow-unauthenticated",
            f"--service-account={service_account}",
            f"--set-env-vars=ENVIRONMENT={args.environment}",
        ]
    )


def trigger_cloud_build(runner: Runner, args: argparse.Namespace) -> None:
    runner.run(
        [
            "gcloud",
            "builds",
            "submit",
            str(ROOT),
            f"--project={args.project_id}",
            f"--config={ROOT / '03_CI_CD_Pipelines' / 'cloudbuild.yaml'}",
            "--substitutions",
            f"_REGION={args.region},_ENVIRONMENT={args.environment},_RESOURCE_PREFIX={args.resource_prefix}",
        ]
    )


def apply_monitoring_dashboard(runner: Runner, args: argparse.Namespace) -> None:
    if not DASHBOARD_JSON.exists():
        logging.warning("Monitoring dashboard file not found: %s", DASHBOARD_JSON)
        return
    runner.run(
        [
            "gcloud",
            "monitoring",
            "dashboards",
            "create",
            f"--project={args.project_id}",
            f"--config-from-file={DASHBOARD_JSON}",
        ]
    )


def run_orchestrator(args: argparse.Namespace) -> None:
    output_path = LOG_DIR / "orchestrator_result.json"
    command = [
        sys.executable,
        str(ORCHESTRATOR),
        "--dry-run",
        "--output",
        str(output_path),
    ]
    logging.info("Running local orchestrator validation: %s", " ".join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        if args.apply:
            raise
        logging.warning("Orchestrator validation failed in dry-run mode: %s", exc)


def write_execution_summary(args: argparse.Namespace, log_path: Path) -> None:
    summary = {
        "project_id": args.project_id,
        "region": args.region,
        "environment": args.environment,
        "resource_prefix": args.resource_prefix,
        "apply": args.apply,
        "completed_at": utc_now(),
        "log_path": str(log_path),
    }
    summary_path = LOG_DIR / "latest_execution_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    logging.info("Wrote execution summary to %s", summary_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomous RegenExcalibur deployment entry point.")
    parser.add_argument("--project-id", required=True, help="Target GCP project ID.")
    parser.add_argument("--region", default="us-central1", help="Target GCP region.")
    parser.add_argument("--environment", default="dev", help="Deployment environment label.")
    parser.add_argument("--resource-prefix", default="regenexcalibur", help="Prefix for named resources.")
    parser.add_argument("--apply", action="store_true", help="Execute live provisioning and deployment commands.")
    parser.add_argument("--skip-cloud-run", action="store_true", help="Skip local Cloud Run image build and deploy.")
    parser.add_argument("--skip-cloud-function", action="store_true", help="Skip Cloud Function deployment.")
    parser.add_argument("--skip-cloud-build", action="store_true", help="Skip Cloud Build trigger.")
    parser.add_argument("--skip-monitoring", action="store_true", help="Skip monitoring dashboard creation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    log_path = setup_logging()
    runner = Runner(apply=args.apply)

    try:
        preflight(args)
        enable_apis(runner, args.project_id)
        run_terraform(runner, args)

        if not args.skip_cloud_function:
            deploy_cloud_function(runner, args)
        if not args.skip_cloud_run:
            deploy_cloud_run(runner, args)
        if not args.skip_cloud_build:
            trigger_cloud_build(runner, args)
        if not args.skip_monitoring:
            apply_monitoring_dashboard(runner, args)

        run_orchestrator(args)
        write_execution_summary(args, log_path)
        logging.info("RegenExcalibur execution completed.")
        return 0
    except Exception:
        logging.exception("RegenExcalibur execution failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
