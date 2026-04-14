# Przekazywanie ścieżki roota projektu do agentów

## Podsumowanie

Agenty pipeline'u zapisują artefakty `.devamp/` względem swojego bieżącego katalogu roboczego. W scenariuszach multi-repo (i potencjalnie single-repo) agent wchodzi do sub-katalogu żeby pracować na kodzie, a potem tworzy `.devamp/` tam zamiast w roocie projektu. Devamp traci widoczność artefaktów, pipeline się gubi.

Rozwiązanie: devamp przekazuje bezwzględną ścieżkę roota projektu w initial message, agenty używają jej jako kotwicy dla wszystkich operacji na `.devamp/`.

## Stan obecny

### Jak devamp przekazuje kontekst

Initial message per agent zawiera ścieżki relatywne:

| Agent | Initial message (przykład) |
|---|---|
| product | `Domain: .devamp/domain/` |
| architect | `Spec: .devamp/tasks/my-feature/spec.md` |
| planner | `System analysis: .devamp/tasks/my-feature/system-analysis.md` |
| dev | `Plan: .devamp/tasks/my-feature/multi-plan.md` |
| qa | `Handoff: .devamp/tasks/my-feature/qa-input.md` |

Nigdzie nie pojawia się informacja o bezwzględnej ścieżce roota.

### Jak agenty korzystają z `.devamp/`

Wszystkie 6 agentów (discovery, product, architect, planner, dev, qa) mają w instrukcjach ścieżki relatywne:
- Czytanie: `.devamp/domain/*.md`, `.devamp/knowledge/`, `.devamp/tasks/{task}/...`
- Zapis: `.devamp/tasks/{task}/spec.md`, `.devamp/knowledge/<temat>.md`, itp.

### Problem

1. Agent dostaje initial message z relatywną ścieżką (np. `Spec: .devamp/tasks/...`)
2. W trakcie pracy agent zmienia CWD — wchodzi do sub-repo żeby czytać/edytować kod
3. Kiedy agent zapisuje artefakt pipeline'u, `.devamp/` rozwiązuje się względem nowego CWD
4. Artefakt ląduje w sub-repo (np. `~/BKF/beloyal-api/.devamp/tasks/...`)
5. Devamp przy następnym uruchomieniu szuka w `~/BKF/.devamp/` — nie znajduje

## Proponowany kierunek

### 1. Devamp dodaje ścieżkę roota do initial message

Każdy initial message zaczyna się od linii z bezwzględną ścieżką roota projektu — katalogu z którego devamp został uruchomiony.

Format (przykład dla agenta architect):

```
Project root: /Users/x/BKF
Spec: /Users/x/BKF/.devamp/tasks/my-feature/spec.md
```

Zmiana dotyczy **wszystkich agentów** — każdy dostaje `Project root:` jako pierwszą linię. Ścieżki do artefaktów pipeline'u (spec, system-analysis, itp.) też powinny być bezwzględne, dla spójności.

### 2. Instrukcje agentów używają roota

Każdy agent `.md` dostaje instrukcję w sekcji kontekstowej:

> Devamp przekazuje Ci ścieżkę roota projektu w initial message (`Project root: ...`). Wszystkie operacje na katalogu `.devamp/` — zarówno odczyt jak zapis — wykonuj względem tej ścieżki, nie względem bieżącego katalogu roboczego.

Dotyczy:
- **Odczyt:** `.devamp/domain/`, `.devamp/knowledge/`, pliki taska
- **Zapis:** spec.md, system-analysis.md, multi-plan.md, qa-input.md, qa-session.md, pliki knowledge

### 3. Ścieżki w instrukcjach — bezwzględne z roota

Wszędzie gdzie instrukcje agentów mówią o ścieżkach `.devamp/`, dodać kontekst że to jest relatywne do project root, nie do CWD. Przykład zmiany w agencie:

**Było:** "Przeczytaj `.devamp/domain/*.md`"
**Ma być:** "Przeczytaj `{project_root}/.devamp/domain/*.md`" (gdzie `{project_root}` to ścieżka z initial message)

Konkretny sposób sformułowania instrukcji — pytanie dla architect.

## Zakres zmian

### Warstwa orkiestratora (devamp)
- Budowanie initial message — dodanie `Project root:` + zamiana ścieżek relatywnych na bezwzględne

### Warstwa agentów (pliki `.md`)
- Wszystkie 6 agentów — dodanie instrukcji o używaniu project root
- Zmiana przykładów ścieżek z relatywnych na "względem roota"

## Priorytet

Jedno zadanie, bez faz. Zmiana w orkiestratorze i zmiana w instrukcjach agentów powinny iść razem — jedno bez drugiego nie rozwiązuje problemu.

Zacząć od orkiestratora (initial message), potem agenty — bo agenty bez roota w message nie mają z czego korzystać.

## Lokalizacja

Brak nowych tekstów UI — zmiana dotyczy wewnętrznego kontekstu przekazywanego agentom, nie interfejsu użytkownika.

## Pytania dla architect

1. Jak dokładnie sformułować instrukcję w agentach — czy wystarczy jeden paragraf na górze, czy trzeba zmienić każde wystąpienie `.devamp/` w treści agenta?
2. Discovery agent nie dostaje initial message (rozmowa od zera wg dokumentacji) — jak przekazać mu root? Czy discovery w ogóle ma ten problem (pracuje na `domain/`, nie na kodzie)?

## Routing

Next: architect
Reason: Zmiana dotyczy dwóch warstw (orkiestrator + 6 agentów). Architect powinien przejrzeć jak initial message jest budowany i zaproponować konkretną formę zmiany — zarówno w kodzie context.py jak i w treści agentów.
