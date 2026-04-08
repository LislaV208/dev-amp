"""Pipeline step ordering and skip logic."""

from __future__ import annotations

from .scanner import ProjectType, TaskStep

# Full pipeline order (multi-repo)
FULL_PIPELINE: list[TaskStep] = [
    TaskStep.PRODUCT,
    TaskStep.DEV_SYSTEM,
    TaskStep.DEV_MULTI,
    TaskStep.DEV_SINGLE,
    TaskStep.QA,
    TaskStep.DONE,
]

# Steps to skip for single-repo projects
SINGLE_REPO_SKIP = {TaskStep.DEV_SYSTEM, TaskStep.DEV_MULTI}


def get_pipeline(project_type: ProjectType) -> list[TaskStep]:
    """Return ordered pipeline steps for a given project type."""
    if project_type == ProjectType.MULTI:
        return FULL_PIPELINE

    # Single-repo and empty: skip dev-system and dev-multi
    return [s for s in FULL_PIPELINE if s not in SINGLE_REPO_SKIP]


def resolve_step(current_step: TaskStep, project_type: ProjectType) -> TaskStep:
    """Resolve the actual next step, accounting for skip logic.

    For single-repo: if task state points to dev-system or dev-multi,
    skip forward to dev-single.
    """
    pipeline = get_pipeline(project_type)

    if current_step in pipeline:
        return current_step

    # Step is not in this pipeline (e.g. dev-system for single-repo) — skip forward
    # Find the next valid step after the skipped one
    full_idx = FULL_PIPELINE.index(current_step)
    for step in FULL_PIPELINE[full_idx + 1 :]:
        if step in pipeline:
            return step

    return TaskStep.DONE


# Map step → agent file name (without .md)
STEP_TO_AGENT: dict[TaskStep, str] = {
    TaskStep.PRODUCT: "product",
    TaskStep.DEV_SYSTEM: "developer-system",
    TaskStep.DEV_MULTI: "developer-multi",
    TaskStep.DEV_SINGLE: "developer-single",
    TaskStep.QA: "qa",
}

# Expected output file per step (for verification after agent session)
STEP_EXPECTED_OUTPUT: dict[TaskStep, str] = {
    TaskStep.PRODUCT: "spec.md",
    TaskStep.DEV_SYSTEM: "system-analysis.md",
    TaskStep.DEV_MULTI: "multi-plan.md",
    TaskStep.DEV_SINGLE: "qa-input.md",
    TaskStep.QA: "qa-session.md",
}
