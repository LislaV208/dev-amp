"""Tests for cli module — private helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from devamp.cli import _run_discovery, _start_adhoc_task, _start_epic_task, _update_epic_status
from devamp.scanner import (
    DOMAIN_DIR,
    TASKS_DIR,
    ProjectState,
    ProjectType,
    RoadmapEpic,
)


def _write_roadmap(tmp_path: Path, content: str) -> Path:
    """Helper: write content to .devamp/domain/roadmap.md and return file path."""
    roadmap = tmp_path / ".devamp" / "domain" / "roadmap.md"
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text(content, encoding="utf-8")
    return roadmap


def _read_roadmap(tmp_path: Path) -> str:
    return (tmp_path / ".devamp" / "domain" / "roadmap.md").read_text(encoding="utf-8")


def _make_project_state(
    has_domain: bool = False,
    project_type: ProjectType = ProjectType.SINGLE,
) -> ProjectState:
    return ProjectState(
        project_type=project_type,
        has_domain=has_domain,
        tasks=[],
        repos=[],
    )


# ---------------------------------------------------------------------------
# _update_epic_status
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Project root in direct construction paths (not through context.py)
# ---------------------------------------------------------------------------


class TestStartEpicTaskProjectRoot:
    """_start_epic_task initial message starts with Project root."""

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    def test_project_root_is_first_line(
        self, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        (tmp_path / TASKS_DIR).mkdir(parents=True, exist_ok=True)
        state = _make_project_state(has_domain=True)
        epic = RoadmapEpic(
            name="My Epic",
            status="in-progress",
            content="## My Epic\nStatus: in-progress\n",
        )

        _start_epic_task(tmp_path, state, epic)

        mock_launch.assert_called_once()
        msg = mock_launch.call_args[0][1]
        assert msg.startswith(f"Project root: {tmp_path}")

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    def test_contains_domain_and_epic(
        self, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        (tmp_path / TASKS_DIR).mkdir(parents=True, exist_ok=True)
        state = _make_project_state(has_domain=True)
        epic = RoadmapEpic(
            name="E",
            status="in-progress",
            content="## E\nStatus: in-progress\n",
        )

        _start_epic_task(tmp_path, state, epic)

        msg = mock_launch.call_args[0][1]
        assert f"Domain: {tmp_path / DOMAIN_DIR}/" in msg
        assert "Roadmap epic:" in msg
        assert "## E" in msg

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    def test_no_trailing_slash_on_root(
        self, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        (tmp_path / TASKS_DIR).mkdir(parents=True, exist_ok=True)
        state = _make_project_state(has_domain=True)
        epic = RoadmapEpic(name="E", status="in-progress", content="content")

        _start_epic_task(tmp_path, state, epic)

        msg = mock_launch.call_args[0][1]
        first_line = msg.splitlines()[0]
        assert first_line == f"Project root: {tmp_path}"
        assert not first_line.endswith("/")


class TestStartAdhocTaskProjectRoot:
    """_start_adhoc_task initial message starts with Project root."""

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    @patch("devamp.cli.typer.prompt", return_value=1)
    def test_project_root_with_domain(
        self, mock_prompt: MagicMock, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        (tmp_path / TASKS_DIR).mkdir(parents=True, exist_ok=True)
        state = _make_project_state(has_domain=True)

        _start_adhoc_task(tmp_path, state)

        msg = mock_launch.call_args[0][1]
        first_line = msg.splitlines()[0]
        assert first_line == f"Project root: {tmp_path}"
        assert f"Domain: {tmp_path / DOMAIN_DIR}/" in msg

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    @patch("devamp.cli.typer.prompt", return_value=1)
    def test_project_root_without_domain(
        self, mock_prompt: MagicMock, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        (tmp_path / TASKS_DIR).mkdir(parents=True, exist_ok=True)
        state = _make_project_state(has_domain=False)

        _start_adhoc_task(tmp_path, state)

        msg = mock_launch.call_args[0][1]
        assert msg == f"Project root: {tmp_path}"
        assert "Domain:" not in msg


class TestRunDiscoveryProjectRoot:
    """_run_discovery initial message starts with Project root."""

    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    def test_project_root_with_domain(
        self, mock_launch: MagicMock, tmp_path: Path
    ) -> None:
        # Create domain dir so success check passes
        domain_dir = tmp_path / DOMAIN_DIR
        domain_dir.mkdir(parents=True, exist_ok=True)
        (domain_dir / "context.md").write_text("content", encoding="utf-8")
        state = _make_project_state(has_domain=True)

        _run_discovery(tmp_path, state)

        msg = mock_launch.call_args[0][1]
        first_line = msg.splitlines()[0]
        assert first_line == f"Project root: {tmp_path}"
        assert f"Domain: {tmp_path / DOMAIN_DIR}/" in msg

    @patch("devamp.cli.typer.confirm", return_value=False)
    @patch("devamp.cli.launch_agent", return_value=(0, "sid"))
    def test_project_root_without_domain(
        self, mock_launch: MagicMock, mock_confirm: MagicMock, tmp_path: Path
    ) -> None:
        state = _make_project_state(has_domain=False)

        _run_discovery(tmp_path, state)

        msg = mock_launch.call_args[0][1]
        assert msg == f"Project root: {tmp_path}"
        assert "Domain:" not in msg
