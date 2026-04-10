# Remove single-repo skip logic

## Podsumowanie

Usunięcie logiki skipowania architect i planner dla single-repo projektów. Wszystkie typy projektów przechodzą pełny pipeline: product → architect → planner → dev → qa. Blokuje pracę nad natalie-claude — devamp przeskakuje architect/planner i kieruje od razu do dev.

## Stan obecny

- `SINGLE_REPO_SKIP = {TaskStep.ARCHITECT, TaskStep.PLANNER}` w `pipeline.py` — hardcodowany skip
- `get_pipeline()` filtruje te kroki dla non-MULTI projektów
- `resolve_step()` przeskakuje architect/planner do dev nawet gdy routing z metadata mówi "architect"
- Dashboard pokazuje `[→ dev]` zamiast `[→ architect]` dla tasków gdzie product zarekomendował architect

## Wymagane zmiany

### 1. `pipeline.py` — usunąć skip logic

- Usunąć `SINGLE_REPO_SKIP`
- `get_pipeline()` — zawsze zwracać `FULL_PIPELINE` niezależnie od `ProjectType`
- `resolve_step()` — uprościć (nie ma kroków do przeskakiwania, ale logika "step not in pipeline" może zostać jako safety net)

### 2. `context.py` — naprawić kontekst architect dla single-repo

W `_base_message()` dla `TaskStep.ARCHITECT`:
```
f"Spec: {task_dir}/spec.md. Repos: {repos_str}"
```
Dla single-repo `repos` jest pustą listą → wychodzi `"Spec: .devamp/tasks/foo/spec.md. Repos: "`. 

Fix: jeśli `repos` jest puste, nie dodawać "Repos:" do wiadomości. Wystarczy: `"Spec: {task_dir}/spec.md"`.

### 3. Do zbadania: agenci nie dostają kontekstu w multi-repo

Zgłoszone przez developera: w multi-repo projekcie kolejni agenci nie mieli informacji od poprzednich agentów (inputu, specek). Developer musiał ręcznie wklejać ścieżki.

Nie udało się zidentyfikować buga z kodu. Hipotezy do sprawdzenia:
- **Resume vs fresh session:** jeśli agent miał zapisaną sesję w metadata (z poprzedniego uruchomienia), devamp robi `claude --resume <session_id>`. Claude CLI przy `--resume` może ignorować pozycyjny argument (initial_message). To znaczy agent startuje bez kontekstu.
- **Weryfikacja:** sprawdzić co robi `claude --resume <id> "message"` — czy message jest przekazywany jako nowy prompt, czy ignorowany.
- Jeśli to potwierdzone — fix: nie resumować sesji przy normalnym pipeline flow, tylko przy explicit `--resume` z dashboardu.

## Testy

- Uruchomić devamp na single-repo projekcie → potwierdzić że dashboard pokazuje `[→ architect]` (nie `[→ dev]`)
- Uruchomić devamp na multi-repo projekcie → potwierdzić że pipeline działa jak wcześniej
- Sprawdzić że architect na single-repo dostaje `"Spec: path/spec.md"` bez pustego "Repos:"

## Poza scope

- Zmiany w definicjach agentów (architect.md, planner.md) — osobne zadanie, agenci potrzebują adaptacji do single-repo kontekstu
- Konfiguracja per-project (opt-in/opt-out z kroków pipeline)
- Update domain/knowledge

## Routing

Next: pipeline
Reason: Dwie chirurgiczne zmiany w pipeline.py i context.py + jeden bug do zbadania. Dev ogarnie bezpośrednio.
