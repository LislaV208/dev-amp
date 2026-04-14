# QA Session — devamp evolution — 2026-04-10

## Środowisko testowe
- Python 3.11.10, macOS (Apple Silicon)
- devamp 0.4.1 (editable install)
- Testy: `python3.11 -m pytest tests/ -v` — 75/75 passed
- Linter: `ruff check src/` — all checks passed
- CLI: `devamp --version` — 0.4.1 ✅

## Round 1 — znalezione problemy (v0.4.0)

### [P2] `devamp domain` subcommand blokowany przez dashboard loop — ✅ NAPRAWIONE
- **Był:** Typer callback `main()` z `while True` uruchamiał się przed subcommandem `domain()`.
- **Fix:** `ctx.invoked_subcommand` guard w `main()` (cli.py linia 623-624).
- **Weryfikacja:** Test typer pattern potwierdza — `devamp domain` → domain only, `devamp` → dashboard only. ✅

### [P3] Brakujący `record_session` na nowych taskach w `_run_agent_for_task` — ✅ NAPRAWIONE
- **Był:** Product agent tworzący nowe taski przez `_run_agent_for_task` nie zapisywał session ID.
- **Fix:** Dodano `for t in new_tasks: record_session(...)` (cli.py linie 329-330).
- **Weryfikacja:** Identyczny pattern jak w `_start_new_task` (linie 525-526). ✅

### [P3] Mylący komunikat "Empty project" — ✅ NAPRAWIONE
- **Był:** `_run_discovery` wyświetlał "Empty project" dla non-empty projektów bez domain/.
- **Fix:** Zmieniony na "No domain files — starting discovery agent..." (cli.py linia 560).
- **Weryfikacja:** Odczytano z kodu. ✅

### [P3] Rozbieżność `has_domain` check — ✅ NAPRAWIONE
- **Był:** Kod używał `any(iterdir())`, dokumentacja mówiła o `.md` files.
- **Fix:** `iterdir()` → `glob("*.md")` (scanner.py linia 139). Dokumentacja `architecture.md` zaktualizowana.
- **Weryfikacja:** Spójne z `_run_discovery` (linia 573) i dokumentacją. ✅

## Round 2 — re-weryfikacja (v0.4.1)

Wszystkie 4 fixy zweryfikowane:
- Kod poprawny, pattern identyczny w obu ścieżkach (record_session)
- Testy: 75/75 przechodzą
- Linter: czysto
- Wersja: 0.4.1 spójnie w `__init__.py`, `pyproject.toml`, `CHANGELOG.md`
- CHANGELOG.md: aktualne opisy fixów

Brak nowych problemów.

## Obserwacje pozytywne

### Pipeline logic — solidna implementacja
- `is_before_step()`, `get_downstream_agents()` — czyste, dobrze przetestowane
- `AGENT_TO_STEP` reverse mapping generowany automatycznie z `STEP_TO_AGENT`

### Cascade flow — dobrze przemyślany
- Semi-automatyczny cascade z kontrolą użytkownika
- Skip agentów bez istniejącego outputu
- Prawidłowy upstream reference propagowany przez cascade loop
- Ephemeral design — pragmatyczne

### Multi-task picker — czysta implementacja
- 0/1/N tasks — wszystkie ścieżki obsłużone poprawnie
- Session ID prawidłowo zapisywany na wszystkich nowych taskach (po fixie — obie ścieżki)

### Ogólna jakość kodu
- 75/75 testów, lint czysto
- Spójny styl, czytelne nazwy funkcji
- Routing mechanism (clear → launch → parse → record) — dobrze zabezpieczony
- Dokumentacja (CHANGELOG, README, CLAUDE.md, architecture.md) — spójna

## Routing

Next: done
Reason: Wszystkie 4 zgłoszone problemy naprawione i zweryfikowane. Brak nowych issues. Task kompletny.
