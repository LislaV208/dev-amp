# devamp — Domain Context

## Co to jest

CLI orkiestrator pipeline'u agentów AI. Automatyzuje przepływ od analizy produktowej do przetestowanego kodu. Thin wrapper na Claude CLI — wartość jest w orkiestracji (kolejność, kontekst, routing) i w definicjach agentów, nie w samym kodzie narzędzia.

## Kto używa

Na ten moment jeden użytkownik — autor, solo developer. Używa zarówno do projektów prywatnych jak i w pracy zawodowej.

Otwarcie na zewnątrz (open source, udostępnienie w firmie) jest realne, ale nie jest aktywnym celem. Narzędzie nie jest projektowane pod community, ale architektura na to pozwala.

## Kontekst użycia

### Praca (główny use case)

Duży system (CM — zarządzanie myjniami) z wieloma modułami. Każdy moduł ma swój stack (web + mobile + backend), do tego mikroserwisy i wewnętrzne biblioteki współdzielone między projektami.

Typowy flow: developer dostaje zadanie → musi zrozumieć kontekst produktowy → sprawdzić zależności systemowe między modułami → ustalić kontrakty (np. backend-frontend) → dopiero wtedy implementować.

Bez devampa: otwierasz kod jednego projektu, analizujesz, odkrywasz że musisz zajrzeć do backendu, potem do innego projektu bo są zależności — łatwo zgubić kontekst i wątek. Podejście "od kodu w górę" zamiast "od zrozumienia w dół".

Z devampem: systematyczne rozeznanie zanim dotkniesz kodu. Architect patrzy szeroko na zależności. Planner ustala kontrakty i spójność danych. Product zapewnia zrozumienie co i po co.

### Projekty prywatne

Mniejsza skala, mniejsza wartość z architecta/plannera (single-repo skipuje te kroki). Wartość: konkretna wizja dzięki discovery/product zanim przejdzie do implementacji.

### Świeży projekt od zera

Jeszcze nie przetestowane w praktyce. Discovery agent ma tu pokryć fazę "od pomysłu do zrozumienia zakresu".

## Główna wartość

Nie sam kod na końcu pipeline'u, tylko **systematyczne rozeznanie przed implementacją**:
- Kontekst produktowy (co dokładnie implementuję i po co)
- Analiza zależności systemowych (co jeszcze jest powiązane, czego sam bym nie wychwycił)
- Kontrakty i spójność danych (planner zapewnia że frontend i backend mówią tym samym językiem)

## Sukces

- Flow bez tarcia — nie walczysz z narzędziem, nie łatasz ręcznie, nie skaczesz między sesjami
- Agenci dobrze zdefiniowani — każdy wie co ma robić, nie produkuje braków które cofają pipeline
- Szybkość i jakość pracy wyższa niż bez devampa

## Stan projektu

Narzędzie CLI istnieje od ~2 dni (stan na 2026-04-10). Wcześniej agenci byli używani ręcznie — devamp automatyzuje to co autor robił manualnie. Za wcześnie na wnioski co konkretnie wymaga poprawy — potrzeba czasu z realnym użyciem.
