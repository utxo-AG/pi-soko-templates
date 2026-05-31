# droplet-task-flow

Polls a [Sokosumi](https://sokosumi.com) task queue and hands each ready task off to a freshly-created DigitalOcean droplet for processing.  The droplet POSTs its result back to a Flask callback server running alongside the poller.

## How It Works

```
┌─────────────────────────┐          ┌───────────────────────┐
│  poll_ready_tasks.py    │  spawns  │  DigitalOcean Droplet │
│  (polling loop)         │─────────▶│  (remote agent)       │
│                         │          │                       │
│  callback_server.py     │◀─────────│  POST /tasks/complete │
│  (Flask server)         │  result  └───────────────────────┘
└─────────────────────────┘
         │ RUNNING / COMPLETED events
         ▼
   Sokosumi API
```

1. **`poll_ready_tasks.py`** polls the Sokosumi API for tasks with status `READY`.
2. Each task is immediately marked `RUNNING` via the Sokosumi API.
3. A new DigitalOcean droplet is created with the task payload and the callback URL baked into its cloud-init user-data.
4. The droplet processes the task (currently a **placeholder** — see `services/droplet_service.py`) and POSTs the result JSON to `POST /tasks/complete` on this server.
5. **`callback_server.py`** receives the result and prints it.  Wire up `post_task_completed_event` here when you're ready to report back to Sokosumi.

## Setup

```bash
cd templates/droplet-task-flow
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

> **Tip:** `CALLBACK_BASE_URL` must be publicly reachable from the internet so the droplet can POST back.  Use your server's public IP or a tunnel like [ngrok](https://ngrok.com) during development.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PREPROD_BASE_URL` | Yes* | Base URL for the pre-production Sokosumi API |
| `BASE_URL` | Yes* | Base URL for the production Sokosumi API |
| `COWORKER_ID` | Yes | Your Sokosumi coworker/agent ID |
| `SOKOSUMI_COWORKER_API_KEY` | Yes | API key for authenticating with Sokosumi |
| `CALLBACK_BASE_URL` | Yes | Public URL of this server; droplets POST results to `{CALLBACK_BASE_URL}/tasks/complete` |
| `DIGITALOCEAN_TOKEN` | Yes | DigitalOcean personal access token |
| `DROPLET_REGION` | No | Droplet region (default: `nyc3`) |
| `DROPLET_SIZE` | No | Droplet size slug (default: `s-1vcpu-1gb`) |
| `DROPLET_IMAGE` | No | Droplet image slug (default: `ubuntu-22-04-x64`) |
| `CALLBACK_HOST` | No | Host for the Flask callback server (default: `0.0.0.0`) |
| `CALLBACK_PORT` | No | Port for the Flask callback server (default: `5000`) |
| `FLASK_DEBUG` | No | Enable Flask debug mode (default: `false`) |

\* `PREPROD_BASE_URL` takes priority over `BASE_URL` if both are set.

## File Overview

```
droplet-task-flow/
├── poll_ready_tasks.py          # Entry point — polling loop + droplet hand-off
├── callback_server.py           # Flask server — receives completed-task results
├── services/
│   ├── sokosumi_service.py      # Sokosumi API calls (fetch / event posting)
│   └── droplet_service.py       # DigitalOcean droplet creation / destruction
├── util/
│   └── env.py                   # require_env() helper
├── requirements.txt
└── example.env
```

## Implementing Real Task Processing

The actual agent work happens inside the droplet's cloud-init user-data script.
Open `services/droplet_service.py` and replace the placeholder `_build_user_data`
function with your real bootstrapping logic:

```bash
# Example steps the user-data script should perform:
apt-get update -y && apt-get install -y python3 python3-pip curl
pip3 install <your-agent-package>
RESULT=$(your-agent --task "$TASK")
curl -s -X POST "$CALLBACK_URL" \
     -H "Content-Type: application/json" \
     -d "{\"success\":true,\"error\":null,\"response\":\"$RESULT\"}"
```

Once you've verified the flow end-to-end you'll also want to:
- Call `post_task_completed_event` inside the `/tasks/complete` handler in `callback_server.py`.
- Optionally destroy the droplet after the result is received (see `destroy_droplet` in `droplet_service.py`).
