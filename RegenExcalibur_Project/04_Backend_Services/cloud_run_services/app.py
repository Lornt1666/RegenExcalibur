import json
import os
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request


app = Flask(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def response(payload: dict[str, Any], status: int = 200):
    return jsonify(payload), status


@app.get("/")
def index():
    return response(
        {
            "service": "regenexcalibur-api",
            "environment": os.environ.get("ENVIRONMENT", "dev"),
            "status": "ready",
            "time": utc_now(),
        }
    )


@app.get("/healthz")
def healthz():
    return response({"ok": True, "time": utc_now()})


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    task = {
        "accepted": True,
        "task_id": payload.get("task_id", f"task-{int(datetime.now().timestamp())}"),
        "received_at": utc_now(),
        "next": "publish-to-pubsub-or-run-orchestrator",
    }
    return response(task, 202)


@app.post("/render")
def render_request():
    payload = request.get_json(silent=True) or {}
    render_plan = {
        "accepted": True,
        "render_id": payload.get("render_id", f"render-{int(datetime.now().timestamp())}"),
        "mode": payload.get("mode", "storyboard"),
        "received_at": utc_now(),
    }
    return response(render_plan, 202)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
