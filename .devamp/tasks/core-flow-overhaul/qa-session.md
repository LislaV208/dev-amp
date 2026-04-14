# QA Session — devamp — 2026-04-08 (re-test #2)

## Środowisko testowe
- devamp 0.3.0, Python 3.11.10, macOS
- Testy: 64/64 passed, linter clean
- Testowane: analiza kodu, unit testy, reprodukcja bugów w interpreterze

## Weryfikacja fixów z sesji 2

| Bug z sesji 2 | Status |
|---|---|
| P2 stale routing persistence | ✅ `clear_routing()` przed agent launch (linia 257), sessions preserved |
| P2 agent picker expected_file mismatch | ✅ `AGENT_EXPECTED_OUTPUT[agent_name]` — poprawny output per agent |
| P3 stale names (6 miejsc) | ✅ Zero starych nazw w src/, agents/, README |
| P3 README.md nieaktualny | ✅ Pipeline, architektura, agent table — zaktualizowane |
| P3 double routing recording | ✅ `_post_agent_menu` nie parsuje — dostaje routing jako parametry |

Nowe testy: `test_clear_routing`, `test_clear_routing_preserves_sessions`, `test_agent_expected_output_covers_all_agents`, `test_detect_task_step_no_routing_falls_to_files` (64 total).

## Znalezione problemy

### [P2] clear_routing niszczy delegation context
- **Typ:** Bug
- **Opis:** W `_run_agent_for_task`, `clear_routing()` (linia 257) jest wywoływane PRZED `build_initial_message()` (linia 260). `_delegation_context()` w `context.py` czyta `meta.last_routing_next` i `meta.last_routing_reason` z metadata — ale oba są już None po clear. Agent nigdy nie dostaje "Delegated from QA: ... Reason: ..." w initial message.
- **Oczekiwane:** Agent powinien dostać delegation context. `clear_routing` powinien być po `build_initial_message`, nie przed.
- **Kroki do reprodukcji:**
  1. QA pisze `Next: dev, Reason: 3 bugs found`
  2. devamp parsuje i zapisuje routing
  3. Re-loop: `_resolve_next_agent` czyta routing → "dev" ✓
  4. `clear_routing()` ← czyści routing
  5. `build_initial_message()` → `_delegation_context()` → reads None → returns None
  6. dev dostaje "Spec: .../spec.md" bez informacji o delegacji
- **Reprodukcja potwierdzona** w interpreterze
- **Fix:** zamiana kolejności — `build_initial_message` PRZED `clear_routing`
- **Priorytet:** P2 — spec punkt 8 (delegation context) nie działa

## Obserwacje pozytywne
- Naming consistency: pełna — routing, step, agent, file, UI — wszystko spójne
- Stale routing defense: `clear_routing` + sessions preserved — solidne
- `AGENT_EXPECTED_OUTPUT` rozwiązuje picker/override mismatch
- Single-place routing recording: `_post_agent_menu` czysta (zero parse/record)
- README, CLAUDE.md, agent prompts — wszystko aktualne
- 64 testy, 4 nowe celowane w fixy z sesji 2

## Routing

Next: dev
Reason: P2 ordering bug — `clear_routing` przed `build_initial_message`. Fix to zamiana dwóch linii (257↔260+).
