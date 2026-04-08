"""Build initial message per agent based on pipeline state."""

from __future__ import annotations

from .metadata import load_metadata
from .scanner import DOMAIN_DIR, ProjectState, TaskState, TaskStep


def build_initial_message(
    task: TaskState,
    project_state: ProjectState,
) -> str | None:
    """Build initial message for the agent about to be launched.

    Includes delegation context when the task was routed by another agent
    (not the default pipeline flow).
    """
    base = _base_message(task, project_state)
    delegation = _delegation_context(task)

    if delegation and base:
        return f"{delegation}\n\n{base}"
    if delegation:
        return delegation
    return base


def _base_message(task: TaskState, project_state: ProjectState) -> str | None:
    """Build the standard initial message for a step."""
    step = task.step
    task_dir = str(task.path)

    if step == TaskStep.PRODUCT:
        if project_state.has_domain:
            return f"Domain: {DOMAIN_DIR}/"
        return None

    if step == TaskStep.ARCHITECT:
        repos_str = ", ".join(project_state.repos)
        return f"Spec: {task_dir}/spec.md. Repos: {repos_str}"

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
