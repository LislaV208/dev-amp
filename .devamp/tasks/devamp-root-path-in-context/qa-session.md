# QA Session — devamp (root path in context) — 2026-04-14

## Środowisko testowe
- Python 3.11.15, macOS (ARM), pytest 9.0.3
- Testy uruchamiane lokalnie: `python3.11 -m pytest tests/ -v`
- Lint: `ruff check src/` — czysto
- Aplikacja nie była uruchamiana end-to-end (CLI wymaga interaktywnego `claude` CLI) — weryfikacja przez code review + unit tests

## Wynik testów
- **111/111 passed** (0.08s) — w tym 23 nowych testów z tego taska + 88 istniejących
- **Ruff**: All checks passed

## Weryfikacja spec vs implementacja

### ✅ `context.py` — `build_initial_message()` / `build_cascade_message()`
- `cwd: Path` parameter dodany do `build_initial_message`, `build_cascade_message`, `_base_message`
- `Project root: {cwd}` jest zawsze pierwszą linią
- Return type zmieniony z `str | None` na `str` — nigdy nie zwraca `None`
- `DOMAIN_DIR` renderowany jako ścieżka absolutna (`{cwd}/{DOMAIN_DIR}/`)
- Brak trailing slash na Project root

### ✅ `cli.py` — 5 callsites
1. `_run_agent_for_task` → `build_initial_message(..., cwd)` ✓
2. `_run_cascade` → `build_cascade_message(..., cwd)` ✓
3. `_start_epic_task` → `f"Project root: {cwd}\nDomain: ..."` ✓
4. `_start_adhoc_task` → `f"Project root: {cwd}\n..."` (z/bez Domain) ✓
5. `_run_discovery` → `f"Project root: {cwd}\n..."` (z/bez Domain) ✓

### ✅ Agenty (6 plików .md)
Wszystkie 6 agentów (discovery, product, architect, planner, dev, qa) mają identyczną sekcję `## Project root` w odpowiednim miejscu — po kontekście domenowym, przed workflow.

### ✅ `launcher.py`
`launch_agent` nadal akceptuje `str | None`. Discovery setup mode zmieniony z `None` na `"Project root: {cwd}"` — `if initial_message:` na linii 71 prawidłowo obsługuje oba przypadki.

### ✅ `architecture.md`
Knowledge zaktualizowany o sekcje v0.7.0 — dokładne i spójne z kodem.

## Znalezione problemy

### [P3] Formatowanie: single vs double newline w direct construction
- **Typ:** Konfiguracja / niespójność
- **Opis:** `build_initial_message()` łączy części z `\n\n` (double newline), natomiast bezpośrednie konstrukcje w `cli.py` (`_start_epic_task`, `_start_adhoc_task`, `_run_discovery`) używają `\n` (single newline) między `Project root:` a `Domain:`.
- **Oczekiwane:** Jednolity format (albo `\n\n` wszędzie, albo `\n`).
- **Wpływ:** Zerowy — LLM parsuje oba formaty identycznie. Czysta estetyka kodu.
- **Priorytet:** P3

### [P3] Brak testów dla direct construction paths
- **Typ:** Pokrycie testowe
- **Opis:** 3 callsite'y w `cli.py` budują initial message bezpośrednio (bez `context.py`). Format `Project root:` w tych ścieżkach nie jest weryfikowany testami. Kod jest wizualnie poprawny, ale brak guardu.
- **Oczekiwane:** Testy potwierdzające `Project root:` jako pierwszą linię dla `_start_epic_task`, `_start_adhoc_task`, `_run_discovery`.
- **Wpływ:** Niski — wymagałoby mockowania `launch_agent`. Regresja wykryta tylko przez code review.
- **Priorytet:** P3

## Obserwacje pozytywne
- **Solidna architektura testów** — 23 nowych testów pokrywają parametrycznie wszystkie kroki pipeline, edge case (brak domeny → nigdy None), delegation, cascade. Bardzo dobra robota.
- **Knowledge zaktualizowane** — `architecture.md` odzwierciedla zmiany wiernie, łącznie z sekcją "Two message construction paths" która jest kluczowa dla przyszłych zmian.
- **Spójność instrukcji agentów** — identyczny tekst `## Project root` we wszystkich 6 agentach, umieszczony w logicznym miejscu.
- **Brak regresji** — 88 istniejących testów przechodzi bez zmian.

## Routing

Next: done
Reason: Implementacja zgodna ze specyfikacją. 111 testów przechodzi. Dwa znalezione problemy to P3 (estetyka formatowania, pokrycie testowe) — nie blokują. Task zakończony.
