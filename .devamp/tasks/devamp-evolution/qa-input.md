# devamp evolution — QA Input

## Summary

Three improvements to devamp implemented across 3 phases:

### Phase 1: Domain Setup
- Discovery agent extended from one-shot setup to 3 modes (setup / domain capture / strategy), auto-detected from `domain/` state
- Domain convention: `context.md` (business facts) + `roadmap.md` (priorities/direction)
- Dashboard `[D] Domain / Strategy` option for non-empty projects
- `devamp domain` CLI shortcut
- Product agent updated: domain-first approach, code only for UI/navigation reference

### Phase 2: Re-entry / Cascade
- Re-entry detection when user picks earlier agent via `[A] Choose different agent`
- Warning about stale downstream artifacts with confirmation
- Semi-automatic cascade after upstream agent finishes — each downstream agent gets "upstream changed" context
- Cascade is ephemeral (no metadata persistence) — user declines = back to dashboard

### Phase 3: Multi-task Output
- `_check_new_tasks()` returns full list instead of first task
- `_pick_new_task()` numbered picker when >1 new tasks
- Session ID recorded on all new tasks from same session
- Remaining tasks appear on dashboard

## Files changed

- `src/devamp/agents/discovery.md` — 3 modes prompt
- `src/devamp/agents/product.md` — domain-first approach
- `src/devamp/agents/dev.md` — flow check practice
- `src/devamp/cli.py` — [D] option, `devamp domain`, re-entry/cascade, multi-task picker
- `src/devamp/context.py` — `build_cascade_message()`
- `src/devamp/pipeline.py` — `is_before_step()`, `get_downstream_agents()`, `AGENT_TO_STEP`
- `tests/test_pipeline.py` — 11 new tests
- `CLAUDE.md` — updated with new concepts
- `CHANGELOG.md` — v0.4.0
- `.devamp/knowledge/architecture.md` — updated

## QA focus areas

1. **Re-entry cascade flow** — trace through: pick earlier agent → warning → agent runs → cascade offered → each downstream agent gets correct context (right step, right input file reference)
2. **Multi-task picker** — verify: 0 tasks (no interaction), 1 task (no picker, direct), N tasks (numbered list, correct selection)
3. **Dashboard [D] option** — only visible for non-empty projects, launches discovery with domain context
4. **`devamp domain` CLI** — works standalone, no task created
5. **Discovery modes** — prompt correctly describes 3 modes with conditions and outputs
6. **Edge case: cascade with missing downstream output** — cascade should skip agents that haven't produced output yet (no qa-session.md at DEV step)

## QA round 2 fixes (v0.4.1)

Fixes for 4 issues found in QA session:

1. **[P2] `devamp domain` subcommand** — added `ctx.invoked_subcommand` guard in `main()` so dashboard loop doesn't block subcommands
2. **[P3] `record_session` on new tasks** — session ID now recorded on all new tasks in `_run_agent_for_task` path (was missing vs `_start_new_task`)
3. **[P3] Discovery message** — "Empty project" → "No domain files" for non-empty projects without `domain/`
4. **[P3] `has_domain` check** — `iterdir()` → `glob("*.md")` to ignore `.DS_Store` etc.

### QA re-check focus
- `devamp domain` should launch discovery directly without dashboard
- `devamp` (no args) and `devamp --resume` should still work normally

## Routing

Next: qa
Reason: QA fixes complete, ready for re-verification.
