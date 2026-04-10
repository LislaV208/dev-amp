# devamp — CLI orkiestrator pipeline'u agentów AI

## Wizja

Jedno narzędzie CLI które eliminuje ręczny klej między agentami w pipeline tworzenia oprogramowania. Devamp wie gdzie jesteś w procesie, uruchamia odpowiedniego agenta z odpowiednim kontekstem i prowadzi przez kolejne kroki.

## Problem

Pipeline składa się z 6 agentów (discovery → product → architect → planner → dev → qa), każdy uruchamiany ręcznie przez `claude --agent`. Developer musi:
- pamiętać który agent jest następny
- wklejać ścieżki do specyfikacji
- śledzić stan pipeline ręcznie

## Rozwiązanie

Standalone Python CLI (`devamp`) który jest cienkim wrapperem wokół `claude` CLI.

### Jak działa

1. Skanuje CWD i `.devamp/` — rozpoznaje typ projektu i stan pipeline
2. Decyduje który agent jest następny
3. Buduje initial message z kontekstem (ścieżki do specyfikacji, lista repozytoriów)
4. Uruchamia `claude --agent {agent}.md` jako interaktywny proces
5. Po zakończeniu sesji weryfikuje czy oczekiwany output powstał
6. Przechodzi do następnego kroku

### Kluczowa zasada

Każdy agent to osobna, interaktywna sesja `claude` CLI. User rozmawia z agentem bezpośrednio. Devamp nie pośredniczy w konwersacji — tylko uruchamia i przekazuje kontekst.

## Rozpoznawanie kontekstu projektu

Devamp rozpoznaje typ projektu na podstawie struktury katalogów (bez LLM):

| Struktura CWD | Typ projektu |
|---|---|
| Pusty katalog | Nowy projekt |
| Jeden `.git` / jeden projekt z kodem | Single-repo |
| Wiele subdirów z `.git` | Multi-repo |

Wszystkie typy projektów przechodzą pełny pipeline: product → architect → planner → dev → qa.

Discovery jest używany tylko przy nowych projektach (pusty katalog) lub ręcznie z dashboardu.

## Struktura plików

Wszystkie pliki generowane przez pipeline żyją w ukrytym katalogu `.devamp/`:

```
my-project/
├── .devamp/
│   ├── config.yaml              # opcjonalnie: overrides
│   ├── domain/                  # wiedza o projekcie (z discovery)
│   │   ├── myapp.md
│   │   └── roadmap.md
│   └── tasks/                   # per-task pipeline
│       ├── email-notifications/
│       │   ├── spec.md              # output: product
│       │   ├── system-analysis.md   # output: architect
│       │   ├── multi-plan.md        # output: planner
│       │   ├── qa-input.md          # output: dev
│       │   └── qa-session.md        # output: qa
│       └── user-avatars/
│           └── spec.md
├── backend/
├── frontend/
└── .gitignore                   # zawiera .devamp/
```

## Stan pipeline per task

Devamp ustala stan taska na podstawie:
1. Routing z metadata (`last_routing_next` w `task-metadata.json`) — priorytet
2. Obecności plików w `.devamp/tasks/{task}/` — fallback

```
qa-session.md  istnieje → done
qa-input.md    istnieje → qa
multi-plan.md  istnieje → dev
system-analysis.md istnieje → planner
spec.md        istnieje → architect
(pusty katalog)            → product
```

## Kontekst przekazywany agentom

Devamp buduje initial message dla każdego agenta:

| Agent | Initial message |
|---|---|
| discovery | (brak — rozmowa od zera) |
| product | "Domain: .devamp/domain/" |
| architect | "Spec: .devamp/tasks/{task}/spec.md" (+ "Repos: ..." dla multi-repo) |
| planner | "System analysis: .devamp/tasks/{task}/system-analysis.md" |
| dev | "Plan: .devamp/tasks/{task}/multi-plan.md" lub "Spec: .devamp/tasks/{task}/spec.md" |
| qa | "Handoff: .devamp/tasks/{task}/qa-input.md" |

## CLI interface

```bash
devamp                              # skanuje .devamp/, pokazuje stan, prowadzi dalej
devamp domain                       # uruchamia discovery agenta bezpośrednio
devamp --resume                     # wraca do ostatniego aktywnego taska
```

## Po QA — decyzja usera

Gdy QA zakończy sesję, devamp pyta:
- **Fix teraz** — wraca do dev z bugami, potem ponownie QA (pętla)
- **Zapisz na później** — QA findings zostają w qa-session.md jako backlog

## Technologia

- Python CLI (typer)
- 7 modułów: cli, scanner, pipeline, context, launcher, metadata, routing

## Czego devamp NIE robi

- Nie pośredniczy w konwersacji z agentem
- Nie trzyma własnego state'u poza plikami w `.devamp/`
- Nie wymaga konfiguracji żeby działać (sensowne defaults)
- Nie jest daemon/server — uruchamiasz, używasz, kończy się
