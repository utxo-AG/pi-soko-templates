# task-flow

Polls a [Sokosumi](https://sokosumi.com) task queue, processes each ready task through an ephemeral pi agent session, and posts the result back as a completed event.

## How It Works

1. `poll_ready_tasks.py` fetches tasks with status `READY` from the Sokosumi API on a configurable interval.
2. Each task is marked `RUNNING`, then its `description` is sent as a prompt to `pi --mode rpc --no-session`.
3. The agent's response is posted back to the task as a `COMPLETED` event with a comment.

## Setup

```bash
cd templates/task-flow
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp example.env .env
# Edit .env with your real credentials
python poll_ready_tasks.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PREPROD_BASE_URL` | Yes* | Base URL for the pre-production Sokosumi API |
| `BASE_URL` | Yes* | Base URL for the production Sokosumi API |
| `COWORKER_ID` | Yes | Your Sokosumi coworker/agent ID |
| `SOKOSUMI_COWORKER_API_KEY` | Yes | API key for authenticating with Sokosumi |
| `PI_MODEL` | No | Override the default pi model (e.g. `claude-4-5`) |

\* `PREPROD_BASE_URL` takes priority over `BASE_URL` if both are set.

## File Overview

```
task-flow/
├── poll_ready_tasks.py         # Entry point — polling loop
├── pi_session.py               # Runs a single prompt via pi RPC
├── services/
│   └── sokosumi_service.py     # Sokosumi API calls (fetch / event posting)
├── util/
│   └── env.py                  # require_env() helper
├── requirements.txt
└── example.env
```
