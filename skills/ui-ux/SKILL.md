# Skill: UI/UX

Generyczny skill dla projektów mobilnych i webowych. Ładuj gdy:
- **Product** — projektujesz nowy ekran, flow, lub oceniasz UX przed napisaniem spec
- **Dev-single** — implementujesz UI i chcesz sprawdzić czy robisz to dobrze
- **QA** — oceniasz czy obecny UI/UX spełnia standardy

Wiedza domenowa (jak ma wyglądać konkretna apka) jest w `_domain/` projektu — tu są tylko generyczne zasady.

---

## 1. Hierarchia informacji

**Zasada:** Użytkownik skanuje, nie czyta. Najważniejsza informacja musi być widoczna w < 2 sekundy.

- Główny identyfikator (imię, nazwa, tytuł) — największy, bold, góra karty
- Akcja kontekstowa — blisko identyfikatora, nie na końcu listy
- Szczegóły (telefon, opis, data) — mniejsze, niżej, wyciszone
- Metadane (czas, ID) — najmniejsze, prawy róg, nieagresywne

**Sygnał że jest źle:** Developer patrzy na kartę i nie wie co jest najważniejsze.

---

## 2. Przyciski i akcje

**Zasada:** Jeden ekran, jedna główna akcja. Jeśli jest kilka — hierarchia wizualna musi ją odzwierciedlać.

- Primary action (CTA) — wyróżniony kolorem, duży, jeden na ekran
- Secondary action — outlined lub ghost button
- Destruktywna akcja — zawsze z potwierdzeniem, czerwona
- FAB (floating action button) — dla głównej akcji gdy lista jest długa

**Mobile:** Przyciski minimum 44x44pt (Apple HIG). Kciuk dociera łatwiej do dołu ekranu — główne akcje tam.

**Sygnał że jest źle:** Użytkownik waha się co kliknąć, albo klika nie to co chce.

---

## 3. Feedback i stany

Każda akcja użytkownika musi dostać odpowiedź w < 100ms. Jeśli operacja trwa dłużej — loading state.

| Stan | Co pokazać |
|---|---|
| Loading | Skeleton lub spinner — nigdy pusty ekran |
| Sukces | Toast lub zmiana UI — nie modal jeśli można uniknąć |
| Błąd | Inline, przy elemencie który wywołał błąd — nie tylko ogólny komunikat |
| Pusty stan | Ilustracja lub komunikat + CTA — nigdy pusta biała strona |

**Undo pattern:** Dla destruktywnych akcji (usuń, wyślij) — toast z opcją cofnięcia przez 3-5s zamiast potwierdzenia przed akcją. Szybciej, mniej frykcji.

**Sygnał że jest źle:** Użytkownik klika i nie wie czy coś się stało.

---

## 4. Formularze

- Label zawsze widoczny (nie tylko placeholder — znika po wpisaniu)
- Walidacja inline, przy polu — nie po submit całego formularza gdy można wcześniej
- Błąd walidacji: czerwony border + komunikat pod polem, pole pozostaje otwarte
- Kolejność pól = kolejność myślenia użytkownika (imię przed telefonem, nie odwrotnie)
- Klawiatura odpowiednia do pola: `type="tel"` dla telefonu, `type="email"` dla emaila
- Submit button — aktywny zawsze, błędy pokazuj po próbie — nie blokuj przycisku

**Sygnał że jest źle:** Użytkownik musi scrollować żeby zobaczyć błąd.

---

## 5. Kolory i kontrast

- Kontrast tekst/tło: minimum 4.5:1 (WCAG AA) dla tekstu normalnego
- Nie przekazuj informacji tylko kolorem — dodaj ikonę lub label
- Dark mode: jeśli nie projektujesz świadomie dla dark mode — wymuś `data-theme="light"` zamiast liczyć na szczęście
- Akcenty: jeden kolor primary, jeden danger (czerwony), jeden success (zielony) — nie więcej

**Sygnał że jest źle:** Na słońcu tekst nieczytelny, albo ktoś daltonista nie rozumie statusów.

---

## 6. Typografia

- Minimum 16px dla tekstu body na mobile (mniejsze = zoom przez użytkownika)
- Maksimum 2-3 rozmiary czcionki na ekranie
- Line-height 1.4-1.6 dla tekstu do czytania
- Bold tylko dla naprawdę ważnych rzeczy — jeśli wszystko bold, nic nie wyróżnione

---

## 7. Spacing i layout

- Consistent spacing scale: 4/8/12/16/24/32px — nie ad-hoc marginesy
- Touch targets minimum 44x44pt — karty klikalne w całości, nie tylko przycisk
- Padding wewnątrz kart: minimum 16px
- Grupowanie: rzeczy powiązane blisko siebie, rzeczy niepowiązane z odstępem

---

## 8. Nawigacja i flow

- Użytkownik zawsze wie gdzie jest (breadcrumb, nagłówek ekranu, aktywna zakładka)
- Back/anuluj zawsze dostępne — nie blokuj użytkownika w ekranie
- Głębokość nawigacji: max 3 poziomy dla prostych apek
- Modal/bottom sheet: dla akcji kontekstowych, nie dla głównego contentu

---

## 9. Checklista per rola

### Product — przed napisaniem spec
- [ ] Wiem kto jest użytkownikiem i w jakim kontekście używa (stresujący? spokojny? jedną ręką?)
- [ ] Zidentyfikowałem jedną główną akcję per ekran
- [ ] Hierarchia informacji jest jasna (co jest najważniejsze na karcie/ekranie?)
- [ ] Opisałem wszystkie stany: loading, sukces, błąd, pusty
- [ ] Nie zaprojektowałem flow który wymaga > 3 tapów do głównej akcji

### Dev-single — przed committem
- [ ] Touch targets ≥ 44pt
- [ ] Kontrast tekst/tło ≥ 4.5:1
- [ ] Dark mode: wymuszony motyw LUB świadomie zaprojektowany
- [ ] Błędy walidacji widoczne inline, modal nie zamyka się przy błędzie
- [ ] Stany loading/error/empty zaimplementowane (nie tylko happy path)
- [ ] Klawiatura odpowiednia do pól formularza
- [ ] Formatowanie danych czytelne dla człowieka (telefon, daty)

### QA — przed zamknięciem sesji
- [ ] Na mobile (emulacja 375px) wszystko czytelne bez zoomu?
- [ ] Główna akcja widoczna od razu bez scrollowania?
- [ ] Każda akcja daje feedback < 1s?
- [ ] Błąd walidacji widoczny i zrozumiały?
- [ ] Pusty stan (brak danych) wygląda zaprojektowanie?
- [ ] Dark mode sprawdzony?
- [ ] Tapping w pobliżu przycisku działa (target area wystarczająca)?

---

## 10. Antypatterny (unikaj)

| Antypattern | Problem | Zamiast |
|---|---|---|
| `opacity: 0.5` na "nieaktywnych" elementach | Wygląda jak bug, nie design | Świadomy styl: szare tło, szary tekst |
| Komunikat błędu tylko na górze strony | Użytkownik nie wie które pole | Inline, przy polu |
| Modal na błąd walidacji | Zamknie się przed przeczytaniem | Zostaw formularz otwarty |
| Placeholder zamiast label | Znika po wpisaniu | Label nad polem |
| Wszystko bold lub wszystko kolorowe | Brak hierarchii | 1-2 akcenty, reszta neutralna |
| Pusta strona gdy brak danych | Użytkownik myśli że błąd | Empty state z komunikatem |
| Tylko kolor sygnalizuje status | Nieczytelne dla daltonistów | Kolor + ikona + label |
