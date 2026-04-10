# devamp — Architecture Notes

## Module dependency graph

```
cli.py → scanner.py, pipeline.py, context.py, launcher.py, metadata.py, routing.py
context.py → scanner.py (types), metadata.py
pipeline.py → scanner.py (types)
scanner.py → metadata.py (for routing-based step detection)
launcher.py → (standalone, uses pathlib to find agents/)
metadata.py → (standalone, JSON persistence)
routing.py → (standalone, regex parsing)
```

## Key design decisions

- **Agents dir resolution:** `launcher.py` resolves agents path from `__file__/../agents/` — agents are bundled inside the package at `src/devamp/agents/`. Works with both `pip install -e .` and `pipx install .`.
- **State priority:** Routing from metadata (last_routing_next) has priority over file-based detection. File presence is fallback for backward compatibility and initial state.
- **Session tracking:** devamp generates a UUID before launching claude and passes it via `--session-id`. This means we always know the session ID. For resume, we pass `--resume <session_id>`.
- **Stale routing defense:** `clear_routing()` is called before every agent launch. If agent doesn't produce `## Routing`, metadata stays clean — no stale routing loops.
- **Expected output by agent name:** `AGENT_EXPECTED_OUTPUT[agent_name]` is used instead of `STEP_EXPECTED_OUTPUT[step]` to correctly handle manual agent picks (e.g. architect on single-repo).
- **subprocess.run without shell:** `claude` CLI is called directly, stdin/stdout inherited from parent process (interactive mode).
- **Task creation:** Product agent creates the task directory and spec.md. After agent exits, devamp scans for new directories in `.devamp/tasks/`.
- **Dashboard loop:** `main()` runs a `while True` loop. After every action (agent session, post-agent menu) control returns to dashboard. Only `[Q] Quit` breaks the loop.
- **Agent rename (v0.3.0):** developer-system → architect, developer-multi → planner, developer-single → dev. Names match roles, not scope. Same names in routing, files, and UI.

## Project type detection logic

- Empty: no children dirs AND no files at all
- Multi-repo: 2+ child dirs with `.git` inside
- Single-repo: everything else (including dirs with code but no `.git`)

## Pipeline

Full: product → architect → planner → dev → qa → done
Single-repo skip: architect, planner (product → dev → qa → done)

`resolve_step()` handles the case where task state points to a skipped step.

## Routing mechanism

1. `clear_routing()` before launching agent (prevents stale loops)
2. Agent writes `## Routing` section in its output markdown file
3. devamp parses it via `routing.py` → `RoutingRecommendation(next, reason)`
4. Stored in `task-metadata.json` via `metadata.py`
5. `detect_task_step()` checks metadata routing first, falls through to file-based on `pipeline`
6. Post-agent menu shows routing recommendation to user

## Metadata per task

File: `.devamp/tasks/{task}/task-metadata.json`
```json
{
  "created_at": "2026-04-08T12:00:00+00:00",
  "sessions": {"dev": "uuid-here", "qa": "uuid-here"},
  "last_routing_next": "dev",
  "last_routing_reason": "3 bugs found"
}
```

## Discovery agent — 3 modes (v0.4.0)

Discovery is no longer a one-shot setup agent. Three modes, auto-detected from context:

| Mode | Condition | Output |
|------|-----------|--------|
| Setup | No `domain/` | Creates `context.md` + `roadmap.md` |
| Domain capture | `domain/` exists but sparse | Updates `context.md` |
| Strategy | `domain/` filled, user returns | Updates `roadmap.md` |

- Agent determines mode from `domain/` state + user's opening message
- Discovery is NOT per-task — it's per-project (domain is shared)
- Dashboard option `[D] Domain / Strategy` available for non-empty projects
- CLI shortcut: `devamp domain` (typer `@app.command()`)
- Auto-trigger for empty projects (no domain/ + EMPTY) unchanged

## Domain convention

```
.devamp/domain/
├── context.md    # WHO/WHAT — company, product, users, constraints
└── roadmap.md    # WHERE — priorities, MVP, later, out of scope
```

- `domain/` = business knowledge (filled by discovery, read by product + others)
- `knowledge/` = technical knowledge (filled by dev/architect, read by dev/architect/planner)
- Code checks `has_domain` by dir existence + any `.md` files — no filename assumptions

## Product agent — domain-first approach (v0.4.0)

Product agent no longer reverse-engineers domain from code. Priority:
1. Read `domain/` for business context
2. Code only for current UI state (screens, forms, navigation)
3. Ask developer for screenshots when visual context needed

## Re-entry & cascade (v0.4.0)

Re-entry = user picks an agent earlier in the pipeline than the current step.

**Detection:** `is_before_step(agent_name, current_step, project_type)` in `pipeline.py`. Uses `AGENT_TO_STEP` reverse mapping and pipeline order.

**Flow:**
1. User picks agent via `[A] Choose different agent` in post-agent menu
2. `_pick_agent()` detects re-entry → warns about stale downstream artifacts → asks confirmation
3. `pending_cascade_from` flag set in `_run_agent_for_task` loop
4. Upstream agent runs (next loop iteration, via routing)
5. After upstream finishes, `_run_cascade()` triggers — offers each downstream agent in order
6. Each downstream agent gets cascade context: "Upstream artifact changed. Review and update."
7. Cascade is semi-automatic: asks "Continue cascade to X?" before each agent
8. User says No → back to dashboard, normal flow takes over

**No persistent state:** Cascade is ephemeral flow in `cli.py`, not tracked in metadata. `cascade_pending` is a local variable, not persisted. If user quits mid-cascade, the task just sits at whatever step routing points to.

**Key functions:**
- `pipeline.is_before_step()` — is agent earlier in pipeline?
- `pipeline.get_downstream_agents()` — list agents after given agent
- `context.build_cascade_message()` — "upstream changed" initial message
- `cli._run_cascade()` — semi-automatic cascade loop
- `cli._pick_agent()` — re-entry detection + warning
