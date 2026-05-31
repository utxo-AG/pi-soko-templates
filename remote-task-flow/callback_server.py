"""
Flask callback server.

Droplets POST their completed-task results here once processing is done.

Expected JSON body:
    {
        "success": false,
        "error": "<agent error message or null>",
        "response": "<agent response text>",
        "taskId": "<task id>"
    }

The droplet name is derived as "pi-worker-{taskId}" — matching the name
assigned at creation time in droplet_service.py.

The endpoint validates the payload, prints the result, and responds 200 OK.
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from services.droplet_service import droplet_name_for_task, destroy_droplet_for_task
from services.sokosumi_service import post_task_completed_event

load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)


@app.post("/tasks/complete")
def task_complete():
    """Receive a completed-task result posted by a remote droplet."""
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    task_id = data.get("taskId")
    success = data.get("success")
    error = data.get("error")
    response = data.get("response")

    if not task_id:
        return jsonify({"error": "Missing required field: taskId"}), 400

    droplet_name = droplet_name_for_task(task_id)

    # ------------------------------------------------------------------
    # Print the result — replace with real handling (DB write, event, …)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Received completed task result from droplet")
    print(f"  taskId      : {task_id}")
    print(f"  droplet_name: {droplet_name}")
    print(f"  success     : {success}")
    print(f"  error       : {error}")
    print(f"  response    : {response}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Report completion back to Sokosumi
    # ------------------------------------------------------------------
    post_task_completed_event(task_id, comment=response or "")

    # ------------------------------------------------------------------
    # Destroy the droplet that processed this task
    # ------------------------------------------------------------------
    droplet_warning = None
    try:
        destroy_droplet_for_task(task_id)
    except RuntimeError as exc:
        droplet_warning = str(exc)
        print(f"[callback] Droplet cleanup failed: {droplet_warning}")

    resp: dict = {"received": True}
    if droplet_warning:
        resp["dropletCleanupError"] = droplet_warning

    return jsonify(resp), 200


if __name__ == "__main__":
    host = os.getenv("CALLBACK_HOST", "0.0.0.0")
    port = int(os.getenv("CALLBACK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"Starting callback server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
