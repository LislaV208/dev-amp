"""Build initial message per agent based on pipeline state."""

from __future__ import annotations

from pathlib import Path

from .metadata import load_metadata
from .pipeline import AGENT_EXPECTED_OUTPUT
from .scanner import DOMAIN_DIR, ProjectState, TaskState, TaskStep


def build_initial_message(
    task: TaskState,
    project_state: ProjectState,
    cwd: Path,
) -> str:
    """Build initial message for the agent about to be launched.

    Includes delegation context when the task was routed by another agent
    (not the default pipeline flow).

    Always returns a non-empty string (at minimum ``Project root: ...``).
    """
    root_line = f"Project root: {cwd}"
    base = _base_message(task, project_state, cwd)
    delegation = _delegation_context(task)

    parts: list[str] = [root_line]
    if delegation:
        parts.append(delegation)
    if base:
        parts.append(base)

    return "\n\n".join(parts)


def build_cascade_message(
    task: TaskState,
    project_state: ProjectState,
    upstream_agent: str,
    cwd: Path,
) -> str:
    """Build initial message for a downstream agent during cascade.

    Tells the agent that upstream artifact changed and it should update its output.
    """
    root_line = f"Project root: {cwd}"

    upstream_output = AGENT_EXPECTED_OUTPUT.get(upstream_agent)
    upstream_ref = f" ({task.path}/{upstream_output})" if upstream_output else ""

    cascade_ctx = (
        f"Upstream artifact changed{upstream_ref}. "
        f"Review the updated input and update your output accordingly."
    )

    base = _base_message(task, project_state, cwd)
    parts: list[str] = [root_line, cascade_ctx]
    if base:
        parts.append(base)

    return "\n\n".join(parts)


def _base_message(task: TaskState, project_state: ProjectState, cwd: Path) -> str | None:
    """Build the standard initial message for a step."""
    step = task.step
    task_dir = str(task.path)

    if step == TaskStep.PRODUCT:
        if project_state.has_domain:
            return f"Domain: {cwd}/{DOMAIN_DIR}/"
        return None

    if step == TaskStep.ARCHITECT:
        if project_state.repos:
            repos_str = ", ".join(project_state.repos)
            return f"Spec: {task_dir}/spec.md. Repos: {repos_str}"
        return f"Spec: {task_dir}/spec.md"

    if step == TaskStep.PLANNER:
        return f"System analysis: {task_dir}/system-analysis.md"

    if step == TaskStep.DEV:
        if (task.path / "multi-plan.md").exists():
            return f"Plan: {task_dir}/multi-plan.md"
        return f"Spec: {task_dir}/spec.md"

    if step == TaskStep.QA:
        return f"Handoff: {task_dir}/qa-input.md"

    return None


def _delegation_context(task: TaskState) -> str | None:
    """Build delegation context from metadata routing info."""
    meta = load_metadata(task.path)

    if not meta.last_routing_next or not meta.last_routing_reason:
        return None

    reason = meta.last_routing_reason
    source = _identify_source_agent(task)
    if not source:
        return None

    output_file = _agent_output_file(source, task)

    parts = [f"Delegated from {source}"]
    if output_file:
        parts[0] += f": {task.path}/{output_file}"
    parts.append(f"Reason: {reason}")

    return "\n".join(parts)


def _identify_source_agent(task: TaskState) -> str | None:
    """Identify which agent last produced output (the delegating agent)."""
    checks = [
        ("qa-session.md", "qa"),
        ("qa-input.md", "dev"),
        ("multi-plan.md", "planner"),
        ("system-analysis.md", "architect"),
        ("spec.md", "product"),
    ]
    for filename, agent in checks:
        if (task.path / filename).exists():
            return agent
    return None


def _agent_output_file(agent_name: str, task: TaskState) -> str | None:
    """Get the output filename for a given agent."""
    mapping = {
        "product": "spec.md",
        "architect": "system-analysis.md",
        "planner": "multi-plan.md",
        "dev": "qa-input.md",
        "qa": "qa-session.md",
    }
    filename = mapping.get(agent_name)
    if filename and (task.path / filename).exists():
        return filename
    return None
