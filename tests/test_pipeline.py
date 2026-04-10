"""Tests for pipeline module — step ordering and skip logic."""

from __future__ import annotations

from devamp.pipeline import (
    AGENT_EXPECTED_OUTPUT,
    STEP_EXPECTED_OUTPUT,
    STEP_TO_AGENT,
    get_downstream_agents,
    get_next_step,
    get_pipeline,
    is_before_step,
    resolve_step,
)
from devamp.scanner import ProjectType, TaskStep

# --- get_pipeline ---


def test_full_pipeline_for_multi() -> None:
    pipeline = get_pipeline(ProjectType.MULTI)
    assert pipeline == [
        TaskStep.PRODUCT,
        TaskStep.ARCHITECT,
        TaskStep.PLANNER,
        TaskStep.DEV,
        TaskStep.QA,
        TaskStep.DONE,
    ]


def test_single_pipeline_is_full() -> None:
    """Single-repo projects now use full pipeline (no skip)."""
    pipeline = get_pipeline(ProjectType.SINGLE)
    assert pipeline == [
        TaskStep.PRODUCT,
        TaskStep.ARCHITECT,
        TaskStep.PLANNER,
        TaskStep.DEV,
        TaskStep.QA,
        TaskStep.DONE,
    ]


def test_empty_pipeline_same_as_single() -> None:
    assert get_pipeline(ProjectType.EMPTY) == get_pipeline(ProjectType.SINGLE)


def test_all_project_types_same_pipeline() -> None:
    """All project types use the same full pipeline."""
    assert get_pipeline(ProjectType.SINGLE) == get_pipeline(ProjectType.MULTI)
    assert get_pipeline(ProjectType.EMPTY) == get_pipeline(ProjectType.MULTI)


# --- resolve_step ---


def test_resolve_step_multi_keeps_all_steps() -> None:
    for step in [TaskStep.PRODUCT, TaskStep.ARCHITECT, TaskStep.PLANNER, TaskStep.DEV]:
        assert resolve_step(step, ProjectType.MULTI) == step


def test_resolve_step_single_keeps_architect() -> None:
    """Architect is now part of single-repo pipeline."""
    assert resolve_step(TaskStep.ARCHITECT, ProjectType.SINGLE) == TaskStep.ARCHITECT


def test_resolve_step_single_keeps_planner() -> None:
    """Planner is now part of single-repo pipeline."""
    assert resolve_step(TaskStep.PLANNER, ProjectType.SINGLE) == TaskStep.PLANNER


def test_resolve_step_single_keeps_product() -> None:
    assert resolve_step(TaskStep.PRODUCT, ProjectType.SINGLE) == TaskStep.PRODUCT


def test_resolve_step_single_keeps_qa() -> None:
    assert resolve_step(TaskStep.QA, ProjectType.SINGLE) == TaskStep.QA


def test_resolve_step_done_stays_done() -> None:
    assert resolve_step(TaskStep.DONE, ProjectType.SINGLE) == TaskStep.DONE
    assert resolve_step(TaskStep.DONE, ProjectType.MULTI) == TaskStep.DONE


# --- get_next_step ---


def test_get_next_step_single_full_sequence() -> None:
    """Single-repo now follows full pipeline like multi."""
    assert get_next_step(TaskStep.PRODUCT, ProjectType.SINGLE) == TaskStep.ARCHITECT
    assert get_next_step(TaskStep.ARCHITECT, ProjectType.SINGLE) == TaskStep.PLANNER
    assert get_next_step(TaskStep.PLANNER, ProjectType.SINGLE) == TaskStep.DEV
    assert get_next_step(TaskStep.DEV, ProjectType.SINGLE) == TaskStep.QA
    assert get_next_step(TaskStep.QA, ProjectType.SINGLE) == TaskStep.DONE


def test_get_next_step_multi_full_sequence() -> None:
    assert get_next_step(TaskStep.PRODUCT, ProjectType.MULTI) == TaskStep.ARCHITECT
    assert get_next_step(TaskStep.ARCHITECT, ProjectType.MULTI) == TaskStep.PLANNER
    assert get_next_step(TaskStep.PLANNER, ProjectType.MULTI) == TaskStep.DEV
    assert get_next_step(TaskStep.DEV, ProjectType.MULTI) == TaskStep.QA
    assert get_next_step(TaskStep.QA, ProjectType.MULTI) == TaskStep.DONE


def test_get_next_step_done_stays_done() -> None:
    assert get_next_step(TaskStep.DONE, ProjectType.SINGLE) == TaskStep.DONE


# --- Mappings completeness ---


def test_all_non_done_steps_have_agent() -> None:
    """Every actionable step should map to an agent."""
    for step in TaskStep:
        if step != TaskStep.DONE:
            assert step in STEP_TO_AGENT, f"Missing agent for {step}"


def test_all_non_done_steps_have_expected_output() -> None:
    """Every actionable step should have an expected output file."""
    for step in TaskStep:
        if step != TaskStep.DONE:
            assert step in STEP_EXPECTED_OUTPUT, f"Missing expected output for {step}"


def test_agent_expected_output_covers_all_agents() -> None:
    """Every agent in STEP_TO_AGENT should have an entry in AGENT_EXPECTED_OUTPUT."""
    for agent_name in STEP_TO_AGENT.values():
        assert agent_name in AGENT_EXPECTED_OUTPUT, (
            f"Missing AGENT_EXPECTED_OUTPUT for {agent_name}"
        )


# --- is_before_step ---


def test_is_before_step_product_before_dev() -> None:
    assert is_before_step("product", TaskStep.DEV, ProjectType.SINGLE) is True


def test_is_before_step_product_before_qa() -> None:
    assert is_before_step("product", TaskStep.QA, ProjectType.SINGLE) is True


def test_is_before_step_dev_not_before_product() -> None:
    assert is_before_step("dev", TaskStep.PRODUCT, ProjectType.SINGLE) is False


def test_is_before_step_same_step() -> None:
    assert is_before_step("dev", TaskStep.DEV, ProjectType.SINGLE) is False


def test_is_before_step_multi_architect_before_dev() -> None:
    assert is_before_step("architect", TaskStep.DEV, ProjectType.MULTI) is True


def test_is_before_step_architect_before_dev_single() -> None:
    """Architect is now in single-repo pipeline, so it IS before dev."""
    assert is_before_step("architect", TaskStep.DEV, ProjectType.SINGLE) is True


# --- get_downstream_agents ---


def test_get_downstream_agents_product_single() -> None:
    """Single-repo now includes architect and planner downstream."""
    assert get_downstream_agents("product", ProjectType.SINGLE) == [
        "architect",
        "planner",
        "dev",
        "qa",
    ]


def test_get_downstream_agents_dev_single() -> None:
    assert get_downstream_agents("dev", ProjectType.SINGLE) == ["qa"]


def test_get_downstream_agents_qa_single() -> None:
    assert get_downstream_agents("qa", ProjectType.SINGLE) == []


def test_get_downstream_agents_product_multi() -> None:
    assert get_downstream_agents("product", ProjectType.MULTI) == [
        "architect",
        "planner",
        "dev",
        "qa",
    ]


def test_get_downstream_agents_architect_multi() -> None:
    assert get_downstream_agents("architect", ProjectType.MULTI) == ["planner", "dev", "qa"]
