# QA Session — devamp — 2026-04-10

## Środowisko testowe
- macOS, Python 3.14.0, pytest 9.0.3
- Aplikacja zainstalowana editable (`pip install -e .`), wersja 0.5.0
- Testy uruchamiane lokalnie, lint ruff, code review zmian od main

## Znalezione problemy

### ✅ Naprawione w locie: domain/devamp.md outdated
- **Typ:** Dokumentacja
- **Opis:** `.devamp/domain/devamp.md` używał starych nazw agentów (dev-single, dev-system, dev-multi), opisywał skip logic i stary pipeline per project type.
- **Fix:** Zaktualizowany cały plik — aktualne nazwy agentów, jeden pipeline dla wszystkich typów, poprawiona tabela kontekstu, routing-based step detection, 7 modułów.

## Obserwacje pozytywne
- **Czyste usunięcie skip logic** — `SINGLE_REPO_SKIP` i cała logika filtrowania usunięta, `get_pipeline()` zwraca zawsze full pipeline. Chirurgiczna zmiana.
- **Auto-resume fix** — dobrze rozwiązany problem z `claude --resume` ignorującym initial_message. Usunięcie session_id z obu ścieżek (pipeline flow + cascade) jest spójne.
- **Architect context fix** — conditional `if project_state.repos` jest prosty i poprawny.
- **Testy zaktualizowane** — 74/74 zielone, nowy `test_all_project_types_same_pipeline` potwierdza główną zmianę.
- **Lint czysto** — ruff bez uwag.
- **CHANGELOG i CLAUDE.md zaktualizowane** — breaking change jasno opisany.
- **Knowledge/architecture.md zaktualizowane** — session tracking i pipeline info aktualne.

## Routing

Next: done
Reason: Implementacja zgodna ze spec. Jedyny finding (stale domain/devamp.md) naprawiony w locie.
