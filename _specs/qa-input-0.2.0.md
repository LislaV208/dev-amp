# QA Input — devamp v0.2.0

## What changed

All 5 issues from QA session 2026-04-08 addressed:

### P2 fixes
1. **`_select_task` resolved step** — now uses `resolve_step()` like `_print_dashboard`. Single-repo tasks display `[dev-single]` instead of raw `[dev-system]`.
2. **README rewritten** — covers `pip install -e .` / `pipx install .`, `devamp` / `devamp --resume`, architecture overview.

### P3 fixes
3. **Recursion → while loops** — `_run_discovery` and `_run_agent_for_task`/`_verify_output` (renamed to `_should_retry`) no longer use recursion. Retry is now a `while True` loop.
4. **Agents bundled in package** — moved from `agents/` (repo root) to `src/devamp/agents/`. `launcher.py` resolves from `__file__/../agents/`. `pyproject.toml` declares artifacts. Old `agents/` dir removed.
5. **Unit tests** — 27 tests in `tests/test_scanner.py` and `tests/test_pipeline.py`. Covers: project type detection, task step detection, scan_tasks, scan_project, pipeline ordering, resolve_step, mapping completeness.

## What to verify

- [ ] `devamp` dashboard in single-repo project with multiple active tasks — step labels should show `[dev-single]` not `[dev-system]`
- [ ] `pipx install .` in a clean venv — agents should resolve correctly
- [ ] Retry flow: mock agent that produces no output → confirm retry → verify no stack growth (optional, code review sufficient)
- [ ] `python -m pytest tests/ -v` — 27 tests pass
- [ ] `ruff check src/ tests/` — clean

## Files changed

- `src/devamp/cli.py` — `_select_task` signature, recursion→while
- `src/devamp/launcher.py` — agents path resolution
- `src/devamp/agents/` — new location (moved from repo root)
- `pyproject.toml` — version bump, artifacts, dev dependencies, pytest config
- `README.md` — full rewrite
- `CHANGELOG.md` — v0.2.0 entry
- `tests/test_scanner.py` — new
- `tests/test_pipeline.py` — new
