#!/usr/bin/env python3
"""
Render init.template.sh → a ready-to-run init script.

Variables resolved from two sources:
  .env file  : MODEL_PROVIDER, MODEL_ID, MODEL_API_KEY, CALLBACK_URL
  CLI args   : TASK_ID (--task-id), PROMPT (--prompt)

Usage:
  python render_init.py --task-id <id> --prompt <text> [--out <path>]

  # or pass runtime vars via environment variables:
  TASK_ID=abc123 PROMPT="do something" python render_init.py
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from util.template import render_init_script

SCRIPT_DIR = Path(__file__).parent
DEFAULT_OUT_PATH = SCRIPT_DIR / "init.sh"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render init.template.sh with values from .env and runtime args."
    )
    parser.add_argument("--task-id", metavar="ID", help="Task ID (TASK_ID)")
    parser.add_argument("--prompt", metavar="TEXT", help="Prompt text (PROMPT)")
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=str(DEFAULT_OUT_PATH),
        help=f"Output path (default: {DEFAULT_OUT_PATH})",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print rendered script to stdout instead of writing a file",
    )
    args = parser.parse_args()

    # ── Load .env ──────────────────────────────────────────────────────────
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        print(f"ERROR: .env not found at {env_path}", file=sys.stderr)
        sys.exit(1)
    load_dotenv(env_path, override=False)

    # ── Collect runtime variables (CLI args take precedence over env) ──────
    task_id = args.task_id or (os.getenv("TASK_ID") or "").strip()
    prompt = args.prompt or (os.getenv("PROMPT") or "").strip()

    missing_runtime: list[str] = []
    if not task_id:
        missing_runtime.append("TASK_ID  (pass --task-id <id> or set TASK_ID env var)")
    if not prompt:
        missing_runtime.append("PROMPT   (pass --prompt <text> or set PROMPT env var)")

    if missing_runtime:
        print(
            "ERROR: The following runtime variables are missing:\n"
            + "\n".join(f"  {m}" for m in missing_runtime),
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Render ─────────────────────────────────────────────────────────────
    try:
        rendered = render_init_script(task_id=task_id, prompt=prompt)
    except (FileNotFoundError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Output ─────────────────────────────────────────────────────────────
    if args.stdout:
        print(rendered, end="")
    else:
        out_path = Path(args.out)
        out_path.write_text(rendered)
        out_path.chmod(0o755)
        print(f"Rendered → {out_path}")


if __name__ == "__main__":
    main()
