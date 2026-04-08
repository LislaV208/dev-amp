"""Tests for pipeline module — step ordering and skip logic."""

from __future__ import annotations

from devamp.pipeline import (
    STEP_EXPECTED_OUTPUT,
    STEP_TO_AGENT,
    get_pipeline,
    resolve_step,
)
from devamp.scanner import ProjectType, TaskStep

# --- get_pipeline ---


def test_full_pipeline_for_multi() -> None:
    pipeline = get_pipeline(ProjectType.MULTI)
    assert pipeline == [
        TaskStep.PRODUCT,
        TaskStep.DEV_SYSTEM,
        TaskStep.DEV_MULTI,
        TaskStep.DEV_SINGLE,
        TaskStep.QA,
        TaskStep.DONE,
    ]


def test_single_pipeline_skips_system_and_multi() -> None:
    pipeline = get_pipeline(ProjectType.SINGLE)
    assert TaskStep.DEV_SYSTEM not in pipeline
    assert TaskStep.DEV_MULTI not in pipeline
    assert pipeline == [
        TaskStep.PRODUCT,
        TaskStep.DEV_SINGLE,
        TaskStep.QA,
        TaskStep.DONE,
    ]


def test_empty_pipeline_same_as_single() -> None:
    assert get_pipeline(ProjectType.EMPTY) == get_pipeline(ProjectType.SINGLE)


# --- resolve_step ---


def test_resolve_step_multi_keeps_all_steps() -> None:
    for step in [TaskStep.PRODUCT, TaskStep.DEV_SYSTEM, TaskStep.DEV_MULTI, TaskStep.DEV_SINGLE]:
        assert resolve_step(step, ProjectType.MULTI) == step


def test_resolve_step_single_skips_dev_system_to_dev_single() -> None:
    result = resolve_step(TaskStep.DEV_SYSTEM, ProjectType.SINGLE)
    assert result == TaskStep.DEV_SINGLE


def test_resolve_step_single_skips_dev_multi_to_dev_single() -> None:
    result = resolve_step(TaskStep.DEV_MULTI, ProjectType.SINGLE)
    assert result == TaskStep.DEV_SINGLE


def test_resolve_step_single_keeps_product() -> None:
    assert resolve_step(TaskStep.PRODUCT, ProjectType.SINGLE) == TaskStep.PRODUCT


def test_resolve_step_single_keeps_qa() -> None:
    assert resolve_step(TaskStep.QA, ProjectType.SINGLE) == TaskStep.QA


def test_resolve_step_done_stays_done() -> None:
    assert resolve_step(TaskStep.DONE, ProjectType.SINGLE) == TaskStep.DONE
    assert resolve_step(TaskStep.DONE, ProjectType.MULTI) == TaskStep.DONE


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
