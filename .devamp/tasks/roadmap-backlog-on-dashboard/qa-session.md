# QA Session — devamp (roadmap-backlog-on-dashboard P2 fixes) — 2026-04-14

## Środowisko testowe

- Single-repo, CLI `devamp` (Python 3.11).
- Weryfikacja lokalna:
  - `python3.11 -m pytest tests/ -v` → **118 passed** (handoff raportował 88; różnica wynika z tego, że między handoffem a sesją zmergowano 0.7.0, które dołożyło 23 testy `test_context.py` + dodatkowe testy bezpośredniej konstrukcji messageʼów w `test_cli.py`).
  - `ruff check src/` → All checks passed.
  - `ruff format --check src/` → 8 files already formatted.
- UI pickera przetestowane przez wywołanie `_pick_epic()` w Pythonie z zamockowanym `typer.prompt` dla trzech scenariuszy (mix / tylko planned / tylko in-progress). Playwright MCP niedostępny i nieistotny — to CLI, nie web.

## Weryfikacja handoff — fix: Picker UI

### Scenariusz 1 — mix sekcji (2× in-progress, 2× planned)

```
  In progress:
    1. 🔄 Epic Alpha (IP)
    2. 🔄 Epic Beta (IP)

  Planned:
    3. Epic Gamma
    4. Epic Delta
  ──────────────────────
  [A] Ad hoc (blank)
```

- ✅ Nagłówek `In progress:` na górze
- ✅ 🔄 przy każdym in-progress
- ✅ Nagłówek `Planned:` pod spodem
- ✅ Numeracja ciągła 1→4 przez obie sekcje
- ✅ Separator `──────────────────────`
- ✅ `[A] Ad hoc (blank)` (stare `(free-form task)` wygrepowane — brak śladów)

### Scenariusz 2 — tylko planned

```
  Planned:
    1. Epic Gamma
    2. Epic Delta
  ──────────────────────
  [A] Ad hoc (blank)
```

- ✅ Brak nagłówka `In progress:`
- ✅ Od razu `Planned:`
- ✅ Separator + ad-hoc

### Scenariusz 3 — tylko in-progress

```
  In progress:
    1. 🔄 Epic Alpha (IP)
    2. 🔄 Epic Beta (IP)

  ──────────────────────
  [A] Ad hoc (blank)
```

- ✅ Brak nagłówka `Planned:`
- ✅ Separator po in-progress
- ✅ Ad-hoc

## Weryfikacja handoff — testy `_update_epic_status`

Plik `tests/test_cli.py` istnieje i zawiera 5 testów opisanych w handoff:

1. `test_update_epic_status_planned_to_in_progress` — happy path ✅
2. `test_update_epic_status_no_impact_on_other_epics` — izolacja między epikami (Alpha/Beta/Gamma) ✅
3. `test_update_epic_status_missing_file` — cichy no-op bez utworzenia pliku ✅
4. `test_update_epic_status_missing_heading` — plik niezmieniony ✅
5. `test_update_epic_status_already_target_status` — idempotentność ✅

Wszystkie przechodzą w ramach pełnego suite.

## Weryfikacja regresji

- `_start_adhoc_task` niezmieniony poza istniejącą ekstrakcją z `_start_new_task` (v0.6.0).
- `_start_epic_task` buduje initial message w formie `Project root: {cwd}\nDomain: {cwd}/.devamp/domain/\n\nRoadmap epic:\n{content}` — spójne z 0.7.0.
- `_start_new_task` przy pustej liście epików przechodzi wprost do `_start_adhoc_task`.
- `grep -ri "free-form"` w `src/` → brak wystąpień. Brak stale texta.

## Znalezione problemy

Brak. Wszystkie punkty z `qa-input.md` pokryte.

### [P3] Nice-to-have — drobna niespójność whitespace w pickerze
- **Typ:** UI (kosmetyka)
- **Opis:** Po bloku `In progress:` jest `typer.echo()` (pusta linia) — w scenariuszu „tylko in-progress” separator ma oddech przed sobą, w scenariuszu „tylko planned” separator leży wprost pod ostatnim epikiem.
- **Oczekiwane:** Zachowanie symetryczne (lub świadomie asymetryczne).
- **Priorytet:** P3, nie blokuje, wizualnie wygląda OK w obu wariantach — zgłaszam tylko dla kompletności.
- **Rekomendacja:** zostawić bez zmian chyba że ktoś celowo chce wyrównać.

## Obserwacje pozytywne

- Handoff rzetelny — wszystkie obietnice potwierdzone 1:1.
- `_update_epic_status` ma precyzyjne okno (max 3 niepuste linie po H2) — mitiguje ryzyko podmiany `Status:` w losowym miejscu dalszej treści epiku. Solidna defensywność.
- Pełny suite 118/118 + lint czysty + format czysty — task w idealnym stanie do zamknięcia.
- Epic picker po skompresowaniu `In progress` + `Planned` + `Ad hoc (blank)` jest teraz czytelniejszy niż payaload przed fixem.

## Routing

Next: done
Reason: Dwa P2 zgłoszone przez poprzednie QA są poprawione i zweryfikowane (UI pickera + testy `_update_epic_status`). Pełny suite 118/118, ruff czysty, regresji brak. Brak P1/P2 do naprawy. Jedyna uwaga to kosmetyczny P3 nie warty iteracji.
