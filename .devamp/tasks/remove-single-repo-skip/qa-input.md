# QA Input — Remove single-repo skip logic

## Co zrobiono

### 1. Usunięcie skip logic z `pipeline.py`
- Usunięto `SINGLE_REPO_SKIP` constant
- `get_pipeline()` zawsze zwraca `FULL_PIPELINE` niezależnie od `ProjectType`
- `resolve_step()` uproszczony — safety net zostaje, ale w praktyce wszystkie kroki są zawsze obecne

### 2. Fix kontekstu architect dla single-repo (`context.py`)
- `_base_message()` dla `TaskStep.ARCHITECT` — gdy `repos` jest puste, zwraca `"Spec: path/spec.md"` bez pustego "Repos:" suffixu

### 3. Fix auto-resume sesji (`cli.py`)
- Usunięto auto-resume w `_run_agent_for_task` i `_run_cascade`
- Problem: `claude --resume <id> "message"` ignoruje positional argument — agenci startowali bez kontekstu
- Fix: każda sesja w pipeline flow jest świeża (nowe UUID), resume tylko przez explicit `--resume` z CLI
- Usunięto nieużywany import `get_session_id` z `cli.py`

### 4. Testy
- Zaktualizowano ~8 testów w `test_pipeline.py` — skip assertions → full pipeline assertions
- Dodano `test_all_project_types_same_pipeline`
- 74 testy przechodzą

### 5. Docs
- CLAUDE.md — usunięto wzmiankę o skip logic
- `.devamp/knowledge/architecture.md` — zaktualizowano pipeline i session tracking info

## Na co QA powinien zwrócić uwagę

1. **Dashboard na single-repo projekcie** — powinien pokazywać `[→ architect]` po product (nie `[→ dev]`)
2. **Architect na single-repo** — initial message powinien być `"Spec: path/spec.md"` (bez "Repos:")
3. **Pipeline flow** — po product → architect → planner → dev → qa (żadne kroki nie są pomijane)
4. **Multi-repo nie powinno być affected** — pipeline działa jak wcześniej
5. **Session resume** — `devamp --resume` nadal powinno działać (to jedyne miejsce gdzie resume jest sensowne)
6. **Cascade/re-entry** — `is_before_step("architect", TaskStep.DEV, ProjectType.SINGLE)` teraz zwraca `True`

## Zmienione pliki

- `src/devamp/pipeline.py` — usunięty skip, uproszczone `get_pipeline()` i `resolve_step()`
- `src/devamp/context.py` — conditional Repos w architect message
- `src/devamp/cli.py` — usunięty auto-resume sesji w pipeline flow i cascade
- `src/devamp/__init__.py` — version bump 0.5.0
- `pyproject.toml` — version bump 0.5.0
- `CHANGELOG.md` — nowa sekcja 0.5.0
- `CLAUDE.md` — usunięta wzmianka o skip logic
- `tests/test_pipeline.py` — zaktualizowane testy
- `.devamp/knowledge/architecture.md` — zaktualizowana dokumentacja

## Routing

Next: qa
Reason: Implementation complete, ready for QA.
