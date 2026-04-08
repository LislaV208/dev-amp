"""Run claude --agent as interactive subprocess."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Agents directory — bundled inside the package
AGENTS_DIR = Path(__file__).resolve().parent / "agents"

# Claude Code user agents directory
CLAUDE_AGENTS_DIR = Path.home() / ".claude" / "agents"


def sync_agents() -> None:
    """Copy bundled agent files to ~/.claude/agents/ so claude CLI can find them.

    Overwrites existing files to keep agents in sync with the installed devamp version.
    """
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    for agent_file in AGENTS_DIR.glob("*.md"):
        dest = CLAUDE_AGENTS_DIR / agent_file.name
        shutil.copy2(agent_file, dest)


def get_agent_path(agent_name: str) -> Path:
    """Get absolute path to bundled agent file (for validation)."""
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

    Syncs agents to ~/.claude/agents/ before launching, then passes the agent
    by name (not path) so claude CLI resolves it correctly.

    Returns the exit code of the subprocess.
    """
    # Validate bundled agent exists
    get_agent_path(agent_name)

    # Sync agents to ~/.claude/agents/ so claude --agent can find them by name
    sync_agents()

    cmd: list[str] = ["claude", "--agent", agent_name]

    if add_dirs:
        for d in add_dirs:
            cmd.extend(["--add-dir", d])

    if initial_message:
        cmd.append(initial_message)

    result = subprocess.run(cmd)
    return result.returncode
