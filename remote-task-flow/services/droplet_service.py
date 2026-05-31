"""
Droplet provisioning service.

Handles creating and destroying DigitalOcean droplets that act as remote
task processors.  Each droplet receives the task payload via user-data on
boot and is expected to POST its result back to the callback server once
processing is complete.

TODO: Replace the placeholder user-data script with real agent bootstrapping
      logic (install dependencies, clone repo, run the agent, POST result).
"""

import json
import os
import urllib.request
from urllib.error import HTTPError
from typing import Any, Dict

from util.env import require_env
from util.template import render_init_script


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def spawn_droplet_for_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new DigitalOcean droplet to process *task*.

    The droplet's cloud-init script is rendered from init.template.sh;
    CALLBACK_URL is read from the environment (set in .env).

    Returns the raw droplet object returned by the DigitalOcean API.
    """
    do_token = require_env("DIGITALOCEAN_TOKEN")
    droplet_region  = _env_get("DROPLET_REGION",  "nyc3")
    droplet_size    = _env_get("DROPLET_SIZE",    "s-1vcpu-1gb")
    droplet_image   = _env_get("DROPLET_IMAGE",   "ubuntu-22-04-x64")
    ssh_key_id      = _env_get("DROPLET_SSH_KEY_ID", None)
    project_id      = _env_get("DROPLET_PROJECT_ID", None)

    task_id = task.get("id", "unknown")
    prompt = (task.get("description") or "").strip()
    user_data = render_init_script(task_id=task_id, prompt=prompt)

    safe_task_id = task_id.replace("_", "-")
    payload: Dict[str, Any] = {
        "name": f"pi-worker-{safe_task_id}",
        "region": droplet_region,
        "size": droplet_size,
        "image": droplet_image,
        "user_data": user_data,
    }
    if ssh_key_id:
        payload["ssh_keys"] = [ssh_key_id]

    req = urllib.request.Request(
        "https://api.digitalocean.com/v2/droplets",
        headers={
            "Authorization": f"Bearer {do_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            droplet = result.get("droplet", result)
            droplet_id = droplet.get("id")
            print(f"[droplet] Created droplet '{droplet.get('name')}' (id={droplet_id}) for task {task_id}")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DigitalOcean droplet creation failed ({exc.code}): {error_body}") from exc

    if project_id and droplet_id:
        _assign_to_project(do_token, project_id, droplet_id)

    return droplet


def destroy_droplet(droplet_id: int | str) -> None:
    """Delete a DigitalOcean droplet by ID."""
    do_token = require_env("DIGITALOCEAN_TOKEN")

    req = urllib.request.Request(
        f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
        headers={"Authorization": f"Bearer {do_token}"},
        method="DELETE",
    )

    try:
        with urllib.request.urlopen(req, timeout=30):
            pass  # 204 No Content on success
        print(f"[droplet] Destroyed droplet {droplet_id}")
    except HTTPError as exc:
        if exc.code == 404:
            print(f"[droplet] Droplet {droplet_id} not found (already destroyed?)")
            return
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DigitalOcean droplet deletion failed ({exc.code}): {error_body}") from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env_get(name: str, default: Any) -> Any:
    value = (os.getenv(name) or "").strip()
    return value if value else default


def _assign_to_project(do_token: str, project_id: str, droplet_id: int) -> None:
    """Assign a droplet to a DigitalOcean project."""
    payload = {"resources": [f"do:droplet:{droplet_id}"]}
    req = urllib.request.Request(
        f"https://api.digitalocean.com/v2/projects/{project_id}/resources",
        headers={
            "Authorization": f"Bearer {do_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        print(f"[droplet] Assigned droplet {droplet_id} to project {project_id}")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Project assignment failed ({exc.code}): {error_body}") from exc
