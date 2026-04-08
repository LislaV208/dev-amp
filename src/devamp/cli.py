"""Typer entry point — routes: devamp (dashboard), devamp --resume."""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .context import build_initial_message
from .launcher import launch_agent
from .pipeline import (
    STEP_EXPECTED_OUTPUT,
    STEP_TO_AGENT,
    resolve_step,
)
from .scanner import (
    DOMAIN_DIR,
    TASKS_DIR,
    ProjectState,
    ProjectType,
    TaskState,
    TaskStep,
    scan_project,
    scan_tasks,
)

app = typer.Typer(add_completion=False)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"devamp {__version__}")
        raise typer.Exit()


def _print_dashboard(state: ProjectState) -> None:
    """Print project dashboard."""
    type_label = state.project_type.value
    if state.repos:
        type_label += f" ({', '.join(state.repos)})"
    typer.echo(f"📁 Project: {type_label}")
    typer.echo()

    active = [t for t in state.tasks if t.step != TaskStep.DONE]
    done = [t for t in state.tasks if t.step == TaskStep.DONE]

    if active:
        typer.echo("Active tasks:")
        for t in active:
            step = resolve_step(t.step, state.project_type)
            typer.echo(f"  {t.name}  [{step.value}]")
    else:
        typer.echo("Active tasks: (none)")

    typer.echo()
    if done:
        typer.echo("Done:")
        for t in done:
            typer.echo(f"  {t.name}")
    else:
        typer.echo("Done: (none)")
    typer.echo()


def _select_task(active: list[TaskState], project_type: ProjectType) -> TaskState | None:
    """Let user select from multiple active tasks."""
    typer.echo("Select task to continue:")
    for i, t in enumerate(active, 1):
        step = resolve_step(t.step, project_type)
        typer.echo(f"  {i}. {t.name}  [{step.value}]")
    typer.echo()

    choice = typer.prompt("Task number", type=int)
    if 1 <= choice <= len(active):
        return active[choice - 1]

    typer.echo("Invalid choice.")
    return None


def _run_discovery(cwd: Path, state: ProjectState) -> None:
    """Run discovery agent for empty projects."""
    while True:
        typer.echo("🔍 Empty project — starting discovery agent...")
        typer.echo()

        exit_code = launch_agent("discovery")

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")
            return

        # Verify: at least 1 .md file in .devamp/domain/
        domain_dir = cwd / DOMAIN_DIR
        if domain_dir.is_dir() and any(domain_dir.glob("*.md")):
            typer.echo("✅ Discovery complete — domain files created.")
            return

        retry = typer.confirm("Agent did not produce expected output. Retry?", default=True)
        if not retry:
            return


def _run_agent_for_task(
    task: TaskState,
    state: ProjectState,
    cwd: Path,
) -> None:
    """Run the appropriate agent for a task's current step."""
    step = resolve_step(task.step, state.project_type)

    if step == TaskStep.DONE:
        typer.echo(f"Task '{task.name}' is already done.")
        return

    while True:
        agent_name = STEP_TO_AGENT[step]
        initial_message = build_initial_message(
            TaskState(name=task.name, step=step, path=task.path),
            state,
        )

        typer.echo(f"🚀 Launching {agent_name} for '{task.name}'...")
        typer.echo()

        # For multi-repo, give agent access to all repo directories
        add_dirs = None
        if state.project_type == ProjectType.MULTI and state.repos:
            add_dirs = [str(cwd / repo) for repo in state.repos]

        exit_code = launch_agent(agent_name, initial_message, add_dirs)

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")

        # Verify expected output — retry loop ends when output exists or user declines
        if not _should_retry(task, step, cwd, state):
            return


def _should_retry(
    task: TaskState,
    step: TaskStep,
    cwd: Path,
    state: ProjectState,
) -> bool:
    """Check expected output. Return True if agent should be retried."""
    expected_file = STEP_EXPECTED_OUTPUT.get(step)
    if not expected_file:
        return False

    output_path = task.path / expected_file

    if output_path.exists():
        typer.echo(f"✅ {expected_file} created.")

        # Check for new task directories (product agent creates the task dir)
        if step == TaskStep.PRODUCT:
            _check_new_tasks(cwd, state)
        return False

    # Maybe the agent created a new task directory (product agent flow)
    if step == TaskStep.PRODUCT and _check_new_tasks(cwd, state):
        return False

    return typer.confirm("Agent did not produce expected output. Retry?", default=True)


def _check_new_tasks(cwd: Path, state: ProjectState) -> bool:
    """Check for newly created task directories after an agent session."""
    current_tasks = scan_tasks(cwd)
    existing_names = {t.name for t in state.tasks}
    new_tasks = [t for t in current_tasks if t.name not in existing_names]

    if new_tasks:
        for t in new_tasks:
            cont = typer.confirm(f"Task created: {t.name}. Continue?", default=True)
            if cont:
                # Re-scan and continue with the new task
                new_state = scan_project(cwd)
                new_task = next((tt for tt in new_state.tasks if tt.name == t.name), None)
                if new_task:
                    _run_agent_for_task(new_task, new_state, cwd)
        return True

    return False


def _get_most_recent_task(tasks: list[TaskState]) -> TaskState | None:
    """Get the most recently modified active task."""
    active = [t for t in tasks if t.step != TaskStep.DONE]
    if not active:
        return None

    # Sort by modification time of task directory (most recent first)
    return max(active, key=lambda t: t.path.stat().st_mtime)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version", callback=_version_callback, is_eager=True,
    ),
    resume: bool = typer.Option(False, "--resume", help="Resume most recent active task"),
) -> None:
    """devamp — AI agent pipeline orchestrator."""
    cwd = Path.cwd()
    state = scan_project(cwd)

    if resume:
        task = _get_most_recent_task(state.tasks)
        if task:
            _run_agent_for_task(task, state, cwd)
        else:
            typer.echo("No active tasks to resume.")
        return

    # Dashboard mode
    active = [t for t in state.tasks if t.step != TaskStep.DONE]

    # No tasks at all
    if not state.tasks:
        if state.project_type == ProjectType.EMPTY and not state.has_domain:
            # Empty project, no domain — start discovery
            _print_dashboard(state)
            _run_discovery(cwd, state)
            return

        if state.has_domain:
            # Has domain but no tasks — launch product agent
            _print_dashboard(state)
            typer.echo("No tasks. Starting new task...")
            typer.echo()

            # Product agent will create the task directory
            # We launch it without a task context — it will create one
            tasks_dir = cwd / TASKS_DIR
            tasks_dir.mkdir(parents=True, exist_ok=True)

            launch_agent(
                "product",
                f"Domain: {DOMAIN_DIR}/" if state.has_domain else None,
            )
            _check_new_tasks(cwd, state)
            return

        # Single/multi repo without domain — go straight to product
        _print_dashboard(state)
        typer.echo("No tasks. Starting new task...")
        typer.echo()

        tasks_dir = cwd / TASKS_DIR
        tasks_dir.mkdir(parents=True, exist_ok=True)

        launch_agent("product")
        _check_new_tasks(cwd, state)
        return

    # Print dashboard
    _print_dashboard(state)

    if not active:
        typer.echo("All tasks are done.")
        return

    if len(active) == 1:
        task = active[0]
        step = resolve_step(task.step, state.project_type)
        cont = typer.confirm(
            f'Continue "{task.name}" [{step.value}]?',
            default=True,
        )
        if cont:
            _run_agent_for_task(task, state, cwd)
    else:
        task = _select_task(active, state.project_type)
        if task:
            _run_agent_for_task(task, state, cwd)
