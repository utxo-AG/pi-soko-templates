import json
import os
import time
from typing import Any, Dict

from dotenv import load_dotenv

from pi_session import run_pi_prompt
from services.sokosumi_service import (
    fetch_ready_tasks,
    post_task_completed_event,
    post_task_running_event,
)

def handle_ready_task(task: Dict[str, Any]) -> None:
    task_id = (task.get("id") or "").strip()
    if not task_id:
        raise RuntimeError("Task is missing 'id'")

    post_task_running_event(task_id)

    task_json = json.dumps(task, ensure_ascii=False)
    model = (os.getenv("PI_MODEL") or "").strip() or None
    
    print("processing task: ", task["description"])
    prompt = (
        "You are processing a ready task. "
        "Respond to this assignment as if you are Senku Ishigami from Dr. Stone:\n\n"
        f"{task['description']}"
    )

    result = run_pi_prompt(prompt, model=model)
    print("Agent result: ", result)
    post_task_completed_event(task_id, comment=result)
    print(result)

def main(poll_interval_seconds: int = 5) -> None:
    load_dotenv()

    base_url = (os.getenv("PREPROD_BASE_URL") or os.getenv("BASE_URL") or "").strip()

    print(f"Polling ready tasks every {poll_interval_seconds}s from {base_url.rstrip('/')}/tasks")

    while True:
        try:
            tasks = fetch_ready_tasks()
            if tasks:
                print(f"Found {len(tasks)} ready task(s)")
                for task in tasks:
                    handle_ready_task(task)
            time.sleep(poll_interval_seconds)
        except KeyboardInterrupt:
            print("\nStopped by user")
            return
        except Exception as exc:
            print(f"Polling error: {exc}")
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    main()
