"""Project type detection and task state reading."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

DEVAMP_DIR = ".devamp"
TASKS_DIR = f"{DEVAMP_DIR}/tasks"
DOMAIN_DIR = f"{DEVAMP_DIR}/domain"


class ProjectType(Enum):
    EMPTY = "empty"
    SINGLE = "single-repo"
    MULTI = "multi-repo"


class TaskStep(Enum):
    """Current pipeline step for a task — what should run next."""

    PRODUCT = "product"
    DEV_SYSTEM = "dev-system"
    DEV_MULTI = "dev-multi"
    DEV_SINGLE = "dev-single"
    QA = "qa"
    DONE = "done"


@dataclass
class TaskState:
    name: str
    step: TaskStep
    path: Path


@dataclass
class ProjectState:
    project_type: ProjectType
    has_domain: bool
    tasks: list[TaskState] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)


def detect_project_type(cwd: Path) -> tuple[ProjectType, list[str]]:
    """Detect project type based on CWD structure.

    Returns (project_type, list_of_repo_names).
    """
    children = [p for p in cwd.iterdir() if p.is_dir() and not p.name.startswith(".")]

    if not children and not any(cwd.iterdir()):
        return ProjectType.EMPTY, []

    # Check for multiple subdirs with .git
    git_repos = [p.name for p in children if (p / ".git").is_dir()]
    if len(git_repos) >= 2:
        return ProjectType.MULTI, sorted(git_repos)

    return ProjectType.SINGLE, []


def detect_task_step(task_dir: Path) -> TaskStep:
    """Determine current pipeline step from file presence in task directory."""
    if (task_dir / "qa-session.md").exists():
        return TaskStep.DONE
    if (task_dir / "qa-input.md").exists():
        return TaskStep.QA
    if (task_dir / "multi-plan.md").exists():
        return TaskStep.DEV_SINGLE
    if (task_dir / "system-analysis.md").exists():
        return TaskStep.DEV_MULTI
    if (task_dir / "spec.md").exists():
        return TaskStep.DEV_SYSTEM
    return TaskStep.PRODUCT


def scan_tasks(cwd: Path) -> list[TaskState]:
    """Read all task states from .devamp/tasks/."""
    tasks_dir = cwd / TASKS_DIR
    if not tasks_dir.is_dir():
        return []

    tasks = []
    for task_dir in sorted(tasks_dir.iterdir()):
        if task_dir.is_dir():
            step = detect_task_step(task_dir)
            tasks.append(TaskState(name=task_dir.name, step=step, path=task_dir))
    return tasks


def scan_project(cwd: Path | None = None) -> ProjectState:
    """Full project scan — type + domain + tasks."""
    if cwd is None:
        cwd = Path.cwd()

    project_type, repos = detect_project_type(cwd)
    has_domain = (cwd / DOMAIN_DIR).is_dir() and any((cwd / DOMAIN_DIR).iterdir())
    tasks = scan_tasks(cwd)

    return ProjectState(
        project_type=project_type,
        has_domain=has_domain,
        tasks=tasks,
        repos=repos,
    )
