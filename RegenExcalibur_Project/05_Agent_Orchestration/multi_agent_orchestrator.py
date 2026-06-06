#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


LOGGER = logging.getLogger("regenexcalibur.orchestrator")


@dataclass
class AgentResult:
    agent: str
    action: str
    status: str
    output: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_definitions(path: Path) -> dict[str, Any]:
    if yaml is None:
        logging.warning("PyYAML is not installed. Using the built-in limited workflow parser.")
        return load_definitions_without_yaml(path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_definitions_without_yaml(path: Path) -> dict[str, Any]:
    workflow_name = "regenexcalibur_mrv_cycle"
    steps: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_workflow = False
    in_steps = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("workflow_name:"):
            workflow_name = stripped.split(":", 1)[1].strip()
            continue
        if stripped == "workflow:":
            in_workflow = True
            continue
        if in_workflow and stripped == "steps:":
            in_steps = True
            continue
        if in_workflow and in_steps and stripped.startswith("- agent:"):
            current = {"agent": stripped.split(":", 1)[1].strip()}
            steps.append(current)
            continue
        if in_workflow and in_steps and stripped.startswith("action:") and current is not None:
            current["action"] = stripped.split(":", 1)[1].strip()
            continue
        if in_workflow and raw_line and not raw_line.startswith(" "):
            break

    if not steps:
        raise RuntimeError(f"No workflow steps found in {path}")

    return {"workflow_name": workflow_name, "workflow": {"steps": steps}}


def execute_agent(agent_name: str, action: str, prior_results: list[AgentResult], dry_run: bool) -> AgentResult:
    context = {
        "prior_result_count": len(prior_results),
        "dry_run": dry_run,
        "generated_at": utc_now(),
    }

    if agent_name == "SensorAgent":
        output = {"normalized_signal": {"source_id": "demo-sensor", "quality": "validated", **context}}
    elif agent_name == "ForecastAgent":
        output = {"forecast_summary": "stable", "confidence_score": 0.82, **context}
    elif agent_name == "FacadePanelAgent":
        output = {"panel_action_plan": ["inspect-panel-a", "queue-maintenance-review"], **context}
    elif agent_name == "CaptureDeviceAgent":
        output = {"capture_manifest": {"mode": "privacy_preserving", "frames": 12}, **context}
    elif agent_name == "HumanReviewAgent":
        output = {"review_decision": "pending" if dry_run else "recorded", **context}
    elif agent_name == "GovernanceAgent":
        output = {"mrv_audit_record": {"status": "prepared", "controls": ["SOC2", "ISO27001", "GDPR"]}, **context}
    else:
        output = {"message": f"No specialized handler for {agent_name}", **context}

    LOGGER.info("Agent %s completed action %s", agent_name, action)
    return AgentResult(agent=agent_name, action=action, status="completed", output=output)


def run_workflow(definitions: dict[str, Any], dry_run: bool) -> list[AgentResult]:
    results: list[AgentResult] = []
    steps = definitions.get("workflow", {}).get("steps", [])
    for step in steps:
        result = execute_agent(step["agent"], step["action"], results, dry_run)
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the RegenExcalibur multi-agent orchestration workflow.")
    parser.add_argument("--definitions", default=str(Path(__file__).with_name("agent_definitions.yaml")))
    parser.add_argument("--dry-run", action="store_true", help="Run without publishing or mutating external systems.")
    parser.add_argument("--output", default="", help="Optional path for a JSON workflow result.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    definitions = load_definitions(Path(args.definitions))
    results = run_workflow(definitions, dry_run=args.dry_run)
    payload = {
        "workflow": definitions.get("workflow_name", "regenexcalibur_mrv_cycle"),
        "dry_run": args.dry_run,
        "completed_at": utc_now(),
        "results": [result.__dict__ for result in results],
    }

    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        LOGGER.info("Wrote workflow result to %s", output_path)
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
