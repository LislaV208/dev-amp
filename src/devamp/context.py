"""Build initial message per agent based on pipeline state."""

from __future__ import annotations

from .scanner import DOMAIN_DIR, ProjectState, TaskState, TaskStep


def build_initial_message(
    task: TaskState,
    project_state: ProjectState,
) -> str | None:
    """Build initial message for the agent about to be launched.

    Returns None if no initial message is needed (e.g. discovery, or first agent in pipeline).
    """
    step = task.step
    task_dir = str(task.path)

    if step == TaskStep.PRODUCT:
        if project_state.has_domain:
            return f"Domain: {DOMAIN_DIR}/"
        return None

    if step == TaskStep.DEV_SYSTEM:
        repos_str = ", ".join(project_state.repos)
        return f"Spec: {task_dir}/spec.md. Repos: {repos_str}"

    if step == TaskStep.DEV_MULTI:
        return f"System analysis: {task_dir}/system-analysis.md"

    if step == TaskStep.DEV_SINGLE:
        # If multi-plan exists, reference it; otherwise reference spec directly
        if (task.path / "multi-plan.md").exists():
            return f"Plan: {task_dir}/multi-plan.md"
        return f"Spec: {task_dir}/spec.md"

    if step == TaskStep.QA:
        return f"Handoff: {task_dir}/qa-input.md"

    return None
