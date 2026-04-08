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
python3.11 -m pytest tests/ -v  # tests
devamp                    # run CLI
```

## Architecture
7 modules in `src/devamp/`:
- `cli.py` — typer entry point, persistent dashboard loop, post-agent menus, --resume flag
- `scanner.py` — detect project type (empty/single/multi-repo), read task states from `.devamp/tasks/`
- `pipeline.py` — step ordering, skip logic (single-repo skips architect & planner), step→agent mapping
- `context.py` — build initial message per agent based on pipeline state, delegation context
- `launcher.py` — run `claude --agent` as interactive subprocess, session tracking (UUID)
- `metadata.py` — task metadata persistence (created_at, sessions, routing) in task-metadata.json
- `routing.py` — parse `## Routing` section from agent output files

Agents live in `src/devamp/agents/` directory (bundled with package):
- `product.md` — specyfikacja produktowa
- `architect.md` — analiza impactu systemowego (dawniej developer-system)
- `planner.md` — koordynacja między projektami (dawniej developer-multi)
- `dev.md` — implementacja (dawniej developer-single)
- `qa.md` — weryfikacja jakości
- `discovery.md` — discovery dla nowych projektów

## Key concepts
- Project type detected by CWD structure (no LLM)
- Pipeline: product → architect → planner → dev → qa → done (single-repo skips architect & planner)
- Pipeline state per task determined by: 1) routing from metadata, 2) file presence (fallback)
- Each agent session is interactive — devamp does NOT proxy the conversation
- Session tracking: devamp generates UUID for each session, resumes via `claude --resume <id>`
- Agent routing: agents write `## Routing` section in output, devamp parses it for next step
- Dashboard is a persistent loop — runs until user quits
- devamp is a thin wrapper around `claude` CLI
