# Plan implementacji: Roadmap backlog on dashboard

## Projekt: devamp (single-repo)

Jeden projekt, trzy moduły, zero koordynacji cross-repo.

### Kolejność implementacji

1. `scanner.py` — parser roadmapy (read-only)
2. `cli.py` — picker epików, zapis statusu, initial message

---

## Krok 1: `scanner.py` — parser roadmapy

### Scope

Nowa funkcja `parse_roadmap()` + dataclass `RoadmapEpic`. Czysto read-only — spójne z resztą modułu.

### Pliki do ruszenia

- `src/devamp/scanner.py` — nowa dataclass + nowa funkcja
- `tests/test_scanner.py` — testy parsera

### Kontrakt

```python
@dataclass
class RoadmapEpic:
    name: str       # nagłówek H2 (bez "## ")
    status: str     # "planned" | "in-progress" | "done"
    content: str    # pełna treść sekcji (od H2 do następnego H2, włącznie z H2)
```

Funkcja:
```python
def parse_roadmap(cwd: Path) -> list[RoadmapEpic]
```

- Czyta `{cwd}/.devamp/domain/roadmap.md`
- Parsuje sekcje H2 → szuka linii `Status: <status>` pod każdym H2
- Zwraca listę wszystkich epików (bez filtrowania — filtr robi `cli.py`)
- Brak pliku → pusta lista (bez wyjątku)
- H2 bez linii `Status:` → pomija epic (nie zgaduje)

### Format roadmapy (źródło prawdy — aktualny `roadmap.md`)

```markdown
## Nazwa epiku
Status: planned

Treść opisowa...

## Kolejny epik
Status: in-progress

Inna treść...
```

Reguły parsowania:
- Sekcja zaczyna się od `## ` (H2)
- `Status:` musi być w pierwszych 3 liniach po H2 (tolerancja na pustą linię)
- `content` = cały blok od linii H2 do następnego H2 (lub EOF), z zachowaniem oryginalnego formatowania

### Testy

| Scenariusz | Input | Oczekiwany wynik |
|---|---|---|
| Happy path — 3 epiki | 3× H2 z różnymi statusami | Lista 3 epików z poprawnymi polami |
| Brak pliku | Nie istnieje `roadmap.md` | Pusta lista |
| Pusty plik | Plik istnieje, brak treści | Pusta lista |
| H2 bez `Status:` | Sekcja bez linii Status | Pomija ten epic |
| Tylko `done` epiki | Wszystkie `Status: done` | Lista z 1+ epicami (filtr robi cli) |
| Treść z wieloma paragrafami | Epic z bullet points, code blocks | `content` zachowuje pełną treść |

### Zależności

Brak — nowa funkcja, nie dotyka istniejącego kodu.

---

## Krok 2: `cli.py` — picker epików + zapis statusu

### Scope

Zmiana `_start_new_task()` — zamiast od razu pokazywać picker agentów, najpierw sprawdza roadmapę. Nowa funkcja pomocnicza `_update_epic_status()` do zapisu statusu w pliku.

### Pliki do ruszenia

- `src/devamp/cli.py` — modyfikacja `_start_new_task()`, nowa `_update_epic_status()`

### Zmiana flow w `_start_new_task()`

**Obecny flow (linia 497-535):**
1. Pokaż picker agentów → user wybiera → launch

**Nowy flow:**
1. `parse_roadmap(cwd)` → lista epików
2. Filtruj: `in-progress` + `planned`
3. **Jeśli lista niepusta** → pokaż picker epików:
   - Na górze: epiki `in-progress` (oznaczone wizualnie, np. `🔄`)
   - Pod spodem: epiki `planned`
   - Na dole: `[A] Ad hoc` (wejście w obecny flow)
4. **Jeśli lista pusta** → obecny flow (picker agentów) — zero zmian w UX
5. Po wybraniu epiku:
   - Jeśli status `planned` → `_update_epic_status()` zmienia na `in-progress` w pliku
   - Buduje initial message: `Domain: .devamp/domain/\n\nRoadmap epic:\n{epic.content}`
   - Launch `product` z tym initial message
   - Dalej normalny flow (`_check_new_tasks()` itd.)
6. `[A]` Ad hoc → obecny flow (picker agentów)

### `_update_epic_status()` — zapis statusu

Logika zapisu żyje w `cli.py` (nie w `scanner.py`). Scanner jest read-only — to decyzja architektoniczna.

```python
def _update_epic_status(cwd: Path, epic_name: str, new_status: str) -> None
```

- Czyta `roadmap.md`
- Znajduje sekcję H2 o danej nazwie
- Zamienia linię `Status: planned` → `Status: in-progress` (precyzyjny find&replace jednej linii)
- Zapisuje plik z powrotem
- Jeśli nie znajdzie — cichy no-op (nie blokuje flow)

### Initial message z epicem

Format wysyłany do product agenta:
```
Domain: .devamp/domain/

Roadmap epic:
## Nazwa epiku
Status: in-progress

Pełna treść epiku z roadmapy...
```

Budowany inline w `_start_new_task()` — spójne z obecnym wzorcem (linia 517 już buduje initial message inline).

### `context.py` — bez zmian

Initial message z epicem budowany przez `cli.py`, nie przez `context.py`. `context.py` obsługuje initial message dla tasków w pipeline (step-based). Epic picker to flow przed utworzeniem taska — `context.py` o epicach nie wie i nie musi.

### Zależności

- Wymaga `parse_roadmap()` z kroku 1 (`scanner.py`)

---

## Lokalizacja

Nie dotyczy — devamp to CLI bez i18n. Nowe teksty to prompty terminalowe (angielski).

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Nadpisanie `roadmap.md` z utratą formatowania | Precyzyjny find&replace jednej linii `Status:`, nie re-write whole file |
| Brak testów na `_start_new_task()` (interaktywny flow) | Nowe unit testy na `parse_roadmap()` pokrywają logikę danych. Flow w `cli.py` to thin glue — manualne testy wystarczą |

## Strategia realizacji

**Sekwencyjnie** — krok 2 zależy od kroku 1. Ale oba w jednym tasku, jeden dev, jeden commit lub dwa.

## Routing

Next: dev
Reason: Jedno repo, plan kompletny, zero otwartych pytań. Dev może implementować.
