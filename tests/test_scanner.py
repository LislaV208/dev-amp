"""Tests for scanner module — project type detection and task state reading."""

from __future__ import annotations

import json
from pathlib import Path

from devamp.scanner import (
    ProjectType,
    TaskStep,
    detect_project_type,
    detect_task_step,
    parse_roadmap,
    scan_project,
    scan_tasks,
)


def test_detect_empty_project(tmp_path: Path) -> None:
    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.EMPTY
    assert repos == []


def test_detect_single_repo_with_files(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')")
    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.SINGLE
    assert repos == []


def test_detect_single_repo_with_dir_no_git(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("")
    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.SINGLE
    assert repos == []


def test_detect_single_repo_one_git(tmp_path: Path) -> None:
    """One subdir with .git is still single-repo (needs 2+ for multi)."""
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / ".git").mkdir()
    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.SINGLE
    assert repos == []


def test_detect_multi_repo(tmp_path: Path) -> None:
    for name in ("backend", "frontend"):
        repo = tmp_path / name
        repo.mkdir()
        (repo / ".git").mkdir()
    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.MULTI
    assert repos == ["backend", "frontend"]


def test_detect_multi_repo_ignores_hidden_dirs(tmp_path: Path) -> None:
    """Hidden directories should not count as repos."""
    for name in ("backend", "frontend"):
        repo = tmp_path / name
        repo.mkdir()
        (repo / ".git").mkdir()
    hidden = tmp_path / ".cache"
    hidden.mkdir()
    (hidden / ".git").mkdir()

    project_type, repos = detect_project_type(tmp_path)
    assert project_type == ProjectType.MULTI
    assert ".cache" not in repos


# --- Task step detection (file-based fallback, no metadata) ---


def test_detect_task_step_empty(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    assert detect_task_step(task_dir) == TaskStep.PRODUCT


def test_detect_task_step_spec(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "spec.md").write_text("")
    assert detect_task_step(task_dir) == TaskStep.ARCHITECT


def test_detect_task_step_system_analysis(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "spec.md").write_text("")
    (task_dir / "system-analysis.md").write_text("")
    assert detect_task_step(task_dir) == TaskStep.PLANNER


def test_detect_task_step_multi_plan(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "spec.md").write_text("")
    (task_dir / "system-analysis.md").write_text("")
    (task_dir / "multi-plan.md").write_text("")
    assert detect_task_step(task_dir) == TaskStep.DEV


def test_detect_task_step_qa_input(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "qa-input.md").write_text("")
    assert detect_task_step(task_dir) == TaskStep.QA


def test_detect_task_step_done(tmp_path: Path) -> None:
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "qa-session.md").write_text("")
    assert detect_task_step(task_dir) == TaskStep.DONE


# --- Task step detection with metadata routing (loops) ---


def test_detect_task_step_routing_overrides_files(tmp_path: Path) -> None:
    """Metadata routing takes priority over file-based detection."""
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "qa-session.md").write_text("")
    meta = {"created_at": "2026-01-01T00:00:00+00:00", "sessions": {}, "last_routing_next": "dev"}
    (task_dir / "task-metadata.json").write_text(json.dumps(meta))
    assert detect_task_step(task_dir) == TaskStep.DEV


def test_detect_task_step_routing_pipeline_falls_through(tmp_path: Path) -> None:
    """Routing 'pipeline' falls through to file-based detection."""
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "qa-input.md").write_text("")
    meta = {
        "created_at": "2026-01-01T00:00:00+00:00",
        "sessions": {},
        "last_routing_next": "pipeline",
    }
    (task_dir / "task-metadata.json").write_text(json.dumps(meta))
    assert detect_task_step(task_dir) == TaskStep.QA


def test_detect_task_step_routing_done(tmp_path: Path) -> None:
    """Routing 'done' returns DONE regardless of files."""
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "qa-input.md").write_text("")
    meta = {
        "created_at": "2026-01-01T00:00:00+00:00",
        "sessions": {},
        "last_routing_next": "done",
    }
    (task_dir / "task-metadata.json").write_text(json.dumps(meta))
    assert detect_task_step(task_dir) == TaskStep.DONE


def test_detect_task_step_no_routing_falls_to_files(tmp_path: Path) -> None:
    """No routing in metadata → file-based detection."""
    task_dir = tmp_path / "my-task"
    task_dir.mkdir()
    (task_dir / "spec.md").write_text("")
    meta = {
        "created_at": "2026-01-01T00:00:00+00:00",
        "sessions": {},
        "last_routing_next": None,
    }
    (task_dir / "task-metadata.json").write_text(json.dumps(meta))
    assert detect_task_step(task_dir) == TaskStep.ARCHITECT


# --- scan_tasks ---


def test_scan_tasks_no_tasks_dir(tmp_path: Path) -> None:
    assert scan_tasks(tmp_path) == []


def test_scan_tasks_returns_sorted(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".devamp" / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "z-task").mkdir()
    (tasks_dir / "a-task").mkdir()
    (tasks_dir / "a-task" / "spec.md").write_text("")

    tasks = scan_tasks(tmp_path)
    assert len(tasks) == 2
    assert tasks[0].name == "a-task"
    assert tasks[0].step == TaskStep.ARCHITECT
    assert tasks[1].name == "z-task"
    assert tasks[1].step == TaskStep.PRODUCT


# --- scan_project ---


def test_scan_project_empty(tmp_path: Path) -> None:
    state = scan_project(tmp_path)
    assert state.project_type == ProjectType.EMPTY
    assert state.has_domain is False
    assert state.tasks == []


def test_scan_project_with_domain(tmp_path: Path) -> None:
    domain = tmp_path / ".devamp" / "domain"
    domain.mkdir(parents=True)
    (domain / "context.md").write_text("domain info")

    state = scan_project(tmp_path)
    assert state.has_domain is True


# --- parse_roadmap ---


def _write_roadmap(tmp_path: Path, content: str) -> None:
    """Helper: write content to .devamp/domain/roadmap.md."""
    roadmap = tmp_path / ".devamp" / "domain" / "roadmap.md"
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text(content, encoding="utf-8")


def test_parse_roadmap_happy_path(tmp_path: Path) -> None:
    """Three epics with different statuses are all parsed correctly."""
    _write_roadmap(
        tmp_path,
        """\
# devamp — Roadmap

## Alpha feature
Status: planned

Some description here.

## Beta feature
Status: in-progress

Another description.

## Gamma feature
Status: done

Completed work.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 3

    assert epics[0].name == "Alpha feature"
    assert epics[0].status == "planned"
    assert "Some description here." in epics[0].content
    assert epics[0].content.startswith("## Alpha feature")

    assert epics[1].name == "Beta feature"
    assert epics[1].status == "in-progress"

    assert epics[2].name == "Gamma feature"
    assert epics[2].status == "done"


def test_parse_roadmap_missing_file(tmp_path: Path) -> None:
    """No roadmap.md → empty list, no exception."""
    assert parse_roadmap(tmp_path) == []


def test_parse_roadmap_empty_file(tmp_path: Path) -> None:
    """Empty roadmap.md → empty list."""
    _write_roadmap(tmp_path, "")
    assert parse_roadmap(tmp_path) == []


def test_parse_roadmap_h2_without_status(tmp_path: Path) -> None:
    """H2 section without Status: line is skipped."""
    _write_roadmap(
        tmp_path,
        """\
## Has status
Status: planned

Description.

## No status

Just text, no status line.

## Also has status
Status: done

Done stuff.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 2
    assert epics[0].name == "Has status"
    assert epics[1].name == "Also has status"


def test_parse_roadmap_all_done(tmp_path: Path) -> None:
    """All epics with status done — parser returns them all (filtering is cli's job)."""
    _write_roadmap(
        tmp_path,
        """\
## Feature A
Status: done

Done.

## Feature B
Status: done

Also done.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 2
    assert all(e.status == "done" for e in epics)


def test_parse_roadmap_rich_content(tmp_path: Path) -> None:
    """Epic with bullet points, code blocks — content preserved fully."""
    _write_roadmap(
        tmp_path,
        """\
## Complex epic
Status: planned

Key points:
- bullet one
- bullet two

```python
def hello():
    pass
```

More text after code block.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 1
    assert "- bullet one" in epics[0].content
    assert "```python" in epics[0].content
    assert "More text after code block." in epics[0].content


def test_parse_roadmap_status_with_blank_line_after_h2(tmp_path: Path) -> None:
    """Status: can be separated from H2 by a blank line (within 3 non-blank lines)."""
    _write_roadmap(
        tmp_path,
        """\
## Spaced epic

Status: in-progress

Description.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 1
    assert epics[0].status == "in-progress"


def test_parse_roadmap_status_case_insensitive(tmp_path: Path) -> None:
    """Status line matching is case-insensitive."""
    _write_roadmap(
        tmp_path,
        """\
## Case test
status: Planned

Desc.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 1
    assert epics[0].status == "planned"


def test_parse_roadmap_preamble_ignored(tmp_path: Path) -> None:
    """Text before first H2 (preamble like H1 title) is ignored."""
    _write_roadmap(
        tmp_path,
        """\
# My Project Roadmap

Some intro text.

## First epic
Status: planned

Description.
""",
    )
    epics = parse_roadmap(tmp_path)
    assert len(epics) == 1
    assert epics[0].name == "First epic"
