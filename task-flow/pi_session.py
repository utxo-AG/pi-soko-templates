import json
import subprocess
from typing import Optional


def run_pi_prompt(prompt: str, model: Optional[str] = None) -> str:
    """Start a new ephemeral pi session, send one prompt, and return the final assistant text."""
    cmd = ["pi", "--mode", "rpc", "--no-session"]
    if model:
        cmd += ["--model", model]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    # Send the prompt command
    proc.stdin.write(json.dumps({"type": "prompt", "message": prompt}) + "\n")
    proc.stdin.flush()

    chunks = []
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            event = json.loads(line)
            event_type = event.get("type")

            # Command-level errors
            if event_type == "response" and event.get("success") is False:
                raise RuntimeError(event.get("error", "Unknown RPC error"))

            # Stream assistant text
            if event_type == "message_update":
                delta = event.get("assistantMessageEvent", {})
                if delta.get("type") == "text_delta":
                    chunks.append(delta.get("delta", ""))

            # End of run
            if event_type == "agent_end":
                break
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    result = "".join(chunks).strip()

    if not result:
        stderr_output = proc.stderr.read().strip()
        if stderr_output:
            raise RuntimeError(f"pi process error: {stderr_output}")

    return result


if __name__ == "__main__":
    print(run_pi_prompt("What do you call a dog in spanish?"))
