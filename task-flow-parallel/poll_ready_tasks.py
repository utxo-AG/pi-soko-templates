import asyncio
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv

from pi_session import run_pi_prompt_async
from services.sokosumi_service import (
    fetch_ready_tasks,
    post_task_completed_event,
    post_task_running_event,
)


async def handle_ready_task(task: Dict[str, Any], sem: asyncio.Semaphore) -> None:
    async with sem:
        task_id = (task.get("id") or "").strip()
        if not task_id:
            raise RuntimeError("Task is missing 'id'")

        post_task_running_event(task_id)

        model = (os.getenv("PI_MODEL") or "").strip() or None

        print(f"[{task_id}] processing task: {task['description']}")
        prompt = (
            "You are processing a ready task. "
            "Respond to this assignment in the style Senku Ishigami from Dr. Stone:\n\n"
            f"{task['description']}"
        )

        result = await run_pi_prompt_async(prompt, model=model)
        print(f"[{task_id}] Agent result: {result}")
        post_task_completed_event(task_id, comment=result)


async def poll_loop(poll_interval_seconds: int, sem: asyncio.Semaphore) -> None:
    base_url = (os.getenv("PREPROD_BASE_URL") or os.getenv("BASE_URL") or "").strip()
    print(f"Polling ready tasks every {poll_interval_seconds}s from {base_url.rstrip('/')}/tasks")

    while True:
        try:
            tasks = fetch_ready_tasks()
            if tasks:
                print(f"Found {len(tasks)} ready task(s)")
                await asyncio.gather(
                    *[handle_ready_task(task, sem) for task in tasks],
                    return_exceptions=True,
                )
        except Exception as exc:
            print(f"Polling error: {exc}")

        await asyncio.sleep(poll_interval_seconds)


def main(poll_interval_seconds: int = 5) -> None:
    load_dotenv()

    parallel_limit = int((os.getenv("PARALLEL_TASK_LIMIT") or "5").strip())
    sem = asyncio.Semaphore(parallel_limit)
    print(f"Parallel task limit: {parallel_limit}")

    try:
        asyncio.run(poll_loop(poll_interval_seconds, sem))
    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == "__main__":
    main()
