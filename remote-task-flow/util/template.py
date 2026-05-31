"""
Template rendering utility for init.template.sh.

Exposes render_init_script() for use by other modules (e.g. droplet_service),
and render() as a low-level helper for tests / CLI use.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = REPO_ROOT / "init.template.sh"

# Loaded once from .env; individual call sites can override via the
# `extra` parameter of render_init_script().
_ENV_VARS = ["MODEL_PROVIDER", "MODEL_ID", "MODEL_API_KEY", "CALLBACK_URL"]


def render(template: str, variables: dict[str, str]) -> str:
    """Replace every {{KEY}} placeholder with its value.

    Raises KeyError if a placeholder has no matching entry in *variables*.
    """

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(f"No value provided for template variable: {{{{{key}}}}}")
        return variables[key]

    return re.sub(r"\{\{([A-Z_]+)\}\}", replacer, template)


def render_init_script(task_id: str, prompt: str) -> str:
    """Render init.template.sh for a specific task.

    Static variables (MODEL_PROVIDER, MODEL_ID, MODEL_API_KEY, CALLBACK_URL)
    are read from the environment (populated by load_dotenv in the caller, or
    already present in os.environ).

    Args:
        task_id: The task's unique identifier — fills {{TASK_ID}}.
        prompt:  The task's prompt text — fills {{PROMPT}}.

    Returns:
        The fully rendered shell script as a string.

    Raises:
        FileNotFoundError: If init.template.sh does not exist.
        RuntimeError:      If any required .env variable is missing.
        KeyError:          If the template contains an unresolvable placeholder.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    missing = [k for k in _ENV_VARS if not (os.getenv(k) or "").strip()]
    if missing:
        raise RuntimeError(
            "Missing required env vars for init.template.sh rendering: "
            + ", ".join(missing)
        )

    variables = {k: os.environ[k].strip() for k in _ENV_VARS}
    variables["TASK_ID"] = task_id
    variables["PROMPT"] = prompt

    return render(TEMPLATE_PATH.read_text(), variables)
