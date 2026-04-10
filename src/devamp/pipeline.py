"""Pipeline step ordering and skip logic."""

from __future__ import annotations

from .scanner import ProjectType, TaskStep

# Full pipeline order (multi-repo): product → architect → planner → dev → qa → done
FULL_PIPELINE: list[TaskStep] = [
    TaskStep.PRODUCT,
    TaskStep.ARCHITECT,
    TaskStep.PLANNER,
    TaskStep.DEV,
    TaskStep.QA,
    TaskStep.DONE,
]


def get_pipeline(project_type: ProjectType) -> list[TaskStep]:
    """Return ordered pipeline steps for a given project type.

    All project types use the full pipeline: product → architect → planner → dev → qa → done.
    """
    return list(FULL_PIPELINE)


def resolve_step(current_step: TaskStep, project_type: ProjectType) -> TaskStep:
    """Resolve the actual next step.

    Safety net: if the step is somehow not in the pipeline, skip forward
    to the next valid step.
    """
    pipeline = get_pipeline(project_type)

    if current_step in pipeline:
        return current_step

    # Step is not in this pipeline — skip forward (safety net)
    full_idx = FULL_PIPELINE.index(current_step)
    for step in FULL_PIPELINE[full_idx + 1 :]:
        if step in pipeline:
            return step

    return TaskStep.DONE


def get_next_step(current_step: TaskStep, project_type: ProjectType) -> TaskStep:
    """Get the default next pipeline step after the current one."""
    pipeline = get_pipeline(project_type)
    try:
        idx = pipeline.index(current_step)
        if idx + 1 < len(pipeline):
            return pipeline[idx + 1]
    except ValueError:
        pass
    return TaskStep.DONE


# Map step → agent file name (without .md)
STEP_TO_AGENT: dict[TaskStep, str] = {
    TaskStep.PRODUCT: "product",
    TaskStep.ARCHITECT: "architect",
    TaskStep.PLANNER: "planner",
    TaskStep.DEV: "dev",
    TaskStep.QA: "qa",
}

# Reverse: agent name → expected output file
AGENT_EXPECTED_OUTPUT: dict[str, str] = {
    "product": "spec.md",
    "architect": "system-analysis.md",
    "planner": "multi-plan.md",
    "dev": "qa-input.md",
    "qa": "qa-session.md",
}

# Expected output file per step (for verification after agent session)
STEP_EXPECTED_OUTPUT: dict[TaskStep, str] = {
    TaskStep.PRODUCT: "spec.md",
    TaskStep.ARCHITECT: "system-analysis.md",
    TaskStep.PLANNER: "multi-plan.md",
    TaskStep.DEV: "qa-input.md",
    TaskStep.QA: "qa-session.md",
}

# All agent names (for agent picker — independent of project type)
ALL_AGENTS: list[str] = ["product", "architect", "planner", "dev", "qa"]

# Agent name → pipeline step (reverse of STEP_TO_AGENT)
AGENT_TO_STEP: dict[str, TaskStep] = {v: k for k, v in STEP_TO_AGENT.items()}


def is_before_step(agent_name: str, current_step: TaskStep, project_type: ProjectType) -> bool:
    """Check if an agent is earlier in the pipeline than the current step.

    Used to detect re-entry — when a user picks an agent that's before
    the task's current position in the pipeline.
    """
    pipeline = get_pipeline(project_type)
    agent_step = AGENT_TO_STEP.get(agent_name)
    if agent_step is None or agent_step not in pipeline or current_step not in pipeline:
        return False
    return pipeline.index(agent_step) < pipeline.index(current_step)


def get_downstream_agents(agent_name: str, project_type: ProjectType) -> list[str]:
    """Get list of agent names downstream from the given agent in the pipeline.

    Returns agents between the given agent and DONE (exclusive of both).
    Used for cascade after re-entry.
    """
    pipeline = get_pipeline(project_type)
    agent_step = AGENT_TO_STEP.get(agent_name)
    if agent_step is None or agent_step not in pipeline:
        return []
    idx = pipeline.index(agent_step)
    downstream_steps = [s for s in pipeline[idx + 1 :] if s != TaskStep.DONE]
    return [STEP_TO_AGENT[s] for s in downstream_steps if s in STEP_TO_AGENT]
