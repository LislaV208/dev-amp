"""Run claude --agent as interactive subprocess."""

from __future__ import annotations

import subprocess
from pathlib import Path

# Agents directory relative to this package
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"


def get_agent_path(agent_name: str) -> Path:
    """Get absolute path to agent file."""
    path = AGENTS_DIR / f"{agent_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent file not found: {path}")
    return path


def launch_agent(
    agent_name: str,
    initial_message: str | None = None,
    add_dirs: list[str] | None = None,
) -> int:
    """Launch claude CLI with the given agent in interactive mode.

    Returns the exit code of the subprocess.
    """
    agent_path = get_agent_path(agent_name)

    cmd: list[str] = ["claude", "--agent", str(agent_path)]

    if add_dirs:
        for d in add_dirs:
            cmd.extend(["--add-dir", d])

    if initial_message:
        cmd.append(initial_message)

    result = subprocess.run(cmd)
    return result.returncode
