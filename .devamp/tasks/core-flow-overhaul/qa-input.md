# QA Input — Core Flow Overhaul (v2 — with QA fixes)

## Co zrobiono

Przebudowa devamp z modelu "run-once-exit" na persistent dashboard loop z pełnym system routingu między agentami. Druga iteracja — zawiera fixy z pierwszej sesji QA.

### Zmiany w modułach Python (src/devamp/)

1. **Rename agentów** — pliki i mappingi:
   - `developer-system.md` → `architect.md`, `developer-multi.md` → `planner.md`, `developer-single.md` → `dev.md`
   - TaskStep enum: `DEV_SYSTEM` → `ARCHITECT`, `DEV_MULTI` → `PLANNER`, `DEV_SINGLE` → `DEV`

2. **Nowy moduł `routing.py`** — parsuje `## Routing` z markdown outputów

3. **Nowy moduł `metadata.py`** — `task-metadata.json` per task + `clear_routing()` (P2 fix)

4. **`scanner.py`** — `detect_task_step()` sprawdza routing z metadata first, file-based jako fallback

5. **`pipeline.py`** — `get_next_step()`, `ALL_AGENTS`, `AGENT_EXPECTED_OUTPUT` (P2 fix)

6. **`launcher.py`** — zwraca `tuple[int, str]` (exit_code, session_id), UUID-based sessions

7. **`context.py`** — kontekst delegacji w initial message

8. **`cli.py`** — kompletny rewrite z QA fixes:
   - Dashboard jako `while True` loop
   - Post-agent menu
   - `clear_routing()` przed każdym agent launch (P2: stale routing)
   - Expected output z `AGENT_EXPECTED_OUTPUT[agent_name]` nie `STEP_EXPECTED_OUTPUT[step]` (P2: picker mismatch)
   - Routing recording w jednym miejscu (P3: double recording)
   - Brak rekursji — tylko pętle `while`

### Zmiany w promptach agentów

- Wszystkie: nazwy zaktualizowane, stare usunięte
- product.md: + knowledge awareness, + routing guidelines
- architect.md: + backward delegation, + routing section
- planner.md: + backward delegation, + routing section
- dev.md: + backward delegation, + routing section
- qa.md: + knowledge awareness, + standardized routing format
- discovery.md: "dev-system" → "architect"

### Inne pliki
- README.md: zaktualizowany pipeline, architektura, agent table
- CLAUDE.md: 7 modułów + agent listing

## QA fixes z sesji 1 — zastosowane

| Issue | Fix |
|---|---|
| P2 stale routing persistence | `clear_routing()` przed każdym agent launch |
| P2 agent picker expected_file mismatch | `AGENT_EXPECTED_OUTPUT[agent_name]` zamiast `STEP_EXPECTED_OUTPUT[step]` |
| P3 stale names (6 miejsc) | Wszystkie zamienione |
| P3 README.md nieaktualny | Zaktualizowany |
| P3 double routing recording | Routing parsowany tylko w `_run_agent_for_task` |

## QA fix z sesji 2 — zastosowany

| Issue | Fix |
|---|---|
| P2 clear_routing niszczy delegation context | `build_initial_message()` przed `clear_routing()` — agent dostaje delegation context |

## Na co QA powinien zwrócić uwagę

1. **Delegation context** — po backward delegation (np. QA → dev), dev agent powinien dostać "Delegated from qa: Reason: ..." w initial message
2. **Stale routing defense** — `clear_routing()` nadal wywoływany, ale PO `build_initial_message`
2. **Agent picker na single-repo** — czy pick architect → oczekuje system-analysis.md (nie qa-input.md)
3. **Brak starych nazw** — grep na `developer-system`, `developer-multi`, `developer-single`, `dev-system`, `dev-multi`, `dev-single`, `READY_FOR_MULTI`, `READY_FOR_SINGLE`
4. **Dashboard loop** — po akcji wraca do dashboard, Q kończy
5. **Session tracking** — UUID generowany, zapisywany, resume działa
6. **Backward compat** — taski bez metadata.json działają (file-based fallback)

## Routing

Next: qa
Reason: Implementation complete with all QA fixes from sessions 1 and 2. Ready for re-verification.
