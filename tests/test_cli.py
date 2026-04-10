"""Tests for cli module — private helpers."""

from __future__ import annotations

from pathlib import Path

from devamp.cli import _update_epic_status


def _write_roadmap(tmp_path: Path, content: str) -> Path:
    """Helper: write content to .devamp/domain/roadmap.md and return file path."""
    roadmap = tmp_path / ".devamp" / "domain" / "roadmap.md"
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text(content, encoding="utf-8")
    return roadmap


def _read_roadmap(tmp_path: Path) -> str:
    return (tmp_path / ".devamp" / "domain" / "roadmap.md").read_text(encoding="utf-8")


# --- _update_epic_status ---


def test_update_epic_status_planned_to_in_progress(tmp_path: Path) -> None:
    """Happy path: changes Status from planned to in-progress."""
    _write_roadmap(
        tmp_path,
        """\
## My feature
Status: planned

Description.
""",
    )
    _update_epic_status(tmp_path, "My feature", "in-progress")

    result = _read_roadmap(tmp_path)
    assert "Status: in-progress" in result
    assert "Status: planned" not in result


def test_update_epic_status_no_impact_on_other_epics(tmp_path: Path) -> None:
    """Only the targeted epic is changed; others remain untouched."""
    _write_roadmap(
        tmp_path,
        """\
## Alpha
Status: planned

Alpha desc.

## Beta
Status: planned

Beta desc.

## Gamma
Status: done

Gamma desc.
""",
    )
    _update_epic_status(tmp_path, "Beta", "in-progress")

    result = _read_roadmap(tmp_path)
    lines = result.splitlines()

    # Alpha still planned
    alpha_idx = lines.index("## Alpha")
    assert lines[alpha_idx + 1] == "Status: planned"

    # Beta changed
    beta_idx = lines.index("## Beta")
    assert lines[beta_idx + 1] == "Status: in-progress"

    # Gamma still done
    gamma_idx = lines.index("## Gamma")
    assert lines[gamma_idx + 1] == "Status: done"


def test_update_epic_status_missing_file(tmp_path: Path) -> None:
    """No roadmap.md — silent no-op, no exception."""
    _update_epic_status(tmp_path, "Nonexistent", "in-progress")
    # No exception raised, no file created
    assert not (tmp_path / ".devamp" / "domain" / "roadmap.md").exists()


def test_update_epic_status_missing_heading(tmp_path: Path) -> None:
    """Epic name not in roadmap — file unchanged."""
    original = """\
## Other feature
Status: planned

Description.
"""
    _write_roadmap(tmp_path, original)
    _update_epic_status(tmp_path, "Nonexistent feature", "in-progress")

    assert _read_roadmap(tmp_path) == original


def test_update_epic_status_already_target_status(tmp_path: Path) -> None:
    """Epic already has the target status — idempotent, file stays valid."""
    _write_roadmap(
        tmp_path,
        """\
## My feature
Status: in-progress

Description.
""",
    )
    _update_epic_status(tmp_path, "My feature", "in-progress")

    result = _read_roadmap(tmp_path)
    assert result.count("Status: in-progress") == 1
    assert "## My feature" in result
