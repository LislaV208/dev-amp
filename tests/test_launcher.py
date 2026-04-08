"""Tests for launcher module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from devamp.launcher import (
    AGENTS_DIR,
    get_agent_path,
    sync_agents,
)


def test_get_agent_path_valid():
    """Known agent name returns a path inside AGENTS_DIR."""
    path = get_agent_path("product")
    assert path == AGENTS_DIR / "product.md"
    assert path.exists()


def test_get_agent_path_renamed_agents():
    """Renamed agents (architect, planner, dev) should be findable."""
    for name in ("architect", "planner", "dev"):
        path = get_agent_path(name)
        assert path.exists()


def test_get_agent_path_invalid():
    """Unknown agent name raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        get_agent_path("nonexistent-agent")


def test_get_agent_path_old_names_invalid():
    """Old agent names should no longer exist."""
    for old_name in ("developer-system", "developer-multi", "developer-single"):
        with pytest.raises(FileNotFoundError):
            get_agent_path(old_name)


def test_sync_agents_copies_files(tmp_path: Path):
    """sync_agents copies all bundled .md files to the target directory."""
    fake_claude_agents = tmp_path / ".claude" / "agents"

    with patch("devamp.launcher.CLAUDE_AGENTS_DIR", fake_claude_agents):
        sync_agents()

    bundled = sorted(f.name for f in AGENTS_DIR.glob("*.md"))
    copied = sorted(f.name for f in fake_claude_agents.glob("*.md"))
    assert bundled == copied
    assert len(copied) > 0


def test_sync_agents_overwrites_existing(tmp_path: Path):
    """sync_agents overwrites existing files to keep them up to date."""
    fake_claude_agents = tmp_path / ".claude" / "agents"
    fake_claude_agents.mkdir(parents=True)

    stale = fake_claude_agents / "product.md"
    stale.write_text("old content")

    with patch("devamp.launcher.CLAUDE_AGENTS_DIR", fake_claude_agents):
        sync_agents()

    assert stale.read_text() != "old content"
    assert stale.read_text() == (AGENTS_DIR / "product.md").read_text()
