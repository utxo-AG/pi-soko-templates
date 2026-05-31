import os
import time
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from services.sokosumi_service import (
    fetch_ready_tasks,
    post_task_running_event,
)
from services.droplet_service import spawn_droplet_for_task


def handle_ready_task(task: Dict[str, Any]) -> None:
    task_id = (task.get("id") or "").strip()
    if not task_id:
        raise RuntimeError("Task is missing 'id'")

    print(f"Handing off task {task_id!r} to a new droplet")

    droplet = spawn_droplet_for_task(task)
    print(f"Droplet spawned: id={droplet.get('id')}, name={droplet.get('name')!r}")
    post_task_running_event(task_id)


def main(poll_interval_seconds: int = 5) -> None:
    load_dotenv(Path(__file__).parent / ".env")

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
