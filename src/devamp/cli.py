"""Typer entry point — persistent dashboard loop with post-agent menus."""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .context import build_initial_message
from .launcher import launch_agent
from .metadata import (
    clear_routing,
    ensure_metadata,
    get_created_at,
    get_session_id,
    record_routing,
    record_session,
)
from .pipeline import (
    AGENT_EXPECTED_OUTPUT,
    ALL_AGENTS,
    STEP_TO_AGENT,
    get_next_step,
    resolve_step,
)
from .routing import ROUTING_DONE, ROUTING_PIPELINE, parse_routing
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


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def _print_dashboard(state: ProjectState) -> None:
    """Print project dashboard."""
    type_label = state.project_type.value
    if state.repos:
        type_label += f" ({', '.join(state.repos)})"
    typer.echo(f"📁 Project: {type_label}")
    typer.echo()

    active = [t for t in state.tasks if t.step != TaskStep.DONE]
    done = [t for t in state.tasks if t.step == TaskStep.DONE]

    # Sort active by mtime (newest first)
    active.sort(key=lambda t: t.path.stat().st_mtime, reverse=True)

    if active:
        typer.echo("Active tasks:")
        for i, t in enumerate(active, 1):
            step = resolve_step(t.step, state.project_type)
            agent = STEP_TO_AGENT.get(step, step.value)
            date = get_created_at(t.path)
            typer.echo(f"  {i}. {t.name}  [→ {agent}]  ({date})")
    else:
        typer.echo("Active tasks: (none)")

    typer.echo()
    if done:
        typer.echo("Done:")
        for t in done:
            date = get_created_at(t.path)
            typer.echo(f"  {t.name}  ({date})")
    else:
        typer.echo("Done: (none)")
    typer.echo()


# ---------------------------------------------------------------------------
# Agent picker
# ---------------------------------------------------------------------------


def _pick_agent() -> str | None:
    """Show full agent list and let user choose. Returns agent name or None."""
    typer.echo("Choose agent:")
    for i, name in enumerate(ALL_AGENTS, 1):
        typer.echo(f"  {i}. {name}")
    typer.echo()

    choice = typer.prompt("Agent number", type=int)
    if 1 <= choice <= len(ALL_AGENTS):
        return ALL_AGENTS[choice - 1]
    typer.echo("Invalid choice.")
    return None


# ---------------------------------------------------------------------------
# Post-agent menu
# ---------------------------------------------------------------------------


def _post_agent_menu(
    task: TaskState,
    state: ProjectState,
    agent_name: str,
    routing_next: str | None,
    routing_reason: str | None,
    expected_file: str | None,
) -> str:
    """Show post-agent menu after agent session ends.

    Returns action: "continue", "pick", "dashboard", "quit", "new_task".
    """
    has_output = expected_file and (task.path / expected_file).exists()

    # Determine recommended next
    step = resolve_step(task.step, state.project_type)
    default_next_step = get_next_step(step, state.project_type)

    if routing_next == ROUTING_DONE:
        typer.echo(f"✅ {expected_file} created. Task complete!")
        typer.echo()
        typer.echo("  [N] Start new task")
        typer.echo("  [D] Dashboard")
        typer.echo("  [Q] Quit")
        typer.echo()
        choice = typer.prompt("Choice", default="D").strip().upper()
        if choice == "N":
            return "new_task"
        if choice == "Q":
            return "quit"
        return "dashboard"

    if routing_next and routing_next not in (ROUTING_PIPELINE, ROUTING_DONE):
        # Agent recommends specific next agent
        typer.echo(f"✅ {expected_file} created.")
        typer.echo(f"{agent_name} recommends: {routing_next} — {routing_reason}")
        typer.echo()
        typer.echo(f"  [C] Continue to {routing_next} (recommended)")
        typer.echo("  [A] Choose different agent for this task")
        typer.echo("  [D] Dashboard")
        typer.echo("  [Q] Quit")
        typer.echo()
        choice = typer.prompt("Choice", default="C").strip().upper()
        if choice == "C":
            return "continue"
        if choice == "A":
            return "pick"
        if choice == "Q":
            return "quit"
        return "dashboard"

    if has_output:
        # Default pipeline flow
        if default_next_step == TaskStep.DONE:
            typer.echo(f"✅ {expected_file} created. Task complete!")
            typer.echo()
            typer.echo("  [N] Start new task")
            typer.echo("  [D] Dashboard")
            typer.echo("  [Q] Quit")
            typer.echo()
            choice = typer.prompt("Choice", default="D").strip().upper()
            if choice == "N":
                return "new_task"
            if choice == "Q":
                return "quit"
            return "dashboard"

        default_agent = STEP_TO_AGENT.get(default_next_step, default_next_step.value)
        typer.echo(f"✅ {expected_file} created.")
        typer.echo(f"Recommended next: {default_agent} (pipeline default)")
        typer.echo()
        typer.echo(f"  [C] Continue to {default_agent} (default)")
        typer.echo("  [A] Choose different agent for this task")
        typer.echo("  [D] Dashboard")
        typer.echo("  [Q] Quit")
        typer.echo()
        choice = typer.prompt("Choice", default="C").strip().upper()
        if choice == "C":
            return "continue"
        if choice == "A":
            return "pick"
        if choice == "Q":
            return "quit"
        return "dashboard"

    # No expected output — shouldn't normally reach here (retry handles it)
    return "dashboard"


# ---------------------------------------------------------------------------
# Agent execution
# ---------------------------------------------------------------------------


def _resolve_next_agent(
    task: TaskState,
    state: ProjectState,
) -> str:
    """Resolve which agent should run next for a task.

    Uses routing from metadata if available, falls back to pipeline default.
    """
    from .metadata import load_metadata

    meta = load_metadata(task.path)

    if meta.last_routing_next and meta.last_routing_next not in (
        ROUTING_PIPELINE,
        ROUTING_DONE,
    ):
        return meta.last_routing_next

    step = resolve_step(task.step, state.project_type)
    return STEP_TO_AGENT.get(step, "product")


def _run_agent_for_task(
    task: TaskState,
    state: ProjectState,
    cwd: Path,
) -> str:
    """Run agents for a task in a loop until user exits to dashboard/quit.

    Returns: "dashboard" or "quit" or "new_task".
    """
    while True:
        # Re-scan to get fresh state
        state = scan_project(cwd)
        fresh_task = next((t for t in state.tasks if t.name == task.name), None)
        if not fresh_task:
            typer.echo(f"Task '{task.name}' not found.")
            return "dashboard"
        task = fresh_task

        step = resolve_step(task.step, state.project_type)
        if step == TaskStep.DONE:
            typer.echo(f"Task '{task.name}' is already done.")
            return "dashboard"

        agent_name = _resolve_next_agent(task, state)

        # Ensure metadata exists for this task
        ensure_metadata(task.path)

        # Build initial message BEFORE clearing routing —
        # delegation context reads last_routing_next/reason from metadata
        initial_message = build_initial_message(
            TaskState(name=task.name, step=step, path=task.path),
            state,
        )

        # Clear stale routing AFTER building message so next loop iteration
        # doesn't re-use this routing
        clear_routing(task.path)

        typer.echo(f"🚀 Launching {agent_name} for '{task.name}'...")
        typer.echo()

        # Session tracking: resume if agent has a previous session on this task
        existing_session = get_session_id(task.path, agent_name)

        # For multi-repo, give agent access to all repo directories
        add_dirs = None
        if state.project_type == ProjectType.MULTI and state.repos:
            add_dirs = [str(cwd / repo) for repo in state.repos]

        exit_code, session_id = launch_agent(
            agent_name,
            initial_message,
            add_dirs,
            session_id=existing_session,
        )

        # Record session ID
        record_session(task.path, agent_name, session_id)

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")

        # Check for new task directories (product agent creates the task dir)
        if step == TaskStep.PRODUCT:
            new_task_name = _check_new_tasks(cwd, state)
            if new_task_name:
                state = scan_project(cwd)
                task = next((t for t in state.tasks if t.name == new_task_name), task)

        # Determine expected output file from agent name (not step!)
        # This fixes P2: when user picks architect on single-repo, expected_file
        # should be system-analysis.md, not qa-input.md from the resolved step.
        expected_file = AGENT_EXPECTED_OUTPUT.get(agent_name)

        # Retry loop for missing output
        if expected_file and not (task.path / expected_file).exists():
            retry = typer.confirm("Agent did not produce expected output. Retry?", default=True)
            if retry:
                continue
            return "dashboard"

        # Parse routing from output (single place — no double recording)
        routing_next = None
        routing_reason = None
        if expected_file and (task.path / expected_file).exists():
            routing = parse_routing(task.path / expected_file)
            if routing:
                record_routing(task.path, routing.next, routing.reason)
                routing_next = routing.next
                routing_reason = routing.reason

        # Post-agent menu
        action = _post_agent_menu(
            task, state, agent_name, routing_next, routing_reason, expected_file
        )

        if action == "continue":
            continue
        if action == "pick":
            picked = _pick_agent()
            if picked:
                record_routing(task.path, picked, "Manual agent selection")
            continue
        # "dashboard", "quit", "new_task"
        return action


def _check_new_tasks(cwd: Path, state: ProjectState) -> str | None:
    """Check for newly created task directories. Returns new task name or None."""
    current_tasks = scan_tasks(cwd)
    existing_names = {t.name for t in state.tasks}
    new_tasks = [t for t in current_tasks if t.name not in existing_names]

    if new_tasks:
        for t in new_tasks:
            typer.echo(f"Task created: {t.name}")
            ensure_metadata(t.path)
        return new_tasks[0].name

    return None


# ---------------------------------------------------------------------------
# New task flow
# ---------------------------------------------------------------------------


def _start_new_task(cwd: Path, state: ProjectState) -> str:
    """Start a new task. Returns "dashboard", "quit", or "new_task"."""
    typer.echo("Select agent for new task:")
    for i, name in enumerate(ALL_AGENTS, 1):
        default_marker = " (default)" if name == "product" else ""
        typer.echo(f"  {i}. {name}{default_marker}")
    typer.echo()

    product_idx = ALL_AGENTS.index("product") + 1
    choice = typer.prompt("Agent number", default=product_idx, type=int)

    if not (1 <= choice <= len(ALL_AGENTS)):
        typer.echo("Invalid choice.")
        return "dashboard"

    agent_name = ALL_AGENTS[choice - 1]

    tasks_dir = cwd / TASKS_DIR
    tasks_dir.mkdir(parents=True, exist_ok=True)

    initial_message = f"Domain: {DOMAIN_DIR}/" if state.has_domain else None
    exit_code, session_id = launch_agent(agent_name, initial_message)

    new_task_name = _check_new_tasks(cwd, state)
    if new_task_name:
        new_state = scan_project(cwd)
        new_task = next((t for t in new_state.tasks if t.name == new_task_name), None)
        if new_task:
            record_session(new_task.path, agent_name, session_id)
            cont = typer.confirm(f'Continue with "{new_task_name}"?', default=True)
            if cont:
                return _run_agent_for_task(new_task, new_state, cwd)

    return "dashboard"


# ---------------------------------------------------------------------------
# Discovery flow
# ---------------------------------------------------------------------------


def _run_discovery(cwd: Path, state: ProjectState) -> None:
    """Run discovery agent for empty projects."""
    while True:
        typer.echo("🔍 Empty project — starting discovery agent...")
        typer.echo()

        exit_code, _session_id = launch_agent("discovery")

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")
            return

        domain_dir = cwd / DOMAIN_DIR
        if domain_dir.is_dir() and any(domain_dir.glob("*.md")):
            typer.echo("✅ Discovery complete — domain files created.")
            return

        retry = typer.confirm("Agent did not produce expected output. Retry?", default=True)
        if not retry:
            return


# ---------------------------------------------------------------------------
# Resume helper
# ---------------------------------------------------------------------------


def _get_most_recent_task(tasks: list[TaskState]) -> TaskState | None:
    """Get the most recently modified active task."""
    active = [t for t in tasks if t.step != TaskStep.DONE]
    if not active:
        return None
    return max(active, key=lambda t: t.path.stat().st_mtime)


# ---------------------------------------------------------------------------
# Main entry — dashboard loop
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version",
        callback=_version_callback,
        is_eager=True,
    ),
    resume: bool = typer.Option(False, "--resume", help="Resume most recent active task"),
) -> None:
    """devamp — AI agent pipeline orchestrator."""
    cwd = Path.cwd()

    if resume:
        state = scan_project(cwd)
        task = _get_most_recent_task(state.tasks)
        if not task:
            typer.echo("No active tasks to resume.")
            return
        result = _run_agent_for_task(task, state, cwd)
        if result == "quit":
            return
        # After resume, fall through to dashboard loop

    # Dashboard loop — runs until user quits
    while True:
        state = scan_project(cwd)

        # No tasks at all
        if not state.tasks:
            if state.project_type == ProjectType.EMPTY and not state.has_domain:
                _print_dashboard(state)
                _run_discovery(cwd, state)
                continue

            if state.has_domain or state.project_type != ProjectType.EMPTY:
                _print_dashboard(state)
                typer.echo("No tasks. Starting new task...")
                typer.echo()
                result = _start_new_task(cwd, state)
                if result == "quit":
                    return
                continue

        # Print dashboard
        _print_dashboard(state)

        active = [t for t in state.tasks if t.step != TaskStep.DONE]
        active.sort(key=lambda t: t.path.stat().st_mtime, reverse=True)

        # Build menu options
        options: list[str] = []
        if active:
            for i, t in enumerate(active, 1):
                options.append(f"  [{i}] Continue '{t.name}'")
        options.append("  [N] Start new task")
        options.append("  [Q] Quit")

        for opt in options:
            typer.echo(opt)
        typer.echo()

        choice = typer.prompt("Choice", default="1" if active else "N").strip().upper()

        if choice == "Q":
            return

        if choice == "N":
            result = _start_new_task(cwd, state)
            if result == "quit":
                return
            continue

        try:
            idx = int(choice)
            if 1 <= idx <= len(active):
                task = active[idx - 1]
                result = _run_agent_for_task(task, state, cwd)
                if result == "quit":
                    return
                continue
        except ValueError:
            pass

        typer.echo("Invalid choice.")
