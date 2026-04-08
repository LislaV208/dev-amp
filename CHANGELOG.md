# Changelog

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
