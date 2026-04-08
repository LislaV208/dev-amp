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
