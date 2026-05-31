#!/usr/bin/env bash
set -euo pipefail

MODEL_PROVIDER="{{MODEL_PROVIDER}}"
MODEL_ID="{{MODEL_ID}}"
MODEL_API_KEY="{{MODEL_API_KEY}}"
PROMPT="{{PROMPT}}"
CALLBACK_URL="{{CALLBACK_URL}}"
TASK_ID="{{TASK_ID}}"

run_as_agent() {
  cd "$HOME"

  # Ensure Pi-managed Node is on PATH for non-interactive shells
  for d in "$HOME"/.local/share/pi-node/node-*/bin; do
    [ -d "$d" ] && export PATH="$d:$PATH"
  done

  export MODEL_PROVIDER MODEL_ID MODEL_API_KEY PROMPT CALLBACK_URL TASK_ID

  if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: node not found (HOME=$HOME, PATH=$PATH)" >&2
    exit 127
  fi

  node --experimental-strip-types ./worker.ts
}

if [[ "$(id -un)" == "agent" ]]; then
  run_as_agent
else
  su - agent -c "bash -lc 'cd ~ && for d in \"\$HOME\"/.local/share/pi-node/node-*/bin; do [ -d \"\$d\" ] && export PATH=\"\$d:\$PATH\"; done; MODEL_PROVIDER=\"$MODEL_PROVIDER\" MODEL_ID=\"$MODEL_ID\" MODEL_API_KEY=\"$MODEL_API_KEY\" PROMPT=\"$PROMPT\" CALLBACK_URL=\"$CALLBACK_URL\" TASK_ID=\"$TASK_ID\" node --experimental-strip-types ./worker.ts'"
fi
