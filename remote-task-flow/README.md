# remote-task-flow

Polls a [Sokosumi](https://sokosumi.com) task queue and hands each ready task off to a freshly-created DigitalOcean droplet form a snapshot running a pi agent. The droplet POSTs its result back to a Flask callback server, which then destroys the droplet.

## How It Works

```
┌──────────────────────────────┐
│       Sokosumi API           │
└──────┬───────────────────────┘
       │ 1. fetch READY tasks
       ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│   poll_ready_tasks.py        │        │    DigitalOcean Droplet      │
│   (polling loop)             │        │    (pi agent)                │
│                              │        │                              │
│  2. render init.sh ──────────┼───────▶│  init.sh runs on             │
│     from init.template.sh    │ spawns │  boot via cloud-init         │
│  3. spawn droplet with       │        │                              │
│     rendered script as       │        │  5. agent processes task     │
│     user_data                │        │                              │
│  4. mark task RUNNING        │        │  6. POST /tasks/complete     │
└──────────────────────────────┘        │     {taskId, success,        │
                                        │      error, response}        │
┌──────────────────────────────┐        │                              │
│   callback_server.py         │◀───────┴──────────────────────────────┘
│   (Flask server)             │
│                              │
│  7. print result             │
│  8. destroy droplet ─────────┼────▶ DO API DELETE /v2/droplets/{id}
│     by task id               │
└──────────────────────────────┘
```

1. **`poll_ready_tasks.py`** polls the Sokosumi API for tasks with status `READY`.
2. `init.template.sh` is rendered in memory with the task's `id`, `description`, and static config from `.env` (`MODEL_PROVIDER`, `MODEL_ID`, `MODEL_API_KEY`, `CALLBACK_URL`).
3. A new DigitalOcean droplet is created with the rendered script as its cloud-init `user_data`. The droplet name is `pi-worker-{task-id}`.
4. On boot the droplet runs the init script, which starts the pi agent with the task prompt.
5. The task is marked `RUNNING` via the Sokosumi API.
6. The agent POSTs its result to `CALLBACK_URL` (`POST /tasks/complete`) with `taskId`, `success`, `error`, and `response`.
7. **`callback_server.py`** receives and prints the result.
8. The callback server looks up the droplet by name (`pi-worker-{task-id}`) and destroys it. If no droplet is found it logs a warning and continues.

## Setup

```bash
cd remote-task-flow
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp example.env .env
# Edit .env with your real credentials
```

### Run both processes

**Terminal 1 — callback server:**
```bash
python callback_server.py
```

**Terminal 2 — task poller:**
```bash
python poll_ready_tasks.py
```

> **Tip:** `CALLBACK_URL` must be publicly reachable from the internet so the droplet can POST back. Use your server's public IP or a tunnel like [ngrok](https://ngrok.com) during development.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PREPROD_BASE_URL` | Yes* | Base URL for the pre-production Sokosumi API |
| `BASE_URL` | Yes* | Base URL for the production Sokosumi API |
| `COWORKER_ID` | Yes | Your Sokosumi coworker/agent ID |
| `SOKOSUMI_COWORKER_API_KEY` | Yes | API key for authenticating with Sokosumi |
| `DIGITALOCEAN_TOKEN` | Yes | DigitalOcean personal access token |
| `MODEL_PROVIDER` | Yes | Model provider passed to the pi agent (e.g. `openrouter`) |
| `MODEL_ID` | Yes | Model ID passed to the pi agent (e.g. `openai/gpt-4o`) |
| `MODEL_API_KEY` | Yes | API key for the model provider |
| `CALLBACK_URL` | Yes | Full public URL the droplet POSTs results to (e.g. `http://your-ip:5000/tasks/complete`) |
| `DROPLET_REGION` | No | Droplet region (default: `nyc3`) |
| `DROPLET_SIZE` | No | Droplet size slug (default: `s-1vcpu-1gb`) |
| `DROPLET_IMAGE` | No | Droplet image ID or slug (default: `ubuntu-22-04-x64`) |
| `DROPLET_SSH_KEY_ID` | No | SSH key ID to inject into droplets (requires `ssh_key:read` token scope) |
| `DROPLET_PROJECT_ID` | No | Project to assign droplets to (requires `project:update` token scope) |
| `CALLBACK_HOST` | No | Host for the Flask callback server (default: `0.0.0.0`) |
| `CALLBACK_PORT` | No | Port for the Flask callback server (default: `5000`) |
| `FLASK_DEBUG` | No | Enable Flask debug mode (default: `false`) |

\* `PREPROD_BASE_URL` takes priority over `BASE_URL` if both are set.

## Callback Payload

The droplet's agent must POST the following JSON to `CALLBACK_URL` when done (this is pre configured for the server contained in the snapshot):

```json
{
  "taskId": "<task id>",
  "success": true,
  "error": null,
  "response": "<agent response text>"
}
```

The callback server responds `200 OK` with `{"received": true}`. If the droplet could not be found for cleanup, a `dropletCleanupError` field is included in the response.
