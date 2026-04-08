# devamp MVP — CLI Orchestrator

**Status:** READY_FOR_DEVELOPMENT
**Scope:** MVP (v0.1) — core loop: scan → decide → launch → verify → next

---

## Summary

Python CLI tool (`devamp`) that orchestrates a pipeline of AI agents for software development. Thin wrapper around `claude` CLI — scans project, determines pipeline state, launches the right agent with context, verifies output, moves to next step.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI language | English | Future-proof for public release; zero cost now |
| Agent location | Bundled in `/agents/` within devamp repo | Versioned with code; no dependency on `~/.claude/agents/` |
| Task naming | Agent creates task directory at end of session | Agent has full context to name the task; devamp confirms with user after |
| First agent initial message | None — clean session | User tells the agent what they need directly |
| Packaging | `pyproject.toml` with entry point, pipx-ready | `pip install -e .` for dev, `pipx install .` for production |
| Tech stack | Python, typer, ~300 LOC | As defined in domain docs |

## Project type detection

Scanner checks CWD structure (no LLM):

| CWD structure | Project type | Pipeline |
|---|---|---|
| Empty directory | New project | discovery → product → dev-single → qa |
| Single `.git` / single project with code | Single-repo | product → dev-single → qa |
| Multiple subdirs with `.git` | Multi-repo | product → dev-system → dev-multi → dev-single → qa |

## Pipeline state per task

Determined by file presence in `.devamp/tasks/{task}/`:

```
qa-session.md exists       → done
qa-input.md exists         → qa
multi-plan.md exists       → dev-single
system-analysis.md exists  → dev-multi (or dev-single for single-repo)
spec.md exists             → dev-system (or dev-single for single-repo)
(empty directory)          → product
```

## Agent context (initial messages)

| Agent | Initial message |
|---|---|
| discovery | _(none — clean session)_ |
| product | _(none if first in pipeline)_ / `"Domain: .devamp/domain/"` if after discovery |
| dev-system | `"Spec: .devamp/tasks/{task}/spec.md. Repos: {list}"` |
| dev-multi | `"System analysis: .devamp/tasks/{task}/system-analysis.md"` |
| dev-single | `"Plan: .devamp/tasks/{task}/multi-plan.md"` or `"Spec: .devamp/tasks/{task}/spec.md"` |
| qa | `"Handoff: .devamp/tasks/{task}/qa-input.md"` |

## Agent launching

```
claude --agent /absolute/path/to/agents/{agent}.md "initial message"
```

- Without `-p` flag — interactive session, user talks to agent directly
- Without initial message for first agent in pipeline — just `claude --agent /path/to/agent.md`
- `--add-dir` can be used for multi-repo to give agent access to all repos

## Task creation flow

1. User runs `devamp` (or `devamp` picks up empty pipeline)
2. Devamp launches first agent (e.g. product) — clean interactive session
3. User works with agent, agent builds spec
4. At end of session, agent creates `.devamp/tasks/{slug}/` and saves output (e.g. `spec.md`)
5. Devamp scans `.devamp/tasks/` for new directory after session ends
6. **Safeguard:** Devamp shows `Task created: {slug}. Continue? (Y/n)`
7. If no new directory found: `No task output found. Retry? (Y/n)`

## Output verification

After each agent session, devamp checks for expected file:

| Step | Expected file |
|------|--------------|
| discovery | At least 1 `.md` file in `.devamp/domain/` |
| product | `spec.md` in task directory |
| dev-system | `system-analysis.md` |
| dev-multi | `multi-plan.md` |
| dev-single | `qa-input.md` |
| qa | `qa-session.md` |

If missing: `Agent did not produce expected output. Retry? (Y/n)`

## CLI interface

### `devamp` (no args)

Dashboard + continue:

```
📁 Project: multi-repo (backend/, frontend/)

Active tasks:
  email-notifications  [dev-single]  ← next step
  user-avatars         [product]

Done:
  (none)

→ Continue "email-notifications"? (Y/n)
```

- 0 tasks, no domain: starts discovery (if empty dir) or product
- 0 tasks, has domain: "No tasks. Starting new task..."  → launches first agent
- 1 active task: proposes to continue
- N active tasks: selection list

### `devamp --resume`

Skips dashboard, immediately continues the most recently modified active task.

## Modules

5 modules as defined in domain docs:

1. **cli** — typer entry point. Routes: `devamp` (dashboard), `devamp --resume`
2. **scanner** — detect project type (empty/single/multi) + read task states from `.devamp/tasks/`
3. **pipeline** — step ordering, skip logic (single-repo skips dev-system & dev-multi)
4. **context** — build initial message per agent based on pipeline state
5. **launcher** — run `claude --agent` as interactive subprocess, wait for exit

## File structure (devamp repo)

```
dev-amp/
├── agents/
│   ├── discovery.md
│   ├── product.md
│   ├── developer-system.md
│   ├── developer-multi.md
│   ├── developer-single.md
│   └── qa.md
├── skills/
│   └── ui-ux/
│       └── SKILL.md
├── src/
│   └── devamp/
│       ├── __init__.py
│       ├── cli.py
│       ├── scanner.py
│       ├── pipeline.py
│       ├── context.py
│       └── launcher.py
├── pyproject.toml
└── README.md
```

> ⚠️ **Note for dev-system:** File/folder structure above is a suggestion for orientation — adjust as you see fit during implementation.

## NOT in MVP scope

- Post-QA loop (fix → re-QA)
- `config.yaml` project overrides
- `devamp --agent X` (force specific agent)
- Git integration (auto branch per task)
- `devamp status` (separate command — dashboard is built into `devamp` no-args)
- `devamp rename` (rename task)
