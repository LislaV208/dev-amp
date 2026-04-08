# devamp — Architecture Notes

## Module dependency graph

```
cli.py → scanner.py, pipeline.py, context.py, launcher.py
context.py → scanner.py (types)
pipeline.py → scanner.py (types)
launcher.py → (standalone, uses pathlib to find agents/)
scanner.py → (standalone)
```

## Key design decisions

- **Agents dir resolution:** `launcher.py` resolves agents path relative to package location (`__file__/../../../agents/`). This works for both `pip install -e .` and `pipx install .` but for pipx the agents won't be bundled — needs attention if distributing via pipx.
- **No state file:** Pipeline state is derived purely from file presence in `.devamp/tasks/{task}/`. No database, no config state.
- **subprocess.run without shell:** `claude` CLI is called directly, stdin/stdout inherited from parent process (interactive mode).
- **Task creation:** Product agent creates the task directory and spec.md. After agent exits, devamp scans for new directories in `.devamp/tasks/`.

## Project type detection logic

- Empty: no children dirs AND no files at all
- Multi-repo: 2+ child dirs with `.git` inside
- Single-repo: everything else (including dirs with code but no `.git`)

## Pipeline skip

Single-repo pipeline: product → dev-single → qa (skips dev-system, dev-multi).
`resolve_step()` handles the case where task state points to a skipped step.
