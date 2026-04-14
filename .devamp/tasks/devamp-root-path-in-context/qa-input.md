# QA Input — Project root in agent context

## Co zrobiono

Dodano bezwzględną ścieżkę project root do wszystkich initial messages przekazywanych agentom. Zmiany w dwóch ścieżkach:

### Python (orkiestrator)

1. **`context.py`** — `build_initial_message()`, `build_cascade_message()`, `_base_message()` przyjmują nowy parametr `cwd: Path`. Każda wiadomość zaczyna się od `Project root: /abs/path`. `DOMAIN_DIR` renderowany jako ścieżka absolutna. `build_initial_message` nigdy nie zwraca `None`.

2. **`cli.py`** — 5 callsite'ów zaktualizowanych:
   - `_run_agent_for_task` → `build_initial_message(..., cwd)`
   - `_run_cascade` → `build_cascade_message(..., cwd)`
   - `_start_epic_task` → direct construction z `Project root:` prefix
   - `_start_adhoc_task` → direct construction z `Project root:` prefix
   - `_run_discovery` → direct construction z `Project root:` prefix (setup mode: `None` → string)

3. **`tests/test_context.py`** — 23 nowe testy pokrywające:
   - Project root jako pierwsza linia dla każdego kroku pipeline
   - Nigdy nie zwraca None
   - Brak trailing slash
   - Per-step content (product z/bez domain, architect z/bez repos, planner, dev z/bez plan, qa)
   - Delegation context
   - Cascade messages
   - Absolutna ścieżka DOMAIN_DIR w `_base_message`

### Instrukcje agentów (6 plików .md)

Dodano sekcję `## Project root` do każdego agenta (discovery, product, architect, planner, dev, qa) — identyczna treść instruująca LLM aby rozwiązywał `.devamp/` ścieżki względem project root.

## Na co zwrócić uwagę

1. **Format wiadomości** — `Project root:` musi być ZAWSZE pierwszą linią. Sprawdzić dla: pipeline flow, cascade, epic task, adhoc task, discovery.
2. **Discovery setup mode** — wcześniej przekazywał `None`, teraz `"Project root: {cwd}"`. Sprawdzić że `launch_agent("discovery", "Project root: ...")` działa poprawnie.
3. **DOMAIN_DIR absolutny** — w wiadomościach musi być pełna ścieżka (`/abs/.devamp/domain/`), nie relatywna (`.devamp/domain/`).
4. **Agenty .md** — sekcja `## Project root` we właściwym miejscu (po wiedzy domenowej, przed workflow).
5. **Brak regresji** — 111 testów przechodzi, w tym 88 istniejących.

## Routing

Next: qa
Reason: Implementation complete, ready for QA.
