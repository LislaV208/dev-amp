# System Analysis — Przekazywanie ścieżki roota projektu do agentów

## Kluczowe odkrycie

Ścieżki do artefaktów taska (spec.md, system-analysis.md, itd.) **są już bezwzględne** w initial messages — `task.path` budowane jest z `Path.cwd() / TASKS_DIR / dir_name` w `scanner.py`.

Problem ogranicza się do:
1. **`DOMAIN_DIR`** — stała `.devamp/domain` jest relatywna, używana wprost w 4 miejscach budowania wiadomości
2. **Brak `Project root:`** — agenty nie mają kotwicy dla instrukcji wewnętrznych (`.devamp/knowledge/`, `.devamp/domain/` w treści `.md`)
3. **Instrukcje agentów** — hardcodowane ścieżki relatywne w 30+ miejscach w 6 plikach `.md`

## Mapa impactu

| Moduł | Dotknięty? | Typ zmiany |
|---|---|---|
| `context.py` | ✅ TAK | Dodanie `cwd: Path` do sygnatur + `Project root:` do wiadomości + absolutne ścieżki DOMAIN_DIR |
| `cli.py` | ✅ TAK | Przekazanie `cwd` do context.py + fix 3 miejsc direct construction (discovery, epic, adhoc) |
| `agents/discovery.md` | ✅ TAK | Dodanie sekcji o project root |
| `agents/product.md` | ✅ TAK | Dodanie sekcji o project root |
| `agents/architect.md` | ✅ TAK | Dodanie sekcji o project root |
| `agents/planner.md` | ✅ TAK | Dodanie sekcji o project root |
| `agents/dev.md` | ✅ TAK | Dodanie sekcji o project root |
| `agents/qa.md` | ✅ TAK | Dodanie sekcji o project root |
| `scanner.py` | ❌ NIE | Bez zmian |
| `launcher.py` | ❌ NIE | Przyjmuje gotowy string — bez zmian |
| `pipeline.py` | ❌ NIE | Bez zmian |
| `metadata.py` | ❌ NIE | Bez zmian |
| `routing.py` | ❌ NIE | Bez zmian |
| Testy | ✅ TAK | Brak testów dla `context.py` — dodać przy okazji |

## Dwie ścieżki konstruowania wiadomości

Kluczowa obserwacja architektoniczna. Wiadomości dla agentów powstają na **dwa sposoby**:

1. **Pipeline flow** — `build_initial_message()` / `build_cascade_message()` w `context.py` — dla tasków w toku
2. **Direct construction** — w `cli.py` — dla nowych tasków i discovery

Obie ścieżki muszą dostawać `Project root:` i używać bezwzględnych ścieżek.

## Decyzje implementacyjne

### 1. Przekazanie `cwd` do `context.py`

Dodać parametr `cwd: Path` do `build_initial_message()` i `build_cascade_message()`. Nie dodawać `cwd` do `ProjectState` — scanner skanuje, nie trzyma konfiguracji runtime.

### 2. Instrukcja w agentach — jeden paragraf

Jeden paragraf na agenta, umieszczony na górze (przed/po "Wiedza domenowa"). Nie zmieniać każdego z 30+ wystąpień `.devamp/` — LLM rozumie kontekst z jednego paragrafu.

Treść:

> **Devamp przekazuje Ci bezwzględną ścieżkę roota projektu w initial message (`Project root: ...`). Wszystkie ścieżki `.devamp/` w tym dokumencie — `domain/`, `knowledge/`, `tasks/` — rozwiązuj względem tego roota, nie względem bieżącego katalogu roboczego. Gdy zmieniasz katalog w trakcie pracy (np. wchodzisz do sub-repo), `.devamp/` nadal musi wskazywać na `{project_root}/.devamp/`.**

### 3. Discovery w trybie setup

Obecnie: `initial_message = None`. Po zmianie: zawsze dawać `Project root:`, nawet bez domeny.

- Setup mode: `"Project root: /Users/x/BKF"`
- Domain capture / Strategy: `"Project root: /Users/x/BKF\nDomain: /Users/x/BKF/.devamp/domain/"`

### 4. Format wiadomości

`Project root:` zawsze jako **pierwsza linia**, przed delegation context i base message:

```
Project root: /Users/x/BKF
Spec: /Users/x/BKF/.devamp/tasks/my-feature/spec.md
```

### 5. Punkty wejścia zmian w `context.py`

- `build_initial_message(task, project_state, cwd)` — dodaje `Project root:` jako prefix
- `build_cascade_message(task, project_state, upstream_agent, cwd)` — j.w.
- `_base_message(task, project_state, cwd)` — zamienia `DOMAIN_DIR` na `{cwd}/{DOMAIN_DIR}`

### 6. Punkty wejścia zmian w `cli.py`

Direct construction (3 miejsca):
- `_start_epic_task()` linia 625 — dodać `Project root:` + absolutne ścieżki
- `_start_adhoc_task()` linia 668 — j.w.
- `_run_discovery()` linia 713 — j.w., plus setup mode (currently `None` → `"Project root: ..."`)

Wywołania context.py (2 miejsca — dorzucić `cwd`):
- `_run_agent_for_task()` linia 294
- `_run_cascade()` linia 419

## Kolejność implementacji

```
1. context.py (cwd param + Project root + absolute paths)
   ↓
2. cli.py (przekazanie cwd + fix direct construction)
   ↓  (równolegle z krokiem 1-2)
3. Wszystkie 6 agentów .md (instrukcja o project root)
   ↓
4. Testy dla context.py
```

Krok 1-2 (orkiestrator) i krok 3 (agenty) mogą iść równolegle. Jeden PR — jedno bez drugiego nie rozwiązuje problemu.

## Ryzyka

| Ryzyko | Poziom | Mitygacja |
|---|---|---|
| Brak testów dla `context.py` | 🟡 Średni | Dodać testy przy okazji tej zmiany |
| Zmiana sygnatury `build_initial_message` | 🟢 Niski | Wewnętrzne API, jedyny consumer to `cli.py` |
| Agenty zignorują instrukcję o project root | 🟡 Średni | Absolutne ścieżki w samych wiadomościach (spec, domain) dają backup |
| Discovery setup mode dostaje message zamiast `None` | 🟢 Niski | `launch_agent()` obsługuje opcjonalny string |

## Rekomendacja dla planner

Jeden task, dwie równoległe ścieżki pracy:
1. **Orkiestrator** (`context.py` + `cli.py` + testy) — zmiany w kodzie Python
2. **Agenty** (6 plików `.md`) — jednolita instrukcja w każdym

Jeden PR, bez faz.

## Routing

Next: planner
Reason: Analiza kompletna, zależności i decyzje domknięte. Planner rozkłada na konkretne zadania dla dev.
