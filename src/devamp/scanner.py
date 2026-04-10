"""Project type detection and task state reading."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

DEVAMP_DIR = ".devamp"
TASKS_DIR = f"{DEVAMP_DIR}/tasks"
DOMAIN_DIR = f"{DEVAMP_DIR}/domain"
ROADMAP_FILE = f"{DOMAIN_DIR}/roadmap.md"


class ProjectType(Enum):
    EMPTY = "empty"
    SINGLE = "single-repo"
    MULTI = "multi-repo"


class TaskStep(Enum):
    """Current pipeline step for a task — what should run next."""

    PRODUCT = "product"
    ARCHITECT = "architect"
    PLANNER = "planner"
    DEV = "dev"
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


@dataclass
class RoadmapEpic:
    """A single epic parsed from roadmap.md."""

    name: str  # H2 heading (without "## ")
    status: str  # "planned" | "in-progress" | "done"
    content: str  # full section text (from H2 to next H2 or EOF, inclusive)


def parse_roadmap(cwd: Path) -> list[RoadmapEpic]:
    """Parse roadmap.md into a list of epics.

    Reads ``{cwd}/.devamp/domain/roadmap.md``, splits on H2 headings and
    extracts ``Status: <value>`` from the first 3 lines after each heading.

    Returns an empty list when the file is missing, empty, or contains no
    valid epics. Sections without a ``Status:`` line are silently skipped.
    """
    roadmap_path = cwd / ROADMAP_FILE
    if not roadmap_path.is_file():
        return []

    text = roadmap_path.read_text(encoding="utf-8")
    if not text.strip():
        return []

    # Split into sections by H2 headings.  re.split keeps the delimiter when
    # wrapped in a capturing group, so we get: [preamble, "## X", body, "## Y", body, ...]
    parts = re.split(r"^(## .+)$", text, flags=re.MULTILINE)

    epics: list[RoadmapEpic] = []
    # parts[0] is text before the first H2 (preamble) — skip it
    # Then pairs: parts[1]=heading, parts[2]=body, parts[3]=heading, parts[4]=body, …
    for i in range(1, len(parts), 2):
        heading = parts[i]  # e.g. "## Nazwa epiku"
        body = parts[i + 1] if i + 1 < len(parts) else ""

        epic_name = heading.removeprefix("## ").strip()

        # Look for "Status: <value>" in the first 3 non-empty lines of the body
        status = _extract_status(body, max_lines=3)
        if status is None:
            continue

        # content = full section including the H2 line
        content = (heading + body).strip()
        epics.append(RoadmapEpic(name=epic_name, status=status, content=content))

    return epics


def _extract_status(body: str, max_lines: int = 3) -> str | None:
    """Extract status value from the first *max_lines* non-blank lines of *body*."""
    count = 0
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        count += 1
        if count > max_lines:
            break
        match = re.match(r"^Status:\s*(.+)$", stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()
    return None


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
    """Determine current pipeline step for a task.

    Priority:
    1. Routing from metadata (last_routing_next) — handles loops (e.g. QA → dev)
    2. File-based detection — fallback when no metadata routing exists

    Routing from metadata is set by devamp after parsing ## Routing from agent output.
    File-based detection is the original mechanism: presence of output files determines step.
    """
    from .metadata import load_metadata

    meta = load_metadata(task_dir)
    if meta.last_routing_next:
        routing = meta.last_routing_next
        if routing == "done":
            return TaskStep.DONE
        if routing == "pipeline":
            # "pipeline" means default next — fall through to file-based
            pass
        else:
            step = _agent_name_to_step(routing)
            if step is not None:
                return step

    return _detect_step_from_files(task_dir)


def _detect_step_from_files(task_dir: Path) -> TaskStep:
    """Original file-based step detection."""
    if (task_dir / "qa-session.md").exists():
        return TaskStep.DONE
    if (task_dir / "qa-input.md").exists():
        return TaskStep.QA
    if (task_dir / "multi-plan.md").exists():
        return TaskStep.DEV
    if (task_dir / "system-analysis.md").exists():
        return TaskStep.PLANNER
    if (task_dir / "spec.md").exists():
        return TaskStep.ARCHITECT
    return TaskStep.PRODUCT


def _agent_name_to_step(agent_name: str) -> TaskStep | None:
    """Convert agent name string to TaskStep."""
    mapping = {
        "product": TaskStep.PRODUCT,
        "architect": TaskStep.ARCHITECT,
        "planner": TaskStep.PLANNER,
        "dev": TaskStep.DEV,
        "qa": TaskStep.QA,
    }
    return mapping.get(agent_name)


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
    has_domain = (cwd / DOMAIN_DIR).is_dir() and any((cwd / DOMAIN_DIR).glob("*.md"))
    tasks = scan_tasks(cwd)

    return ProjectState(
        project_type=project_type,
        has_domain=has_domain,
        tasks=tasks,
        repos=repos,
    )
