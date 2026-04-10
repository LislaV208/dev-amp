"""Typer entry point — persistent dashboard loop with post-agent menus."""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .context import build_cascade_message, build_initial_message
from .launcher import launch_agent
from .metadata import (
    clear_routing,
    ensure_metadata,
    get_created_at,
    record_routing,
    record_session,
)
from .pipeline import (
    AGENT_EXPECTED_OUTPUT,
    AGENT_TO_STEP,
    ALL_AGENTS,
    STEP_TO_AGENT,
    get_downstream_agents,
    get_next_step,
    is_before_step,
    resolve_step,
)
from .routing import ROUTING_DONE, ROUTING_PIPELINE, parse_routing
from .scanner import (
    DOMAIN_DIR,
    ROADMAP_FILE,
    TASKS_DIR,
    ProjectState,
    ProjectType,
    RoadmapEpic,
    TaskState,
    TaskStep,
    parse_roadmap,
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


def _pick_agent(
    current_step: TaskStep | None = None,
    project_type: ProjectType | None = None,
) -> tuple[str | None, bool]:
    """Show full agent list and let user choose.

    Returns (agent_name, is_re_entry). If the picked agent is earlier in the
    pipeline than the current step, warns about stale downstream artifacts
    and asks for confirmation.
    """
    typer.echo("Choose agent:")
    for i, name in enumerate(ALL_AGENTS, 1):
        typer.echo(f"  {i}. {name}")
    typer.echo()

    choice = typer.prompt("Agent number", type=int)
    if not (1 <= choice <= len(ALL_AGENTS)):
        typer.echo("Invalid choice.")
        return None, False

    picked = ALL_AGENTS[choice - 1]

    # Detect re-entry
    if current_step and project_type and is_before_step(picked, current_step, project_type):
        downstream = get_downstream_agents(picked, project_type)
        downstream_files = [
            AGENT_EXPECTED_OUTPUT[a] for a in downstream if a in AGENT_EXPECTED_OUTPUT
        ]
        files_str = ", ".join(downstream_files)
        typer.echo()
        typer.echo(
            f"⚠️  Downstream artifacts ({files_str}) will become stale. "
            f"Pipeline will re-run from this point."
        )
        if not typer.confirm("Continue?", default=True):
            return None, False
        return picked, True

    return picked, False


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
    # Track pending cascade: after a re-entry pick, the upstream agent runs
    # first (next loop iteration), then cascade triggers for downstream agents.
    pending_cascade_from: str | None = None

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

        # Don't resume previous sessions during normal pipeline flow —
        # claude --resume may ignore the initial_message positional argument,
        # which means the agent starts without context.
        # Sessions are only resumed via explicit --resume from the CLI.

        # For multi-repo, give agent access to all repo directories
        add_dirs = None
        if state.project_type == ProjectType.MULTI and state.repos:
            add_dirs = [str(cwd / repo) for repo in state.repos]

        exit_code, session_id = launch_agent(
            agent_name,
            initial_message,
            add_dirs,
        )

        # Record session ID
        record_session(task.path, agent_name, session_id)

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")

        # Check for new task directories (product agent creates the task dir)
        if step == TaskStep.PRODUCT:
            new_tasks = _check_new_tasks(cwd, state)
            if new_tasks:
                for t in new_tasks:
                    record_session(t.path, agent_name, session_id)
                chosen_name = _pick_new_task(new_tasks)
                if chosen_name:
                    state = scan_project(cwd)
                    task = next((t for t in state.tasks if t.name == chosen_name), task)

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

        # Handle cascade after re-entry: upstream agent finished → cascade downstream
        if pending_cascade_from:
            cascade_from = pending_cascade_from
            pending_cascade_from = None
            return _run_cascade(task, state, cwd, cascade_from)

        # Post-agent menu
        action = _post_agent_menu(
            task, state, agent_name, routing_next, routing_reason, expected_file
        )

        if action == "continue":
            continue
        if action == "pick":
            picked, is_re_entry = _pick_agent(step, state.project_type)
            if picked:
                record_routing(task.path, picked, "Manual agent selection")
                if is_re_entry:
                    pending_cascade_from = picked
            continue
        # "dashboard", "quit", "new_task"
        return action


def _run_cascade(
    task: TaskState,
    state: ProjectState,
    cwd: Path,
    upstream_agent: str,
) -> str:
    """Run cascade through downstream agents after re-entry.

    After an upstream agent finishes (re-entry), offers to run each downstream
    agent in pipeline order so they can update their outputs.

    Returns: "dashboard" or "quit".
    """
    downstream = get_downstream_agents(upstream_agent, state.project_type)

    for agent_name in downstream:
        expected_file = AGENT_EXPECTED_OUTPUT.get(agent_name)

        # Only cascade to agents that have existing output to update
        if not expected_file or not (task.path / expected_file).exists():
            continue

        if not typer.confirm(
            f"Upstream artifact changed. Continue cascade to {agent_name}?",
            default=True,
        ):
            return "dashboard"

        typer.echo(f"🔄 Cascading to {agent_name} for '{task.name}'...")
        typer.echo()

        # Build cascade-specific message with the cascade agent's own step
        # (not upstream step) so _base_message gives the right input reference
        cascade_step = AGENT_TO_STEP.get(agent_name, TaskStep.DEV)
        cascade_message = build_cascade_message(
            TaskState(
                name=task.name,
                step=cascade_step,
                path=task.path,
            ),
            state,
            upstream_agent,
        )

        # Don't resume previous sessions during cascade — same reason as
        # _run_agent_for_task: --resume ignores positional initial_message.
        add_dirs = None
        if state.project_type == ProjectType.MULTI and state.repos:
            add_dirs = [str(cwd / repo) for repo in state.repos]

        exit_code, session_id = launch_agent(
            agent_name,
            cascade_message,
            add_dirs,
        )

        record_session(task.path, agent_name, session_id)

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")

        # Parse routing from cascade output
        if expected_file and (task.path / expected_file).exists():
            routing = parse_routing(task.path / expected_file)
            if routing:
                record_routing(task.path, routing.next, routing.reason)

        # This agent becomes upstream for the next cascade step
        upstream_agent = agent_name

    return "dashboard"


def _check_new_tasks(cwd: Path, state: ProjectState) -> list[TaskState]:
    """Check for newly created task directories. Returns list of new tasks."""
    current_tasks = scan_tasks(cwd)
    existing_names = {t.name for t in state.tasks}
    new_tasks = [t for t in current_tasks if t.name not in existing_names]

    for t in new_tasks:
        ensure_metadata(t.path)

    return new_tasks


def _pick_new_task(new_tasks: list[TaskState]) -> str | None:
    """Show list of newly created tasks and let user pick one to continue with.

    Returns the chosen task name, or None if user declines.
    """
    if not new_tasks:
        return None

    if len(new_tasks) == 1:
        typer.echo(f"Task created: {new_tasks[0].name}")
        return new_tasks[0].name

    typer.echo("New tasks created:")
    for i, t in enumerate(new_tasks, 1):
        typer.echo(f"  {i}. {t.name}")
    typer.echo()

    choice = typer.prompt("Which task to continue with?", default=1, type=int)
    if 1 <= choice <= len(new_tasks):
        return new_tasks[choice - 1].name

    typer.echo("Invalid choice.")
    return None


# ---------------------------------------------------------------------------
# New task flow
# ---------------------------------------------------------------------------


def _update_epic_status(cwd: Path, epic_name: str, new_status: str) -> None:
    """Update the Status: line for *epic_name* in roadmap.md.

    Performs a precise single-line replacement to preserve formatting.
    Silent no-op if the section or file is not found.
    """
    import re

    roadmap_path = cwd / ROADMAP_FILE
    if not roadmap_path.is_file():
        return

    text = roadmap_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Find the H2 heading, then replace the first Status: line after it
    found_heading = False
    lines_after_heading = 0
    for idx, line in enumerate(lines):
        if line.strip() == f"## {epic_name}":
            found_heading = True
            lines_after_heading = 0
            continue

        if found_heading:
            # Stop searching if we hit the next H2
            if line.startswith("## "):
                break

            if line.strip():
                lines_after_heading += 1

            if lines_after_heading > 3:
                break

            if re.match(r"^Status:\s*.+$", line.strip(), re.IGNORECASE):
                # Preserve original indentation (if any)
                leading = line[: len(line) - len(line.lstrip())]
                lines[idx] = f"{leading}Status: {new_status}\n"
                roadmap_path.write_text("".join(lines), encoding="utf-8")
                return


def _pick_epic(epics: list[RoadmapEpic]) -> RoadmapEpic | None:
    """Show epic picker and return chosen epic, or None for ad-hoc."""
    in_progress = [e for e in epics if e.status == "in-progress"]
    planned = [e for e in epics if e.status == "planned"]
    ordered = in_progress + planned

    idx = 1
    if in_progress:
        typer.echo("  In progress:")
        for epic in in_progress:
            typer.echo(f"    {idx}. 🔄 {epic.name}")
            idx += 1
        typer.echo()
    if planned:
        typer.echo("  Planned:")
        for epic in planned:
            typer.echo(f"    {idx}. {epic.name}")
            idx += 1
    typer.echo("  ──────────────────────")
    typer.echo("  [A] Ad hoc (blank)")
    typer.echo()

    raw = typer.prompt("Choice", default="1").strip().upper()

    if raw == "A":
        return None

    try:
        idx = int(raw)
        if 1 <= idx <= len(ordered):
            return ordered[idx - 1]
    except ValueError:
        pass

    typer.echo("Invalid choice.")
    return None


def _start_new_task(cwd: Path, state: ProjectState) -> str:
    """Start a new task. Returns "dashboard", "quit", or "new_task"."""
    # Check roadmap for available epics
    epics = parse_roadmap(cwd)
    actionable = [e for e in epics if e.status in ("in-progress", "planned")]

    if actionable:
        epic = _pick_epic(actionable)
        if epic is not None:
            return _start_epic_task(cwd, state, epic)
        # User chose ad-hoc — fall through to agent picker

    return _start_adhoc_task(cwd, state)


def _start_epic_task(cwd: Path, state: ProjectState, epic: RoadmapEpic) -> str:
    """Start a new task from a roadmap epic. Returns "dashboard", "quit", or "new_task"."""
    # Mark as in-progress if planned
    if epic.status == "planned":
        _update_epic_status(cwd, epic.name, "in-progress")
        # Update content to reflect new status for the initial message
        import re

        updated_content = re.sub(
            r"(?im)^Status:\s*planned$",
            "Status: in-progress",
            epic.content,
            count=1,
        )
        epic = RoadmapEpic(
            name=epic.name,
            status="in-progress",
            content=updated_content,
        )

    tasks_dir = cwd / TASKS_DIR
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Build initial message with epic context
    initial_message = f"Domain: {DOMAIN_DIR}/\n\nRoadmap epic:\n{epic.content}"
    exit_code, session_id = launch_agent("product", initial_message)

    new_tasks = _check_new_tasks(cwd, state)
    if new_tasks:
        for t in new_tasks:
            record_session(t.path, "product", session_id)

        chosen_name = _pick_new_task(new_tasks)
        if chosen_name:
            new_state = scan_project(cwd)
            new_task = next((t for t in new_state.tasks if t.name == chosen_name), None)
            if new_task:
                cont = typer.confirm(f'Continue with "{chosen_name}"?', default=True)
                if cont:
                    return _run_agent_for_task(new_task, new_state, cwd)

    return "dashboard"


def _start_adhoc_task(cwd: Path, state: ProjectState) -> str:
    """Start an ad-hoc task (original agent-picker flow).

    Returns "dashboard", "quit", or "new_task".
    """
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

    new_tasks = _check_new_tasks(cwd, state)
    if new_tasks:
        # Record session on all new tasks (they came from this agent session)
        for t in new_tasks:
            record_session(t.path, agent_name, session_id)

        chosen_name = _pick_new_task(new_tasks)
        if chosen_name:
            new_state = scan_project(cwd)
            new_task = next((t for t in new_state.tasks if t.name == chosen_name), None)
            if new_task:
                cont = typer.confirm(f'Continue with "{chosen_name}"?', default=True)
                if cont:
                    return _run_agent_for_task(new_task, new_state, cwd)

    return "dashboard"


# ---------------------------------------------------------------------------
# Discovery flow
# ---------------------------------------------------------------------------


def _run_discovery(cwd: Path, state: ProjectState) -> None:
    """Run discovery agent.

    Works in all three discovery modes:
    - Setup: no domain/ yet (empty project) → creates domain files
    - Domain capture: domain/ exists but sparse → updates context.md
    - Strategy: domain/ filled, user returns → updates roadmap.md

    The agent itself determines which mode to use based on domain/ state
    and user intent.
    """
    while True:
        if state.has_domain:
            typer.echo("🔍 Starting discovery agent (domain / strategy)...")
        else:
            typer.echo("🔍 No domain files — starting discovery agent...")
        typer.echo()

        # Pass domain context if it exists so the agent can detect mode
        initial_message = f"Domain: {DOMAIN_DIR}/" if state.has_domain else None

        exit_code, _session_id = launch_agent("discovery", initial_message)

        if exit_code != 0:
            typer.echo(f"Agent exited with code {exit_code}.")
            return

        domain_dir = cwd / DOMAIN_DIR
        if domain_dir.is_dir() and any(domain_dir.glob("*.md")):
            typer.echo("✅ Discovery complete — domain files updated.")
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


@app.command()
def domain() -> None:
    """Run discovery agent for domain / strategy sessions."""
    cwd = Path.cwd()
    state = scan_project(cwd)
    _run_discovery(cwd, state)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
    # When a subcommand is invoked (e.g. `devamp domain`), don't run the dashboard
    if ctx.invoked_subcommand is not None:
        return

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
        if state.project_type != ProjectType.EMPTY:
            options.append("  [D] Domain / Strategy")
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

        if choice == "D" and state.project_type != ProjectType.EMPTY:
            _run_discovery(cwd, state)
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
