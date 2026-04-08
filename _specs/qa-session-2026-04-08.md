# QA Session — devamp CLI Orchestrator — 2026-04-08

## Środowisko testowe
- macOS, Python 3.11+, pip install -e . (editable)
- Testy: manualne (Python scripts) — brak pliku test_*.py w repo
- Nie testowano pełnego flow z `claude` CLI (wymaga interaktywnej sesji)
- Testowano: scanner, pipeline, context, launcher (path resolution), cli (dashboard, resume)

## Znalezione problemy

### [P2] _select_task wyświetla surowy step zamiast resolved
- **Typ:** Bug
- **Opis:** W `cli.py` linia 63: `_select_task` wyświetla `t.step.value` (surowy krok z plików), nie `resolve_step(t.step, project_type)`. Dla single-repo, task z `spec.md` pokaże `[dev-system]` zamiast `[dev-single]`.
- **Oczekiwane:** Powinno wyświetlać resolved step, tak jak robi to `_print_dashboard` (linia 44-45).
- **Priorytet:** P2

### [P2] README.md nieaktualny po wdrożeniu CLI
- **Typ:** Dokumentacja
- **Opis:** README nadal mówi o `cp agents/*.md ~/.claude/agents/` — starej metodzie instalacji. Brak informacji o `pip install -e .`, `devamp` command, `pyproject.toml`. Nowy użytkownik nie wie jak uruchomić narzędzie.
- **Oczekiwane:** README powinien opisywać: instalację (`pip install -e .` / `pipx install .`), uruchomienie (`devamp`, `devamp --resume`), architekturę modułów.
- **Priorytet:** P2

### [P3] Rekursja w retry logic — potencjalny stack overflow
- **Typ:** Bug (edge case)
- **Opis:** `_run_discovery` (linia 92) i `_verify_output → _run_agent_for_task` (linia 157) używają rekursji do retry. Jeśli agent wielokrotnie nie produkuje outputu i user cały czas mówi "Retry", stack rośnie.
- **Oczekiwane:** Pętla `while` zamiast rekursji.
- **Priorytet:** P3 — w praktyce user nie zretry'uje 1000 razy, ale to code smell.

### [P3] Agenci nie bundlowani w wheel — `pipx install` nie zadziała
- **Typ:** Konfiguracja / Architektura
- **Opis:** `AGENTS_DIR` w `launcher.py` bazuje na `Path(__file__).parent.parent.parent / "agents"`. Działa z `pip install -e .` (editable), ale w normalnym `pip install` lub `pipx install` pakiet trafia do `site-packages/` i ścieżka `../../agents` wskazuje na `lib/python3.x/` — agentów tam nie ma. Dodatkowo `agents/` nie jest zadeklarowane w `pyproject.toml` jako część wheel.
- **Oczekiwane:** Agenci powinni być bundlowani z pakietem (np. jako package data) albo `AGENTS_DIR` powinien szukać w kilku lokalizacjach.
- **Priorytet:** P3 — MVP działa z editable install, ale blokuje `pipx install .` z spec.

### [P3] Brak testów automatycznych
- **Typ:** Brakująca funkcja
- **Opis:** Nie ma pliku `test_*.py` ani `tests/`. Logika w scanner, pipeline, context jest dobrze testowalna unit testami.
- **Oczekiwane:** Podstawowy test suite — przynajmniej dla scanner i pipeline.
- **Priorytet:** P3

## Obserwacje pozytywne

1. **Scanner działa poprawnie** — wykrywa empty/single/multi-repo bez fałszywych pozytywów. Edge cases (hidden dirs, single .git) obsłużone.
2. **Pipeline skip logic bezbłędna** — single-repo poprawnie skipuje dev-system i dev-multi, resolve_step działa dla wszystkich kombinacji.
3. **Context building spójny ze spec** — initial messages dokładnie odpowiadają specyfikacji (domain, spec, multi-plan, qa-input).
4. **Agent path resolution działa** — wszystkie 6 agentów znalezionych, FileNotFoundError dla nieistniejących.
5. **Task step detection poprawna** — hierarchia plików (qa-session > qa-input > multi-plan > system-analysis > spec > empty) działa prawidłowo.
6. **Kod czysty** — ruff check bez uwag, moduły dobrze rozdzielone, nazewnictwo spójne.
7. **Dashboard czytelny** — format wyjścia jasny i przydatny.

## Nietestowane (wymaga manualnego testu z claude CLI)

- Pełny flow: devamp → agent → output verification → next step
- Task creation flow (product agent tworzy katalog)
- `--add-dir` dla multi-repo
- Interakcja `_check_new_tasks` po zakończeniu sesji agenta

## Rekomendacja routingu

**Proponuję:** `developer-single` — bo:
- P2 bug w `_select_task` to 1 linia (dodaj resolve_step)
- P2 README wymaga przepisania
- P3 rekursja → while to mała zmiana
- P3 bundling agentów i testy to osobny temat, ale da się zrobić w jednej sesji
