# QA Handoff: Roadmap backlog on dashboard

## Co zrobiono

Dodano picker epików z roadmapy do flow "Start new task". Gdy user tworzy nowy task, devamp najpierw sprawdza `roadmap.md` — jeśli są epiki `planned`/`in-progress`, pokazuje je do wyboru. Po wybraniu epiku zmienia status na `in-progress` i uruchamia `product` z kontekstem epiku.

### Zmienione pliki
- `src/devamp/scanner.py` — nowa dataclass `RoadmapEpic`, nowa funkcja `parse_roadmap()`
- `src/devamp/cli.py` — nowe: `_pick_epic()`, `_update_epic_status()`, `_start_epic_task()`, `_start_adhoc_task()`. Zmieniona: `_start_new_task()` (rozbita na epic/adhoc path)
- `tests/test_scanner.py` — 9 nowych testów dla `parse_roadmap`

### Kluczowe ścieżki do przetestowania

1. **Happy path — epic z roadmapy:**
   - Mając `roadmap.md` z epicem `Status: planned`, uruchom `devamp` → `[N] Start new task`
   - Powinien pojawić się picker epików (nie agent picker)
   - Wybranie epiku → `roadmap.md` zmienia status na `in-progress` + product agent dostaje epic content w initial message

2. **In-progress na górze:**
   - Mając epiki `in-progress` i `planned` — in-progress powinny być na górze z ikoną 🔄

3. **Ad hoc fallback:**
   - Z pickera epików wybrać `[A]` → powinien pojawić się oryginalny agent picker

4. **Brak actionable epików:**
   - Mając roadmapę z samymi `Status: done` → powinien od razu pokazać agent picker (zero zmian w UX)

5. **Brak roadmapy:**
   - Bez pliku `roadmap.md` → oryginalny flow (agent picker)

6. **Zapis statusu:**
   - Po wybraniu epiku `planned` sprawdzić czy `roadmap.md` ma `Status: in-progress`
   - Reszta formatowania pliku powinna być nienaruszona

### Na co zwrócić uwagę
- Initial message do product agenta powinien zawierać `Domain: .devamp/domain/` + `Roadmap epic:` + pełną treść epiku
- `_update_epic_status()` robi precyzyjny replace jednej linii — sprawdzić że nie psuje reszty pliku
- Epiki bez linii `Status:` w roadmapie są ignorowane (nie crashują)

## Routing

Next: qa
Reason: Implementation complete, ready for QA.
