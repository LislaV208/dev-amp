# devamp evolution — domain setup, re-entry, multi-task

## Podsumowanie

Trzy powiązane usprawnienia devampa wynikające z realnych bolączek użytkowania:
1. Brak wiedzy domenowej dla agenta product (musi kopać w kodzie żeby zrozumieć kontekst)
2. Brak możliwości cofnięcia się w pipeline kiedy zmienia się scope
3. Brak możliwości stworzenia wielu tasków z jednej sesji agenta

Fazy są niezależne i deployowalne osobno. Priorytet: domain → re-entry → multi-task.

---

## Faza 1: Domain setup

### Problem

Agent product nie ma wiedzy o firmie, produkcie, użytkownikach. Żeby zrozumieć kontekst, musi parsować kod — co jest nieefektywne i prowadzi do myślenia na poziomie implementacji zamiast na poziomie produktu.

Agent discovery istnieje, ale działa tylko na pustych projektach (automatyczny trigger gdy `ProjectType.EMPTY` i brak `domain/`). Dla istniejących projektów nie ma ścieżki do zbudowania wiedzy domenowej.

### Stan obecny

- `.devamp/domain/` tworzony przez discovery, ale tylko dla nowych projektów
- Discovery odpala się automatycznie na pustym repo (`_run_discovery` w `cli.py`)
- Product agent ma w prompcie "zbadaj kod samodzielnie" — czyta cli.py, pipeline.py itp. żeby wyłuskać sens biznesowy
- `.devamp/knowledge/` istnieje dla wiedzy technicznej (architektura, patterns) — napełniane przez dev/architect podczas pracy
- `context.py` → `_base_message` dla PRODUCT wysyła tylko "Domain: .devamp/domain/" jeśli domain istnieje

### Rozwiązanie

#### 1.1 Discovery agent — rozszerzenie o tryby

Discovery przestaje być agentem jednorazowym "setup". Staje się agentem do rozmów strategicznych o projekcie. Trzy tryby, rozpoznawane z kontekstu (nie wybierane explicite):

| Tryb | Warunek | Rola | Output |
|------|---------|------|--------|
| **Setup** | Brak `domain/` | "Co budujemy od zera?" | `domain/context.md` + `domain/roadmap.md` |
| **Domain capture** | Jest `domain/` ale szczątkowe/brak info o firmie | "Opowiedz mi o firmie, produkcie, użytkownikach" | Uzupełnienie `domain/context.md` |
| **Strategy** | Jest `domain/`, użytkownik wraca z intencją | "Gdzie idziemy? Roadmapa, nowe ficzery, kierunek" | Update `domain/roadmap.md` |

Agent rozpoznaje tryb na podstawie:
- Stanu `domain/` (pusty vs wypełniony)
- Tego co użytkownik mówi na start sesji

Prompt discovery powinien opisywać te 3 tryby i dawać agentowi wytyczne jak się zachować w każdym z nich.

#### 1.2 Konwencja domain/

Dwa pliki jako minimum:

```
.devamp/domain/
├── context.md    # CO JEST — firma, produkt, użytkownicy, ograniczenia, kontekst biznesowy
└── roadmap.md    # CO BĘDZIE — priorytety, MVP, later, out of scope
```

- `context.md` — wiedza faktyczna: kim jest użytkownik, czym zajmuje się firma, jakie są główne aplikacje, jakie ograniczenia (regulacje, SLA), kontekst użycia
- `roadmap.md` — kierunek: co wchodzi do MVP, co na później, co świadomie pomijamy

Dodatkowe pliki (np. `app-mobile.md`) mogą pojawić się organicznie w złożonych projektach, ale nie są wymuszane.

Rozgraniczenie domain vs knowledge:
- `domain/` = wiedza BIZNESOWA — napełniana przez discovery, czytana przez product (i opcjonalnie architect, planner)
- `knowledge/` = wiedza TECHNICZNA — napełniana przez dev/architect podczas pracy, czytana przez dev/architect/planner

#### 1.3 Dashboard + CLI

Nowa opcja na dashboardzie — dostępna gdy projekt nie jest empty:

```
  [1] Continue 'some-task'
  [N] Start new task
  [D] Domain / Strategy
  [Q] Quit
```

`[D]` odpala discovery agenta z kontekstem domain/ (nie tworzy taska — domain jest per-projekt, nie per-task).

Plus CLI shortcut: `devamp domain` — odpala discovery bezpośrednio, bez przechodzenia przez dashboard.

Obecny auto-trigger dla pustych projektów (brak domain/ + EMPTY) pozostaje bez zmian.

#### 1.4 Product agent — zmiana podejścia do kodu

Zmiana w prompcie product agenta:

**Było:** "Zbadaj kod samodzielnie — znajdź ekrany, widgety, logikę domenową, nawigację"

**Ma być:** "Przeczytaj `domain/` na start — tam masz kontekst biznesowy. Do kodu zaglądaj punktowo: obecny stan UI (ekrany, formularze), nawigacja. Jeśli potrzebujesz wizualnego kontekstu — poproś developera o screenshot. Nie parsuj kodu żeby zrozumieć domenę — od tego jest domain/."

Product nadal ma dostęp do kodu, ale priorytet to domain knowledge, nie reverse-engineering z kodu.

---

## Faza 2: Re-entry / cascade

### Problem

Pipeline jest jednokierunkowy: product → architect → planner → dev → qa → done. Kiedy w trakcie pracy (np. na etapie dev) zmienia się scope — dodaje się coś nowego albo zmienia wymaganie — nie ma mechanizmu cofnięcia się do wcześniejszego agenta i kaskadowego odświeżenia downstream artefaktów.

Obecne obejście: opcja `[A] Choose different agent` w post-agent menu pozwala wybrać dowolnego agenta, ale:
- Agent nie wie po co wraca (brak kontekstu delegacji wstecznej)
- Downstream outputy (system-analysis.md, qa-input.md) stają się stale — nikt ich nie aktualizuje
- File-based detection widzi najnowszy output → pipeline "nie zauważa" że upstream się zmienił

### Rozwiązanie

#### 2.1 Świadomy re-entry

Kiedy użytkownik wybiera agenta wcześniejszego niż obecny krok pipeline, devamp rozpoznaje to jako re-entry:

- Informuje: "Downstream artefakty (X, Y) staną się nieaktualne. Po zakończeniu sesji pipeline przeleci ponownie od tego punktu w dół."
- Użytkownik potwierdza

#### 2.2 Kontekst delegacji wstecznej

Agent wracający do wcześniejszego kroku dostaje kontekst:
- "Wracasz z etapu [X]. Obecna spec: {path}. Zaktualizuj ją o nowe wymagania."
- Resume sesji (session tracking działa — agent ma istniejącą sesję do wznowienia)

#### 2.3 Cascade po re-entry

Po zakończeniu sesji upstream agenta, devamp automatycznie proponuje cascade w dół:
- Każdy downstream agent dostaje kontekst: "Upstream artefakt (spec.md / system-analysis.md) się zmienił — zaktualizuj swój output"
- Downstream agenci wznawiają swoje sesje (nie startują od zera)
- Cascade idzie po kolei: product → architect → planner → dev (zgodnie z pipeline)

#### 2.4 Metadata

Nowy koncept w `task-metadata.json` do śledzenia re-entry (pytanie dla architect: jaka struktura?).

Downstream pliki NIE są kasowane — agenci je aktualizują, nie piszą od nowa.

---

## Faza 3: Multi-task output

### Problem

Jedna sesja z product/discovery agentem naturalnie rodzi więcej niż jeden task — np. "paczka zadań" w ramach jednego modułu, albo kilka tematów wynikających z jednej rozmowy strategicznej. Devamp wymusza 1 sesja = 1 task, co jest nienaturalne i zmusza do sztucznego cięcia rozmów.

### Rozwiązanie

#### 3.1 Agent tworzy wiele katalogów

Product/discovery agent może stworzyć N katalogów w `.devamp/tasks/`, każdy z osobnym spec.md. Agent sam decyduje o podziale na podstawie rozmowy z użytkownikiem.

#### 3.2 Obsługa w devampie

`_check_new_tasks()` obsługuje N nowych tasków (już teraz skanuje wszystkie nowe katalogi, ale zwraca tylko pierwszy — `return new_tasks[0].name`).

Po sesji agenta, devamp pokazuje listę nowych tasków i pyta od którego zacząć:

```
New tasks created:
  1. formularz-zamowien
  2. walidacja-stanow  
  3. powiadomienia-email

Which task to continue with? [1]
```

Pozostałe taski lądują na dashboardzie jako `→ product` (lub `→ dev` jeśli spec jest kompletny).

#### 3.3 Kontekst między taskami

Taski z jednej sesji mogą mieć powiązanie (pytanie dla architect: czy potrzebna koncepcja "grupy tasków" w metadata, czy wystarczy timestamp?).

---

## Lokalizacja

Nie dotyczy — devamp to narzędzie CLI, UI jest w języku angielskim (komunikaty w cli.py). Nowe komunikaty:

| Kontekst | Tekst |
|----------|-------|
| Dashboard option | `[D] Domain / Strategy` |
| Re-entry warning | `Downstream artifacts (X, Y) will become stale. Pipeline will re-run from this point. Continue?` |
| Multi-task picker | `New tasks created:` / `Which task to continue with?` |
| Cascade prompt | `Upstream artifact changed. Continue cascade to [agent]?` |

---

## Priorytety

1. **Faza 1 (domain setup)** — niezależna, natychmiastowa wartość. Product agent staje się 10x bardziej użyteczny z dobrą wiedzą domenową.
2. **Faza 2 (re-entry)** — wymaga zmian w metadata + pipeline + context. Bardziej złożone, ale rozwiązuje realną bolączkę.
3. **Faza 3 (multi-task)** — wymaga zmian w product prompt + scanner + dashboard. Rozwiązuje problem który sam się ujawnił podczas tworzenia tego taska.

Każda faza jest deployowalna osobno. Faza 1 nie blokuje fazy 2, faza 2 nie blokuje fazy 3.

---

## Pytania dla architect

- **Re-entry metadata**: Jaka struktura w `task-metadata.json` do śledzenia re-entry i cascade? Czy wystarczy pole `re_entry_from` + `cascade_pending: [agent_list]`, czy potrzebne coś bardziej złożone?
- **Cascade flow**: Czy cascade powinien być automatyczny (devamp odpala kolejnych agentów bez pytania) czy semi-automatyczny (pyta po każdym kroku)?
- **Multi-task grouping**: Czy taski z jednej sesji powinny mieć powiązanie w metadata (np. `group_id`)? Czy wystarczy wspólny timestamp?
- **Discovery session tracking**: Discovery nie jest per-task (domain jest per-projekt). Czy sesja discovery powinna być śledzona osobno (nie w task-metadata)?

---

## Routing

Next: architect
Reason: Task touches multiple modules (cli, pipeline, metadata, context, scanner) across 3 phases. Impact analysis needed especially for re-entry cascade mechanism and multi-task metadata structure.
