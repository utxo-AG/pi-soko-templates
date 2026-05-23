import json
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from typing import Any, Dict, List

from util.env import require_env


def fetch_ready_tasks() -> List[Dict[str, Any]]:
    """Fetch ready tasks using env config."""
    base_url = require_env("PREPROD_BASE_URL")
    agent_id = require_env("COWORKER_ID")
    coworker_api_key = require_env("SOKOSUMI_COWORKER_API_KEY")

    url = f"{base_url.rstrip('/')}/tasks"
    query = urllib.parse.urlencode({"status": "READY", "agent_id": agent_id})
    full_url = f"{url}?{query}"

    req = urllib.request.Request(
        full_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {coworker_api_key}",
            "x-api-key": coworker_api_key,
        },
        method="GET",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        if not body.strip():
            return []
        payload = json.loads(body)
        return payload.get("data", [])


def _post_task_event(
    task_id: str,
    event_type: str,
    extra_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if not task_id or not task_id.strip():
        raise ValueError("task_id is required")

    base_url = require_env("PREPROD_BASE_URL")
    coworker_api_key = require_env("SOKOSUMI_COWORKER_API_KEY")

    payload: Dict[str, Any] = {"status": event_type}

    if extra_payload:
        payload.update(extra_payload)

    url = f"{base_url.rstrip('/')}/tasks/{task_id}/events"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {coworker_api_key}",
            "x-api-key": coworker_api_key,
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Task event POST failed ({exc.code}): {error_body}") from exc


def post_task_running_event(task_id: str) -> Dict[str, Any]:
    """Post a RUNNING event for the task."""
    return _post_task_event(task_id, "RUNNING")


def post_task_completed_event(task_id: str, comment: str) -> Dict[str, Any]:
    """Post a COMPLETED event with the agent response as the comment."""
    return _post_task_event(task_id, "COMPLETED", extra_payload={"comment": comment})
