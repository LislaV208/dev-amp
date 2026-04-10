# Changelog

## 0.5.0

### Breaking changes
- **Full pipeline for all project types:** Single-repo and empty projects now run the full pipeline (product → architect → planner → dev → qa). Previously architect & planner were skipped.

### Fixes
- [P2] Agents no longer auto-resume previous sessions during pipeline flow — `claude --resume` ignores positional arguments, so agents were starting without context. Each pipeline step now gets a fresh session with proper initial message.
- [P3] Architect initial message no longer includes empty "Repos:" suffix for single-repo projects

### Removed
- `SINGLE_REPO_SKIP` constant from `pipeline.py`

## 0.4.1

### Fixes
- [P2] `devamp domain` subcommand no longer blocked by dashboard loop — added `ctx.invoked_subcommand` guard in `main()`
- [P3] Session ID now recorded on new tasks created via `_run_agent_for_task` path (was only recorded in `_start_new_task`)
- [P3] Discovery message changed from "Empty project" to "No domain files" for non-empty projects without `domain/`
- [P3] `has_domain` check uses `glob("*.md")` instead of `iterdir()` — ignores non-markdown files like `.DS_Store`

## 0.4.0

### Features
- **Discovery 3 modes:** Discovery agent now supports setup, domain capture, and strategy modes — auto-detected from `domain/` state and user intent
- **Domain convention:** Standardized `domain/context.md` + `domain/roadmap.md` as minimum domain files
- **Dashboard [D] option:** New `[D] Domain / Strategy` option on dashboard for non-empty projects
- **`devamp domain` CLI shortcut:** Run discovery agent directly without going through dashboard
- **Product agent domain-first:** Product agent reads `domain/` for business context first, uses code only for UI/navigation reference
- **Re-entry detection:** When user picks an agent earlier in pipeline, devamp warns about stale downstream artifacts and asks confirmation
- **Cascade after re-entry:** Semi-automatic cascade through downstream agents after upstream re-entry — each agent gets "upstream changed" context
- **Multi-task output:** Product/discovery agent can create N task directories per session — picker shown when multiple tasks created, remaining tasks appear on dashboard
- **Dev agent flow check:** New practice in dev agent prompt — mental flow testing after implementation to catch logic bugs

### New functions
- `pipeline.is_before_step()` — detect if agent is earlier in pipeline than current step
- `pipeline.get_downstream_agents()` — list agents downstream from given agent
- `pipeline.AGENT_TO_STEP` — reverse mapping of STEP_TO_AGENT
- `context.build_cascade_message()` — build "upstream changed" initial message for cascade agents
- `cli._run_cascade()` — semi-automatic cascade loop
- `cli._pick_new_task()` — multi-task picker

### Tests
- 75 tests total (up from 64): new tests for `is_before_step` and `get_downstream_agents`

## 0.3.1

### Fixes
- [P2] Delegation context now built before `clear_routing()` — agents receive "Delegated from X: Reason: ..." in initial message

## 0.3.0

### Breaking changes
- Agent rename: `developer-system` → `architect`, `developer-multi` → `planner`, `developer-single` → `dev`
- TaskStep enum values changed: `DEV_SYSTEM` → `ARCHITECT`, `DEV_MULTI` → `PLANNER`, `DEV_SINGLE` → `DEV`
- `launch_agent()` now returns `tuple[int, str]` (exit_code, session_id) instead of `int`

### Features
- **Dashboard loop:** persistent hub — program runs until user quits, no more exit after single action
- **Post-agent menu:** after agent session, user chooses: continue, pick agent, dashboard, or quit
- **Agent picker:** full agent list available regardless of project type (manual override)
- **Routing system:** agents write `## Routing` section in output; devamp parses and uses for next step
- **Session tracking:** UUID-based session IDs, resume previous sessions when agent returns to task
- **Task metadata:** `task-metadata.json` per task (created_at, sessions, routing info)
- **Loop support:** routing from metadata overrides file-based step detection (QA → dev loops work)
- **Delegation context:** initial message includes who delegated and why
- **Product routing awareness:** product agent recommends next agent based on task complexity
- **Knowledge awareness:** product, qa, architect, planner now read `.devamp/knowledge/` on startup
- **Backward delegation:** all agents (except product) can delegate back when input has gaps
- **"Start new task" always available** in dashboard, not just when all tasks are done

### Fixes
- [P2] Session ID captured in all launch paths (new-task, auto-launch)
- [P2] Recursion replaced with while loops (re-fixed regression)
- [P2] Stale routing cleared before each agent launch (prevents infinite loops)
- [P2] Expected output derived from agent name, not pipeline step (fixes picker on single-repo)
- [P3] CLAUDE.md updated to reflect all 7 modules
- [P3] README.md updated with new agent names and architecture
- [P3] All stale agent names removed from comments and prompts

### New modules
- `metadata.py` — task metadata persistence
- `routing.py` — parse `## Routing` from agent output files

### Tests
- 60 tests total (up from 27): new tests for routing, metadata, renamed agents, loop detection

## 0.2.2

- Feat: "Start new task?" prompt when all tasks are done, with agent selection (default: product)

## 0.2.1

- Fix: agent loading — pass agent by name (not path) to `claude --agent` so system prompt loads correctly (P1)
- Added `sync_agents()` — auto-copies bundled agents to `~/.claude/agents/` before each launch
- Added `tests/test_launcher.py` with 4 tests for agent sync and validation

## 0.2.0

- Fix: `_select_task` now displays resolved step instead of raw step (P2)
- Updated README with current installation and usage instructions (P2)
- Fix: replaced recursion with `while` loops in retry logic to prevent stack overflow (P3)
- Agents bundled inside package (`src/devamp/agents/`) — `pipx install` now works (P3)
- Added unit test suite (27 tests) for scanner and pipeline modules (P3)
- Added `[project.optional-dependencies] dev` with pytest and ruff

## 0.1.0

- Initial MVP CLI orchestrator
- Project type detection (empty / single-repo / multi-repo)
- Pipeline state tracking from `.devamp/tasks/` file presence
- Pipeline skip logic (single-repo skips dev-system & dev-multi)
- Agent launching via `claude --agent` as interactive subprocess
- Context building (initial message per agent)
- Dashboard with active/done tasks
- `--resume` flag to continue most recent active task
- Output verification after each agent session
- Task creation flow with user confirmation
- Agents moved to `agents/` directory (bundled with repo)
