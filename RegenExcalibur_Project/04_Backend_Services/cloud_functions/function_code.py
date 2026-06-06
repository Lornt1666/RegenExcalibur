import base64
import json
import logging
import os
from datetime import datetime, timezone

import functions_framework


LOGGER = logging.getLogger("regenexcalibur.cloud_function")
LOGGER.setLevel(logging.INFO)


def _decode_message(event_data):
    message = event_data.get("message", {})
    payload = message.get("data")
    if not payload:
        return {}
    decoded = base64.b64decode(payload).decode("utf-8")
    return json.loads(decoded)


@functions_framework.cloud_event
def ingest_event(cloud_event):
    """Ingests Pub/Sub events for RegenExcalibur agent tasks."""
    environment = os.environ.get("ENVIRONMENT", "dev")
    mrv_topic = os.environ.get("MRV_TOPIC", "regenexcalibur-mrv-events")

    try:
        payload = _decode_message(cloud_event.data or {})
    except Exception as exc:
        LOGGER.exception("Failed to decode Pub/Sub message")
        raise exc

    audit_event = {
        "environment": environment,
        "mrv_topic": mrv_topic,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": "cloud_function.ingest_event",
        "payload": payload,
    }

    LOGGER.info("RegenExcalibur task received: %s", json.dumps(audit_event, sort_keys=True))
    return None
