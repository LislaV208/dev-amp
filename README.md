# Dev Amp — AI Agent Pipeline Orchestrator

CLI orchestrator that runs AI agents in sequence to take a project from idea to tested code.

## Installation

```bash
# Development (editable)
pip install -e .

# Or via pipx
pipx install .
```

Requires Python 3.11+ and [Claude CLI](https://docs.anthropic.com/claude-cli) installed.

## Usage

```bash
# Show dashboard — project status, active tasks, next step
devamp

# Resume most recently active task
devamp --resume

# Run discovery agent directly (domain capture / strategy)
devamp domain
```

On first run in an empty directory, devamp launches the **discovery** agent to establish domain context. For existing projects, use `devamp domain` or the `[D] Domain / Strategy` dashboard option to update domain knowledge or plan direction.

## Pipeline

```
Discovery → Product → Architect → Planner → Dev → QA
```

Single-repo projects skip `Architect` and `Planner` — pipeline goes straight from `Product` to `Dev`.

## Architecture

```
src/devamp/
  cli.py        — typer entry point, dashboard loop, re-entry/cascade, multi-task picker
  scanner.py    — detect project type (empty/single/multi-repo), read task states
  pipeline.py   — step ordering, skip logic for single-repo
  context.py    — build initial message per agent, delegation context
  launcher.py   — run `claude --agent` as interactive subprocess, session tracking
  metadata.py   — task metadata persistence (timestamps, sessions, routing)
  routing.py    — parse `## Routing` section from agent output files
```

State is derived from routing metadata (priority) and file presence in `.devamp/tasks/{task}/` (fallback).

## Key features

- **Re-entry & cascade:** Pick an earlier agent to revisit — devamp warns about stale artifacts and cascades updates through downstream agents
- **Multi-task output:** Product/discovery agent can create multiple tasks in one session — picker shown, remaining tasks land on dashboard
- **Domain knowledge:** `domain/context.md` (business facts) + `domain/roadmap.md` (priorities) — separate from technical `knowledge/`

## Agents

| Agent | Role |
|-------|------|
| `discovery` | Domain knowledge — setup, domain capture, or strategy (3 modes) |
| `product` | Product analysis, spec, UX |
| `architect` | System-wide impact analysis |
| `planner` | Coordination across repos |
| `dev` | Code implementation |
| `qa` | Testing, bug collection, routing |

Agents are bundled in `src/devamp/agents/` and are passed to `claude --agent`.

## Skills

| Skill | Description |
|-------|-------------|
| `ui-ux` | Generic UI/UX skill — checklist per role (product/dev/qa) |
