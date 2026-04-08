# Changelog

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
