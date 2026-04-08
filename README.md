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
Discovery → Product → Dev-System → Dev-Multi → Dev-Single → QA
```

Single-repo projects skip `Dev-System` and `Dev-Multi` — pipeline goes straight from `Product` to `Dev-Single`.

## Architecture

```
src/devamp/
  cli.py        — typer entry point, dashboard, --resume flag
  scanner.py    — detect project type (empty/single/multi-repo), read task states
  pipeline.py   — step ordering, skip logic for single-repo
  context.py    — build initial message per agent based on pipeline state
  launcher.py   — run `claude --agent` as interactive subprocess
```

State is derived from file presence in `.devamp/tasks/{task}/` — no database, no config file.

## Agents

| Agent | Role |
|-------|------|
| `discovery` | Extract product vision from conversation with developer/client |
| `product` | Product analysis, spec, UX |
| `developer-system` | System-wide impact analysis |
| `developer-multi` | Coordination across repos |
| `developer-single` | Code implementation |
| `qa` | Testing, bug collection, routing |

Agents live in the `agents/` directory and are passed to `claude --agent`.

## Skills

| Skill | Description |
|-------|-------------|
| `ui-ux` | Generic UI/UX skill — checklist per role (product/dev/qa) |
