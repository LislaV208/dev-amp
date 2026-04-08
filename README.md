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
```

On first run in an empty directory, devamp launches the **discovery** agent to establish domain context.

## Pipeline

```
Discovery → Product → Architect → Planner → Dev → QA
```

Single-repo projects skip `Architect` and `Planner` — pipeline goes straight from `Product` to `Dev`.

## Architecture

```
src/devamp/
  cli.py        — typer entry point, persistent dashboard loop, post-agent menus
  scanner.py    — detect project type (empty/single/multi-repo), read task states
  pipeline.py   — step ordering, skip logic for single-repo
  context.py    — build initial message per agent, delegation context
  launcher.py   — run `claude --agent` as interactive subprocess, session tracking
  metadata.py   — task metadata persistence (timestamps, sessions, routing)
  routing.py    — parse `## Routing` section from agent output files
```

State is derived from routing metadata (priority) and file presence in `.devamp/tasks/{task}/` (fallback).

## Agents

| Agent | Role |
|-------|------|
| `discovery` | Extract product vision from conversation with developer/client |
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
