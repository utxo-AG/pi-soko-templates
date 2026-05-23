import asyncio
import json
from typing import Optional


async def run_pi_prompt_async(prompt: str, model: Optional[str] = None) -> str:
    """Start a new ephemeral pi session, send one prompt, and return the final assistant text."""
    cmd = ["pi", "--mode", "rpc", "--no-session"]
    if model:
        cmd += ["--model", model]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    # Send the prompt command
    proc.stdin.write((json.dumps({"type": "prompt", "message": prompt}) + "\n").encode())
    await proc.stdin.drain()

    chunks = []
    try:
        async for raw_line in proc.stdout:
            line = raw_line.decode().strip()
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
        await proc.wait()

    result = "".join(chunks).strip()

    if not result:
        assert proc.stderr is not None
        stderr_output = (await proc.stderr.read()).decode().strip()
        if stderr_output:
            raise RuntimeError(f"pi process error: {stderr_output}")

    return result


if __name__ == "__main__":
    async def _test() -> None:
        print(await run_pi_prompt_async("What do you call a dog in spanish?"))

    asyncio.run(_test())
