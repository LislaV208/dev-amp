"""Tests for pipeline module — step ordering and skip logic."""

from __future__ import annotations

from devamp.pipeline import (
    AGENT_EXPECTED_OUTPUT,
    STEP_EXPECTED_OUTPUT,
    STEP_TO_AGENT,
    get_next_step,
    get_pipeline,
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


def test_single_pipeline_skips_architect_and_planner() -> None:
    pipeline = get_pipeline(ProjectType.SINGLE)
    assert TaskStep.ARCHITECT not in pipeline
    assert TaskStep.PLANNER not in pipeline
    assert pipeline == [
        TaskStep.PRODUCT,
        TaskStep.DEV,
        TaskStep.QA,
        TaskStep.DONE,
    ]


def test_empty_pipeline_same_as_single() -> None:
    assert get_pipeline(ProjectType.EMPTY) == get_pipeline(ProjectType.SINGLE)


# --- resolve_step ---


def test_resolve_step_multi_keeps_all_steps() -> None:
    for step in [TaskStep.PRODUCT, TaskStep.ARCHITECT, TaskStep.PLANNER, TaskStep.DEV]:
        assert resolve_step(step, ProjectType.MULTI) == step


def test_resolve_step_single_skips_architect_to_dev() -> None:
    result = resolve_step(TaskStep.ARCHITECT, ProjectType.SINGLE)
    assert result == TaskStep.DEV


def test_resolve_step_single_skips_planner_to_dev() -> None:
    result = resolve_step(TaskStep.PLANNER, ProjectType.SINGLE)
    assert result == TaskStep.DEV


def test_resolve_step_single_keeps_product() -> None:
    assert resolve_step(TaskStep.PRODUCT, ProjectType.SINGLE) == TaskStep.PRODUCT


def test_resolve_step_single_keeps_qa() -> None:
    assert resolve_step(TaskStep.QA, ProjectType.SINGLE) == TaskStep.QA


def test_resolve_step_done_stays_done() -> None:
    assert resolve_step(TaskStep.DONE, ProjectType.SINGLE) == TaskStep.DONE
    assert resolve_step(TaskStep.DONE, ProjectType.MULTI) == TaskStep.DONE


# --- get_next_step ---


def test_get_next_step_single_product_to_dev() -> None:
    assert get_next_step(TaskStep.PRODUCT, ProjectType.SINGLE) == TaskStep.DEV


def test_get_next_step_single_dev_to_qa() -> None:
    assert get_next_step(TaskStep.DEV, ProjectType.SINGLE) == TaskStep.QA


def test_get_next_step_single_qa_to_done() -> None:
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
