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

The endpoint validates the payload, prints the result, and responds 200 OK.
"""

import json
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

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

    # ------------------------------------------------------------------
    # Print the result — replace with real handling (DB write, event, …)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Received completed task result from droplet")
    print(f"  taskId  : {task_id}")
    print(f"  success : {success}")
    print(f"  error   : {error}")
    print(f"  response: {response}")
    print("=" * 60)

    return jsonify({"received": True}), 200


if __name__ == "__main__":
    host = os.getenv("CALLBACK_HOST", "0.0.0.0")
    port = int(os.getenv("CALLBACK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"Starting callback server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
