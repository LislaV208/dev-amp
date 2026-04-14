"""Tests for context module — build_initial_message, build_cascade_message, _base_message."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devamp.context import _base_message, build_cascade_message, build_initial_message
from devamp.scanner import DOMAIN_DIR, ProjectState, ProjectType, TaskState, TaskStep

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(
    tmp_path: Path, name: str, step: TaskStep, files: list[str] | None = None
) -> TaskState:
    """Create a task directory with optional files and return TaskState."""
    task_dir = tmp_path / ".devamp" / "tasks" / name
    task_dir.mkdir(parents=True, exist_ok=True)
    for f in files or []:
        (task_dir / f).write_text("content", encoding="utf-8")
    return TaskState(name=name, step=step, path=task_dir)


def _make_project_state(
    has_domain: bool = False,
    repos: list[str] | None = None,
    project_type: ProjectType = ProjectType.SINGLE,
    tasks: list[TaskState] | None = None,
) -> ProjectState:
    return ProjectState(
        project_type=project_type,
        has_domain=has_domain,
        tasks=tasks or [],
        repos=repos or [],
    )


def _write_metadata(task: TaskState, routing_next: str, routing_reason: str) -> None:
    """Write task-metadata.json with routing info (for delegation context tests)."""
    meta = {
        "created_at": "2026-01-01T00:00:00+00:00",
        "sessions": {},
        "last_routing_next": routing_next,
        "last_routing_reason": routing_reason,
    }
    (task.path / "task-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# build_initial_message — Project root always first line
# ---------------------------------------------------------------------------


class TestBuildInitialMessageProjectRoot:
    """Project root: must be the first line in every message."""

    @pytest.mark.parametrize(
        "step",
        [TaskStep.PRODUCT, TaskStep.ARCHITECT, TaskStep.PLANNER, TaskStep.DEV, TaskStep.QA],
    )
    def test_first_line_is_project_root(self, tmp_path: Path, step: TaskStep) -> None:
        files = {
            TaskStep.ARCHITECT: ["spec.md"],
            TaskStep.PLANNER: ["system-analysis.md"],
            TaskStep.DEV: ["multi-plan.md"],
            TaskStep.QA: ["qa-input.md"],
        }
        task = _make_task(tmp_path, "t", step, files.get(step, []))
        state = _make_project_state(has_domain=True)

        msg = build_initial_message(task, state, tmp_path)
        assert msg.startswith(f"Project root: {tmp_path}")

    def test_never_returns_none(self, tmp_path: Path) -> None:
        """Even PRODUCT without domain must return a string (not None)."""
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=False)

        msg = build_initial_message(task, state, tmp_path)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_no_trailing_slash_on_root(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=False)

        msg = build_initial_message(task, state, tmp_path)
        first_line = msg.splitlines()[0]
        assert not first_line.endswith("/")


# ---------------------------------------------------------------------------
# build_initial_message — per-step content
# ---------------------------------------------------------------------------


class TestBuildInitialMessageSteps:
    """Each pipeline step produces the expected message body."""

    def test_product_with_domain(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=True)

        msg = build_initial_message(task, state, tmp_path)
        assert f"Domain: {tmp_path}/{DOMAIN_DIR}/" in msg

    def test_product_without_domain(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=False)

        msg = build_initial_message(task, state, tmp_path)
        # Only Project root line, no Domain
        assert "Domain:" not in msg
        assert f"Project root: {tmp_path}" in msg

    def test_architect_without_repos(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.ARCHITECT, ["spec.md"])
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert f"Spec: {task.path}/spec.md" in msg
        assert "Repos:" not in msg

    def test_architect_with_repos(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.ARCHITECT, ["spec.md"])
        state = _make_project_state(repos=["backend", "frontend"], project_type=ProjectType.MULTI)

        msg = build_initial_message(task, state, tmp_path)
        assert f"Spec: {task.path}/spec.md" in msg
        assert "Repos: backend, frontend" in msg

    def test_planner(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.PLANNER, ["system-analysis.md"])
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert f"System analysis: {task.path}/system-analysis.md" in msg

    def test_dev_with_plan(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["multi-plan.md"])
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert f"Plan: {task.path}/multi-plan.md" in msg

    def test_dev_without_plan(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["spec.md"])
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert f"Spec: {task.path}/spec.md" in msg

    def test_qa(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.QA, ["qa-input.md"])
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert f"Handoff: {task.path}/qa-input.md" in msg


# ---------------------------------------------------------------------------
# build_initial_message — delegation context
# ---------------------------------------------------------------------------


class TestBuildInitialMessageDelegation:
    """When metadata has routing info, delegation context is included."""

    def test_delegation_from_architect(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.PLANNER, ["system-analysis.md"])
        _write_metadata(task, "planner", "Analysis complete")
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert "Delegated from architect" in msg
        assert "system-analysis.md" in msg
        assert "Reason: Analysis complete" in msg
        # Project root still first
        assert msg.startswith(f"Project root: {tmp_path}")

    def test_delegation_from_planner(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["multi-plan.md"])
        _write_metadata(task, "dev", "Plan ready")
        state = _make_project_state()

        msg = build_initial_message(task, state, tmp_path)
        assert "Delegated from planner" in msg
        assert "multi-plan.md" in msg
        assert "Reason: Plan ready" in msg


# ---------------------------------------------------------------------------
# build_cascade_message
# ---------------------------------------------------------------------------


class TestBuildCascadeMessage:
    """Cascade messages include Project root + upstream change notice + base."""

    def test_cascade_has_project_root_first(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["multi-plan.md"])
        state = _make_project_state()

        msg = build_cascade_message(task, state, "planner", tmp_path)
        assert msg.startswith(f"Project root: {tmp_path}")

    def test_cascade_contains_upstream_notice(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["multi-plan.md"])
        state = _make_project_state()

        msg = build_cascade_message(task, state, "planner", tmp_path)
        assert "Upstream artifact changed" in msg
        assert "multi-plan.md" in msg
        assert "Review the updated input" in msg

    def test_cascade_contains_base_message(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.DEV, ["multi-plan.md"])
        state = _make_project_state()

        msg = build_cascade_message(task, state, "planner", tmp_path)
        assert f"Plan: {task.path}/multi-plan.md" in msg

    def test_cascade_qa_step(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "feat", TaskStep.QA, ["qa-input.md"])
        state = _make_project_state()

        msg = build_cascade_message(task, state, "dev", tmp_path)
        assert f"Project root: {tmp_path}" in msg
        assert f"Handoff: {task.path}/qa-input.md" in msg


# ---------------------------------------------------------------------------
# _base_message — DOMAIN_DIR is absolute
# ---------------------------------------------------------------------------


class TestBaseMessageDomainAbsolute:
    """DOMAIN_DIR in _base_message output contains cwd (is absolute)."""

    def test_domain_path_is_absolute(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=True)

        msg = _base_message(task, state, tmp_path)
        assert msg is not None
        assert str(tmp_path) in msg
        assert f"{tmp_path}/{DOMAIN_DIR}/" in msg

    def test_no_domain_returns_none(self, tmp_path: Path) -> None:
        task = _make_task(tmp_path, "t", TaskStep.PRODUCT)
        state = _make_project_state(has_domain=False)

        msg = _base_message(task, state, tmp_path)
        assert msg is None
