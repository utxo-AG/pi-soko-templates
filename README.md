# pi Templates

A monorepo of example templates showing how to integrate with the [pi SDK](https://www.npmjs.com/package/@earendil-works/pi-coding-agent).

## Structure

```
pi-soko-templates/
├── task-flow/              # Poll a task queue and process tasks with pi
├── <your-template>/        # Add more templates here
├── package.json            # Root workspace config
├── .gitignore
└── README.md
```

## Templates

| Template | Description | Language |
|---|---|---|
| [task-flow](./task-flow) | Polls a Sokosumi task queue, runs each task through a pi agent session, and posts results back | Python + Node |

## Adding a New Template

1. Create a new directory in the project root:
   ```
   my-new-template/
   ├── README.md         # Required: describe what the template does
   ├── example.env       # Required: document all env vars (no real secrets)
   └── ...               # Your template source files
   ```

2. Each template must include:
   - **`README.md`** — purpose, setup steps, and env var reference
   - **`example.env`** — all required env vars with placeholder values

3. If your template uses Node, add a `package.json` so it is picked up as a workspace.

## Quick Start

Clone and set up a specific template:

```bash
git clone <this-repo>
cd pi-soko-templates/task-flow
cp example.env .env
# Fill in .env with real values, then:
pip install -r requirements.txt
python poll_ready_tasks.py
```
