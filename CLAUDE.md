# devamp — CLI Orchestrator

## Stack
- Python 3.11+
- typer (CLI framework)
- hatchling (build)

## Commands
```bash
pip install -e .          # dev install
ruff check src/           # lint
ruff format src/          # format
devamp                    # run CLI
```

## Architecture
5 modules in `src/devamp/`:
- `cli.py` — typer entry point, dashboard, --resume flag
- `scanner.py` — detect project type (empty/single/multi-repo), read task states from `.devamp/tasks/`
- `pipeline.py` — step ordering, skip logic (single-repo skips dev-system & dev-multi)
- `context.py` — build initial message per agent based on pipeline state
- `launcher.py` — run `claude --agent` as interactive subprocess

Agents live in `agents/` directory (bundled with repo).

## Key concepts
- Project type detected by CWD structure (no LLM)
- Pipeline state per task determined by file presence in `.devamp/tasks/{task}/`
- Each agent session is interactive — devamp does NOT proxy the conversation
- devamp is a thin wrapper around `claude` CLI
