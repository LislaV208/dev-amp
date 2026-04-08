# QA Input — devamp v0.1.0

## Co zrobiono

MVP CLI orchestrator — `devamp` command that scans project, shows dashboard, and launches AI agents in sequence.

### Moduły
- **scanner.py** — wykrywa typ projektu (empty/single/multi-repo) po strukturze katalogów, czyta stan tasków z `.devamp/tasks/`
- **pipeline.py** — kolejność kroków, skip logic dla single-repo, mapowanie step→agent
- **context.py** — buduje initial message dla każdego agenta (ścieżki do specyfikacji)
- **launcher.py** — uruchamia `claude --agent` jako interaktywny subprocess
- **cli.py** — dashboard, `--resume`, task selection, output verification

### Inne zmiany
- Agenci przeniesieni z root do `agents/`
- `pyproject.toml` z entry pointem `devamp`
- `CLAUDE.md` z opisem stacku i komend

## Na co zwrócić uwagę

1. **Dashboard** — czy poprawnie wyświetla stan tasków dla każdego typu projektu (empty, single, multi)
2. **Pipeline skip** — single-repo powinien skipować dev-system i dev-multi, skacząc od product do dev-single
3. **Output verification** — po zakończeniu sesji agenta, devamp powinien sprawdzić czy oczekiwany plik powstał
4. **Task creation flow** — product agent tworzy katalog taska, devamp powinien go wykryć i zapytać o kontynuację
5. **--resume** — powinien kontynuować najnowszy aktywny task (po st_mtime katalogu)
6. **Agent path resolution** — czy `launcher.py` poprawnie znajduje pliki agentów w `agents/`
7. **Edge case: multi-repo** — czy `--add-dir` przekazuje wszystkie repozytoria do agenta
