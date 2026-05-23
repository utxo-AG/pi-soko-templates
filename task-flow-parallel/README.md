# task-flow-parallel

Polls a [Sokosumi](https://sokosumi.com) task queue and processes ready tasks **in parallel** through ephemeral pi agent sessions, posting results back as completed events.

Parallelism is implemented with `asyncio` and capped by a `asyncio.Semaphore` so you never exceed the configured limit of concurrent agents.

## How It Works

1. `poll_ready_tasks.py` fetches tasks with status `READY` from the Sokosumi API on a configurable interval.
2. All ready tasks from a single poll are dispatched concurrently via `asyncio.gather`.
3. A `asyncio.Semaphore` ensures at most `PARALLEL_TASK_LIMIT` tasks run at the same time.
4. Each task is marked `RUNNING`, its `description` is sent as a prompt to `pi --mode rpc --no-session` via a non-blocking async subprocess.
5. The agent's response is posted back to the task as a `COMPLETED` event with a comment.

## Setup

```bash
cd templates/task-flow-parallel
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp example.env .env
# Edit .env with your real credentials
python poll_ready_tasks.py
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PREPROD_BASE_URL` | Yes* | — | Base URL for the pre-production Sokosumi API |
| `BASE_URL` | Yes* | — | Base URL for the production Sokosumi API |
| `COWORKER_ID` | Yes | — | Your Sokosumi coworker/agent ID |
| `SOKOSUMI_COWORKER_API_KEY` | Yes | — | API key for authenticating with Sokosumi |
| `PI_MODEL` | No | pi default | Override the default pi model (e.g. `claude-4-5`) |
| `PARALLEL_TASK_LIMIT` | No | `5` | Max number of tasks processed concurrently |

\* `PREPROD_BASE_URL` takes priority over `BASE_URL` if both are set.

## File Overview

```
task-flow-parallel/
├── poll_ready_tasks.py         # Entry point — async polling loop with Semaphore
├── pi_session.py               # Runs a single prompt via pi RPC (async subprocess)
├── services/
│   └── sokosumi_service.py     # Sokosumi API calls (fetch / event posting)
├── util/
│   └── env.py                  # require_env() helper
├── requirements.txt
└── example.env
```
