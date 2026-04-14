# devamp — Roadmap

## MVP
Status: done

Pipeline działa end-to-end:
- 6 agentów: discovery → product → architect → planner → dev → qa
- Single-repo skip (architect + planner)
- Dashboard z persistent loop
- Routing między agentami (agent mówi kto jest następny)
- Session tracking (resume sesji)
- Re-entry z cascade (cofanie do wcześniejszego agenta)
- Multi-task output (product/discovery tworzy N tasków)
- Domain knowledge (context.md + roadmap.md)

## Reduce friction w trybie interaktywnym
Status: planned

Wkurzające: gdy agent wykonuje złożone komendy (np. `cd ... && ... && ...`), Claude CLI wewnątrz devampa prosi o zatwierdzenie każdej z nich. Rozbija flow.

Kierunek: dać Claude CLI odpalanemu przez launcher większe zaufanie — allowlist, skip-permissions dla bezpiecznych operacji, albo inny mechanizm który zredukuje liczbę przerwań bez otwierania furtki na rzeczy destrukcyjne.

Mały epik, można zrobić niezależnie od reszty. Jest też warunkiem koniecznym trybu `--auto` (AI nie będzie klikać "yes"), ale ma wartość samodzielną dla trybu interaktywnego.

## Tryb `--auto` — delegacja AI→AI
Status: planned

Docelowy scenariusz: użytkownik omawia coś ze swoim "głównym asystentem AI", asystent rozumie zadanie i przechodzi do pracy z devampem, zastępując człowieka w rozmowie z agentami pipeline'u.

Zakres:
- Flaga `--auto` w CLI włączająca tryb nie-interaktywny
- Agenci mają być bardziej samodzielni — zadają tylko **krytyczne** pytania (definicja "krytyczne" do ustalenia)
- Techniczny kanał komunikacji asystent ↔ devamp (do rozeznania — API, stdin/stdout JSON, pliki pytań/odpowiedzi, długa sesja sterowana przez asystenta — opcje otwarte)
- Prawdopodobnie osobny zestaw promptów agentów albo rozszerzenie istniejących o tryb auto
- Obsługa pełnego zakresu: zarówno tworzenie projektu od zera (discovery), jak i utrzymanie / rozwój istniejącego projektu z wypełnionym domainem

Duży epik, wieloetapowy, do rozbicia na mniejsze kroki. Fundamentalna zmiana kierunku — devamp przestaje być wyłącznie narzędziem dla człowieka.

## Out of scope
Status: done

Poza zakresem produktu — spisane dla jasności kierunku:
- Nie jest IDE ani edytorem — to orkiestrator
- Nie zastępuje Claude CLI — jest wrapperem na niego
- Nie jest platformą do budowania agentów — agenci są sztywno zdefiniowani w pipeline
- ~~Tylko dla człowieka~~ — po dodaniu trybu `--auto` devamp będzie obsługiwał również scenariusz "inny AI jako użytkownik"
