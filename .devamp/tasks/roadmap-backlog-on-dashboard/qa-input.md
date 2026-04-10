# QA Handoff: Roadmap backlog on dashboard (P2 fixes)

## Co zrobiono

Dwa P2 z QA session naprawione:

### Fix: Picker UI zgodny ze spec
`_pick_epic()` w `cli.py` wyświetla teraz:
- Nagłówki sekcji `In progress:` / `Planned:` (pomijane gdy sekcja pusta)
- Numeracja ciągła przez obie sekcje
- Separator `──────────────────────` przed ad-hoc
- `[A] Ad hoc (blank)` (było `(free-form task)`)

### Nowe testy: `_update_epic_status()`
5 unit testów w nowym `tests/test_cli.py`:
1. Happy path — `planned` → `in-progress`
2. Brak wpływu na inne epiki — tylko docelowy zmieniony
3. Brak pliku — cichy no-op
4. Brak nagłówka — plik niezmieniony
5. Idempotentność — epik już ma docelowy status

## Kluczowe ścieżki do przetestowania

1. **Picker UI z mix sekcji** — mając epiki in-progress i planned, sprawdzić:
   - Nagłówek `In progress:` na górze z epicami z 🔄
   - Nagłówek `Planned:` pod spodem
   - Separator `──────────────────────` przed ad-hoc
   - `[A] Ad hoc (blank)`
2. **Tylko planned** — brak nagłówka `In progress:`, od razu `Planned:`
3. **Tylko in-progress** — brak nagłówka `Planned:`, separator po in-progress
4. **Testy** — 88/88 przechodzi, lint czysty
5. **Regresja** — reszta flow (ad-hoc, epic task, initial message) niezmieniona

## Zmienione pliki
- `src/devamp/cli.py` — `_pick_epic()` UI fix
- `tests/test_cli.py` — nowy plik, 5 testów `_update_epic_status`
- `CHANGELOG.md` — wpis 0.6.1
- `pyproject.toml` — wersja 0.6.1
- `src/devamp/__init__.py` — wersja 0.6.1

## Routing

Next: qa
Reason: P2 fixes complete, ready for QA verification.
