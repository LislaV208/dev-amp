# Multi-plan — Przekazywanie ścieżki roota projektu do agentów

## Projekt: devamp

Jeden projekt, jeden PR. Dwie równoległe ścieżki pracy.

---

## Ścieżka 1: Orkiestrator Python

### 1.1 `context.py` — core logic

**Scope:**
- Dodać parametr `cwd: Path` do `build_initial_message()`, `build_cascade_message()`, `_base_message()`
- `_base_message()` linia 59: zamienić `DOMAIN_DIR` na `f"{cwd}/{DOMAIN_DIR}"` (absolutna ścieżka domain)
- Obie publiczne funkcje: dodać prefix `Project root: {cwd}\n` przed resztą wiadomości
- Po zmianie `build_initial_message` **nigdy nie zwraca `None`** — zawsze ma przynajmniej `Project root:`

**Pliki:** `src/devamp/context.py`

**Kontrakt — format wiadomości:**

Pipeline flow (z domain):
```
Project root: /Users/x/my-project
Domain: /Users/x/my-project/.devamp/domain/
```

Pipeline flow (architect):
```
Project root: /Users/x/my-project
Spec: /Users/x/my-project/.devamp/tasks/my-feature/spec.md
```

Cascade:
```
Project root: /Users/x/my-project
Upstream artifact changed (/Users/x/my-project/.devamp/tasks/my-feature/spec.md). Review the updated input and update your output accordingly.

Spec: /Users/x/my-project/.devamp/tasks/my-feature/spec.md
```

Z delegation context:
```
Project root: /Users/x/my-project
Delegated from architect: /Users/x/my-project/.devamp/tasks/my-feature/system-analysis.md
Reason: Analiza kompletna.

System analysis: /Users/x/my-project/.devamp/tasks/my-feature/system-analysis.md
```

**`Project root:` zawsze pierwsza linia. Bezwzględna ścieżka. Bez trailing slash.**

**Sygnatury po zmianie:**
```python
def build_initial_message(task: TaskState, project_state: ProjectState, cwd: Path) -> str
def build_cascade_message(task: TaskState, project_state: ProjectState, upstream_agent: str, cwd: Path) -> str
def _base_message(task: TaskState, project_state: ProjectState, cwd: Path) -> str | None
```

Uwaga: return type `build_initial_message` zmienia się z `str | None` na `str`.

### 1.2 `cli.py` — callsites

**Scope:** Dostosować 5 miejsc do nowych sygnatur + absolutne ścieżki w direct construction.

**Zmiany:**

| Linia (orientacyjna) | Funkcja | Co zmienić |
|---|---|---|
| ~294 | `_run_agent_for_task` | `build_initial_message(..., cwd)` — dorzucić `cwd` |
| ~419 | `_run_cascade` | `build_cascade_message(..., cwd)` — dorzucić `cwd` |
| ~625 | `_start_epic_task` | `f"Project root: {cwd}\nDomain: {cwd / DOMAIN_DIR}/\n\nRoadmap epic:\n{epic.content}"` |
| ~668 | `_start_adhoc_task` | `f"Project root: {cwd}\nDomain: {cwd / DOMAIN_DIR}/"` gdy domain, `f"Project root: {cwd}"` gdy brak |
| ~713 | `_run_discovery` | `f"Project root: {cwd}\nDomain: {cwd / DOMAIN_DIR}/"` gdy domain, `f"Project root: {cwd}"` gdy brak (zamiast `None`) |

**Pliki:** `src/devamp/cli.py`

**Ryzyko:** `_run_discovery` dotychczas przekazywał `None` w setup mode → teraz zawsze string. Sprawdzić że `launch_agent("discovery", "Project root: ...")` działa poprawnie (launcher przyjmuje `str | None`).

### 1.3 Testy — `test_context.py`

**Scope:** Nowy plik testowy. Pokryć:

1. `build_initial_message` — każdy krok pipeline (PRODUCT z/bez domain, ARCHITECT z/bez repos, PLANNER, DEV z plan/bez, QA)
2. `build_initial_message` — zawsze zawiera `Project root:` jako pierwszą linię
3. `build_initial_message` — nigdy nie zwraca `None`
4. `build_initial_message` — delegation context (z routing w metadata)
5. `build_cascade_message` — zawiera `Project root:` + cascade context + base message
6. `_base_message` — DOMAIN_DIR jest absolutny (zawiera cwd)

**Pliki:** `tests/test_context.py`

---

## Ścieżka 2: Instrukcje agentów (6 plików .md)

**Scope:** Dodać jeden paragraf do każdego agenta — instrukcja o project root.

**Treść (identyczna w każdym):**

> **Devamp przekazuje Ci bezwzględną ścieżkę roota projektu w initial message (`Project root: ...`). Wszystkie ścieżki `.devamp/` w tym dokumencie — `domain/`, `knowledge/`, `tasks/` — rozwiązuj względem tego roota, nie względem bieżącego katalogu roboczego. Gdy zmieniasz katalog w trakcie pracy (np. wchodzisz do sub-repo), `.devamp/` nadal musi wskazywać na `{project_root}/.devamp/`.**

**Umiejscowienie:** Po sekcji "Wiedza domenowa" (lub "Input" w qa.md), przed pierwszą sekcją o workflow.

**Pliki:**
- `src/devamp/agents/discovery.md`
- `src/devamp/agents/product.md`
- `src/devamp/agents/architect.md`
- `src/devamp/agents/planner.md`
- `src/devamp/agents/dev.md`
- `src/devamp/agents/qa.md`

**Nic więcej w agentach nie ruszać** — nie zmieniać 30+ wystąpień `.devamp/` w treści. LLM rozumie kontekst z jednego paragrafu.

---

## Strategia realizacji

**Równolegle:** Ścieżka 1 (Python) i Ścieżka 2 (agenty .md) są niezależne.

**W ścieżce 1 sekwencyjnie:** context.py → cli.py → testy (cli zależy od nowej sygnatury context).

**Jeden commit, jeden PR.**

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| `build_initial_message` zwraca `str` zamiast `str \| None` — breaking change | Jedyny consumer to cli.py, zmieniany w tym samym PR |
| Discovery setup mode: `None` → string | Sprawdzić `launch_agent` — przyjmuje `str \| None`, string jest valid |
| Agenty zignorują instrukcję | Backup: same wiadomości mają absolutne ścieżki |

---

## Routing

Next: dev
Reason: Plan kompletny, kontrakty zdefiniowane, jeden projekt — dev może implementować.
