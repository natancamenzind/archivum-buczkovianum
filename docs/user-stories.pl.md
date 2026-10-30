# User stories — Archivum Buczkovianum

Tłumaczenie `docs/user-stories.md`. W razie rozbieżności obowiązuje wersja angielska.

Źródła: `docs/PROJECT_BRIEF.md`, brudnopis ze spotkania 10.10.26 i plik Figma „archiwum-buczkowski-model”, strona „po korekcie”.

## Jak czytać ten dokument

- Story jest gotowe, gdy spełnione są wszystkie jego kryteria akceptacji (AC). Jedno story to jedna gałąź i jeden PR; obie mają w nazwie jego ID.
- **RA (Relacyjny archiwista)** to czytelnik serwisu: anonimowy, nigdy się nie loguje. **WR (Wnikliwa Redaktorka)** pracuje w panelu administracyjnym; wszystkie redaktorki mają te same uprawnienia.
- Każde story należy do v1 i jest obowiązkowe, chyba że ma oznaczenie **(Opcjonalne)**: robimy je, jeśli starczy czasu. Rozdział 5 wymienia to, czego nie robimy w v1.
- Zasady R-01 do R-12 obowiązują na każdej publicznej stronie. Story odwołują się do nich zamiast je powtarzać.
- Tekst w cudzysłowie to dokładne brzmienie w interfejsie. Interfejs używa wyłącznie polskich terminów ze słownika.

## Słownik

| Termin | Znaczenie |
|--------|-----------|
| Utwór | Utwór jako idea, niezależnie od wydania czy dokumentu, np. „Wertepy”. |
| Wydanie | Wydanie utworu: rok, wydawnictwo, miejsce. |
| Maszynopis | Maszynopis utworu: skan + tekst OCR. Należy do dokładnie jednego utworu. |
| Główny maszynopis | Jedyny tagowany maszynopis utworu. Jego fragmenty pokazujemy na stronie utworu. |
| Zapisek | Rękopiśmienny materiał autora: strona notesu, karta, brudnopis, notatka. Może być w relacji z wieloma utworami. |
| Tekst sekundarny | Recenzja, opracowanie, list lub nagranie o utworze. Może być w relacji z wieloma utworami. |
| Materiał kontekstowy | Dowolne medium + opis. Może być w relacji z wieloma utworami. |
| Materiał wizualny | Materiał kontekstowy, który jest obrazem: zdjęcie lub skan ilustracyjny. |
| Powiązanie z utworem | Relacja między utworem a tekstem sekundarnym lub materiałem kontekstowym. Można je otagować. |
| Tag | Nazwa dla relacji, łącząca fragmenty i zapiski: słowo klucz z Buczkowskiego (np. „dezerter”) albo nasza interpretacja (np. „wielokulturowość”). |
| Fragment | Otagowany zakres tekstu (OCR lub tekstu litego), z opcjonalną sygnaturą, lokalizacją i opisem. |
| Wystąpienie | Jeden opublikowany element z danym tagiem: fragment, cały byt albo powiązanie z utworem. |
| Sygnatura | Instytucja + numer, wyświetlane jako „ML, sygn. 1618”. Fragment ma własny numer („ML, sygn. 1618.0009”), a instytucję dziedziczy po dokumencie. |
| Byt | Każdy obiekt archiwum, który ma własną stronę: utwór, maszynopis, tag, zapisek, tekst sekundarny, materiał kontekstowy. |
| Tekst lity | Zwykły tekst bez skanu, np. transkrypcja listu. |

---

## 1. Zasady dla każdej publicznej strony

**R-01 Przechodzenie między bytami.** Każdy byt pokazany na stronie linkuje do własnej strony. Fragment nie ma własnej strony: linkuje do dokumentu źródłowego, przewiniętego do tego fragmentu.

**R-02 Puste bloki.** Jeśli na stronie nie ma treści dla danego bloku, okienko się nie wyświetla: bez nagłówka i bez komunikatu o braku treści.

**R-03 Powiązane utwory.** Kolumna kontekstu na stronie każdego bytu pokazuje listę powiązanych utworów. Strona utworu pokazuje w tym miejscu listę wydań.

**R-04 Typ i tytuł.** Każdy byt ma typ i tytuł. Wszędzie, gdzie pojawia się poza swoją stroną (wyszukiwarka, listy, karty), pokazujemy typ razem z tytułem.

**R-05 Układ strony bytu.** Strony utworu, maszynopisu, tagu, zapisku, tekstu sekundarnego i materiału kontekstowego mają jeden układ:

1. hiro: ciemny pas z linią typu (np. „Utwór · Leopold Buczkowski · 1947”), tytułem i opisem;
2. kolumna kontekstu po lewej;
3. kolumna główna;
4. kolumna tagów po prawej;
5. blok materiałów kontekstowych (R-08) pod kolumnami, jeśli strona go ma.

Na telefonie kolejność to: kolumna główna, kontekst, tagi, materiały kontekstowe.

**R-06 Tylko opublikowane.** Publicznie widać tylko byty ze statusem `published`. Szkice nie pojawiają się na listach ani w wyszukiwarce, a ich adresy zwracają anonimowym czytelnikom 404. Zalogowana redaktorka, wchodząc na adres szkicu, widzi stronę z banerem szkicu (US-WR-13). Szkice nigdy nie pojawiają się na listach, w podglądach ani w wyszukiwarce, także dla redaktorek.

**R-07 Nagłówek, menu, stopka.**

- Nagłówek: nazwa serwisu i podtytuł (link do strony głównej), link „O archiwum”, pasek wyszukiwania.
- Menu główne: Strona główna, Utwory, Maszynopisy, Tagi. Na komputerze jest w stopce. Na telefonie jest dolnym paskiem, a wyszukiwarka zamienia się w ikonę lupy w nagłówku.
- Stopka: nazwa serwisu i podtytuł, menu główne (na komputerze), informacja o finansowaniu.

Aktywna pozycja menu: strona główna → Strona główna; lista utworów i utwór → Utwory; lista maszynopisów i maszynopis → Maszynopisy; lista tagów i tag → Tagi. Pozostałe strony nie mają aktywnej pozycji.

**R-08 Blok materiałów kontekstowych.** Blok „Materiały kontekstowe” ma dwie części:

1. „Teksty sekundarne”: numerowana lista tekstów sekundarnych i nieobrazowych materiałów kontekstowych. Pierwsza linia: autor i tytuł. Druga linia: źródło (wydawnictwo, miejsce, rok, strony).
2. „Materiały wizualne”: galeria materiałów wizualnych. Każdy ma miniaturę i podpis: tytuł i sygnaturę.

Każda strona określa, które elementy pokazuje.

**R-09 Liczniki i podglądy.**

- Nagłówek sekcji pokazuje licznik: „3” albo „2 z 24”, gdy sekcja jest podglądem.
- Podgląd pokazuje pierwsze `PREVIEW_LIMIT` elementów (jedno ustawienie, domyślnie 2): najpierw wyróżnione fragmenty, potem reszta w kolejności tekstu. Kończy się linkiem z celem i liczbą, np. „Wszystkie fragmenty (24)”.
- Link „wszystkie” w podglądach fragmentów nie otwiera nowej strony. Na stronie maszynopisu rozwija listę w miejscu, w kolejności stron. Na stronie utworu otwiera stronę głównego maszynopisu z rozwiniętą listą.
- Liczby mają poprawne polskie formy: 1 fragment, 2–4 fragmenty, 5+ fragmentów.

**R-10 Karta fragmentu.** Każdy fragment wyświetlamy jako taką kartę:

1. linia lokalizacji: utwór, numer w dokumencie („fragment 01”), opcjonalna lokalizacja („rozdział I”); etykieta z typem źródła („Maszynopis”, „Zapisek”);
2. cytat (tekst fragmentu skrócony do kilku linii); dla źródła OCR miniatura strony skanu, na której fragment się zaczyna;
3. sygnatura, opis, tagi.

Kliknięcie karty otwiera dokument źródłowy przewinięty do fragmentu.

**R-11 Czytnik.** Każdy dokument OCR (maszynopis, zapisek, tekst sekundarny, materiał kontekstowy) czytamy w jednym czytniku:

1. Na komputerze każda strona skanu stoi obok tekstu OCR tej samej strony, a cały dokument przewija się w sposób ciągły. Na telefonie przełącznik „Skan” / „Transkrypcja”.
2. Fragmenty są wyróżnione w tekście. Kliknięcie fragmentu pokazuje jego tagi; każdy tag linkuje do strony tagu.
3. Otwarty z odnośnikiem do fragmentu, czytnik przewija do niego i go wyróżnia. Otwarty z wyniku wyszukiwania, przewija do pierwszego trafienia.

Dokument z tekstem litym wyświetlamy jako tekst, z fragmentami wyróżnionymi jak w punkcie 2.

**R-12 Dostępność.** WCAG 2.1 AA. Każdy obraz ma tekst alternatywny wpisany przez WR. Animacje respektują `prefers-reduced-motion`. Każdą kontrolkę da się obsłużyć z klawiatury i każda ma dostępną nazwę (np. ikona zamykania panelu filtrów to „Zamknij filtry”).

---

## 2. Archiwista (RA)

### US-RA-01 — Strona główna

1. Kolejno: nagłówek, hiro, utwory, wyróżniony fragment (US-RA-02), chmura tagów, stopka (R-07).
2. Hiro: tytuł „Archivum Buczkovianum” i wstępniak na portrecie Buczkowskiego, oraz liczby opublikowanych utworów, widocznych fragmentów i opublikowanych tagów („4 utwory · 62 fragmenty · 12 tagów”).
3. Utwory: jedna karta na każdy opublikowany utwór, w kolejności pierwszych wydań: okładka, gatunek i rok, tytuł, autor, liczba fragmentów. Liczba fragmentów to liczba widocznych fragmentów głównego maszynopisu utworu; gdy wynosi 0 (brak głównego maszynopisu, maszynopis w wersji roboczej albo brak widocznych fragmentów), karta jej nie pokazuje (R-02). Kliknięcie otwiera stronę utworu.
4. Chmura tagów: każdy opublikowany tag z co najmniej jednym wystąpieniem. Pięć rozmiarów według liczby wystąpień: 1–3, 4–7, 8–15, 16–25, 26+; dwa największe w kolorze akcentu. Układ jest deterministyczny: te same dane zawsze dają tę samą chmurę. Kliknięcie tagu otwiera jego stronę.
5. Wstępniak i portret są edytowalne (US-WR-11).

### US-RA-02 — Wyróżniony fragment na stronie głównej (Opcjonalne)

1. Jedna karta fragmentu (R-10), losowana spośród widocznych fragmentów oznaczonych jako wyróżnione (US-WR-09 AC6). Licznik: „1 z <liczba wszystkich widocznych fragmentów>”.
2. Pod kartą link „Wszystkie fragmenty „<utwór>” (n)” otwiera wyszukiwarkę na zakładce Fragmenty z filtrem na utwór tego fragmentu (US-RA-16).

### US-RA-03 — Stopka

1. Stopka jest zgodna z R-07.

### US-RA-04 — Strona utworu

Jako RA widzę korpus informacji o utworze; na pierwszy rzut oka tylko kluczowe informacje.

1. Hiro: „Utwór · Leopold Buczkowski · <rok pierwszego wydania>”, tytuł, opis.
2. Kolumna kontekstu: lista wydań według roku, każde z rokiem, wydawnictwem i miejscem. Najwcześniejsze ma etykietę „pierwsze wydanie”.
3. Kolumna główna, kolejno:
   1. „Fragmenty maszynopisu”: podgląd (R-09) fragmentów głównego maszynopisu jako karty fragmentów (R-10);
   2. „Maszynopisy”: numerowana lista maszynopisów utworu, każdy linkuje do swojej strony;
   3. „Zapiski”: zapiski powiązane z utworem, jako karty zapisków: linia lokalizacji, etykieta typu, obraz (lub zaślepka), sygnatura, opis, tagi.
4. Kolumna tagów: każdy opublikowany tag, który odnosi się do utworu (definicja w US-RA-07 AC5), w tym tagi relacji (US-RA-05).
5. Materiały kontekstowe (R-08): teksty sekundarne i materiały kontekstowe powiązane z utworem.

### US-RA-05 — Tagi relacji na stronie utworu

1. Tagi na powiązaniu z utworem (utwór ↔ tekst sekundarny lub utwór ↔ materiał kontekstowy) pojawiają się w kolumnie tagów utworu.
2. Każdy linkuje do strony tagu.

### US-RA-06 — Przejście w głąb ze strony utworu

1. Każdy element w kolumnie głównej, kolumnie tagów i bloku materiałów kontekstowych strony utworu linkuje do własnej podstrony, a fragment do swojego miejsca w źródle (R-01).

### US-RA-07 — Strona tagu

Jako RA widzę wszystko, co jest powiązane z tagiem.

1. Hiro: „Tag · <n> wystąpień w <m> utworach” (z poprawnymi formami liczby mnogiej), tytuł, opis (biografia albo krótkie opracowanie). Rodzaju tagu nie pokazujemy.
2. Kolumna kontekstu: „Utwory”, każdy utwór, do którego tag się odnosi, w kolejności pierwszych wydań. Każdy z rokiem, tytułem i liczbą swoich fragmentów z tym tagiem.
3. Kolumna główna, kolejno:
   1. „Fragmenty z tagiem”: każdy widoczny fragment z tagiem, jako karty fragmentów (R-10), w kolejności pierwszego wydania utworu, potem pozycji w tekście;
   2. „Zapiski z tagiem”: każdy zapisek z tagiem, otagowany całością lub fragmentem, jako karty zapisków (US-RA-04 AC3).
4. Kolumna tagów: „Powiązane tagi”, czyli tagi powiązane (symetrycznie, bez typu relacji).
5. Tag odnosi się do utworu, jeśli jest na utworze, na bycie powiązanym z utworem, na fragmencie takiego bytu albo na jednym z powiązań tego utworu.
6. Materiały kontekstowe (R-08): teksty sekundarne i materiały kontekstowe z tagiem, otagowane całością, fragmentem lub na powiązaniu z utworem.

### US-RA-08 — Strona maszynopisu

1. Hiro: „Maszynopis · <sygnatura> · <rok utworu>”, tytuł, opcjonalny opis.
2. Kolumna kontekstu: utwór (R-03) z rokiem i liczbą fragmentów; „Maszynopisy utworu”, wszystkie maszynopisy tego samego utworu z sygnaturą i tytułem, z zaznaczonym bieżącym.
3. Kolumna główna, kolejno:
   1. „Skan maszynopisu”: czytnik (R-11); licznik pokazuje liczbę stron;
   2. „Fragmenty z maszynopisu”: podgląd (R-09) jego fragmentów jako numerowana lista (numer fragmentu, lokalizacja, sygnatura), w kolejności stron.
4. Kolumna tagów: tagi na maszynopisie i na jego fragmentach.
5. Materiały kontekstowe (R-08): te powiązane z jego utworem.

### US-RA-09 — Czytanie całego maszynopisu

1. Cały maszynopis czytamy w czytniku (R-11). Wyróżnione fragmenty ma tylko główny maszynopis.

### US-RA-10 — Strona tekstu sekundarnego

1. Hiro: linia typu z rodzajem tekstu, a dla listu z nadawcą i datą („List · Leopold Buczkowski · 1.10.1947”); tytuł; opis. Bez grafiki w nagłówku.
2. Kolumna kontekstu: „Powiązane utwory” (R-03).
3. Kolumna główna, kolejno:
   1. „Transkrypcja”: pełny tekst w czytniku (R-11) albo jako tekst lity;
   2. „Powiązane fragmenty”: podgląd (R-09) fragmentów maszynopisu, które mają co najmniej jeden wspólny tag z tym tekstem lub jego fragmentami, jako karty fragmentów (R-10). Bez linku „wszystkie”.
4. Kolumna tagów: „Powiązane tagi”, czyli tagi na tekście, jego fragmentach i jego powiązaniach z utworami.

### US-RA-11 — Strona zapisku

Nie ma jej w Figmie; używa układu strony tekstu sekundarnego.

1. Hiro: „Zapisek · <sygnatura>”, tytuł, opcjonalny opis.
2. Kolumna kontekstu: powiązane utwory (R-03).
3. Kolumna główna, kolejno:
   1. treść, zależnie od typu:
      - obrazek: wyświetlony na stronie;
      - dokument: wyświetlony na stronie, jeśli to PDF, w przeciwnym razie do pobrania;
      - zewnętrzny link audio/wideo: osadzony odtwarzacz, jeśli dostawca na to pozwala, w przeciwnym razie link;
      - tekst OCR lub tekst lity: czytnik (R-11);
   2. „Powiązane fragmenty”, jak w US-RA-10 AC3.
4. Kolumna tagów: tagi na zapisku i jego fragmentach.

### US-RA-12 — Strona materiału kontekstowego

Nie ma jej w Figmie; używa układu strony tekstu sekundarnego.

1. Hiro: linia typu z rodzajem materiału i sygnaturą, tytuł, opcjonalny opis.
2. Kolumna kontekstu: powiązane utwory (R-03).
3. Kolumna główna: treść jak w US-RA-11 AC3, potem „Powiązane fragmenty” jak w US-RA-10 AC3.
4. Kolumna tagów: tagi na materiale, jego fragmentach i jego powiązaniach z utworami.

### US-RA-18 — Lista utworów

1. Otwierana z pozycji „Utwory” w menu głównym (R-07).
2. Siatka kart utworów (US-RA-01 AC3) dla każdego opublikowanego utworu, w kolejności pierwszych wydań, z liczbą w nagłówku.

### US-RA-19 — Lista maszynopisów

1. Otwierana z pozycji „Maszynopisy” w menu głównym (R-07).
2. Każdy opublikowany maszynopis, pogrupowany według utworu (utwory w kolejności pierwszych wydań), na komputerze dwie karty w rzędzie. Nagłówek grupy: tytuł utworu, gatunek, rok, liczba. Karta: numer, tytuł, sygnatura; otwiera stronę maszynopisu.

### US-RA-20 — Lista tagów

1. Otwierana z pozycji „Tagi” w menu głównym (R-07).
2. Chmura tagów (US-RA-01 AC4), potem „Wszystkie tagi”: każdy opublikowany tag z co najmniej jednym wystąpieniem, te same tagi co w chmurze, alfabetycznie, z liczbą wystąpień („4 wystąpienia”).

Na telefonie wszystkie trzy listy mają jedną kolumnę z tych samych komponentów.

### US-RA-13 — Strona „O archiwum”

1. Otwierana z linku „O archiwum” w nagłówku (R-07).
2. Hiro: tytuł „O archiwum” i wstęp.
3. „O projekcie”: tekst z bogatym formatowaniem o celu, zakresie, instytucjach partnerskich i finansowaniu.
4. „Zespół”: członkowie zespołu w trzech grupach, w tej kolejności: „Kierownictwo projektu”, „Członkowie zespołu”, „Opracowanie serwisu”. Każda osoba ma imię i nazwisko, funkcję i krótką biografię. Puste grupy się nie wyświetlają (R-02).

### US-RA-14 — Wejście do wyszukiwarki

1. Pasek wyszukiwania jest w nagłówku każdej strony (R-07). Wysłanie zapytania otwiera stronę wyszukiwarki z listą wyników.
2. Pod paskiem na stronie wyszukiwarki: co jest przeszukiwane („Przeszukiwane: tytuły, opisy, transkrypcje i tagi”) i wskazówka, że frazę w cudzysłowie wyszukujemy dokładnie.

### US-RA-15 — Wyniki wyszukiwania

Jako RA znajduję utwory, tagi, fragmenty i zapiski, wpisując frazę.

1. Wszystko jest indeksowane: wszystkie opublikowane byty i widoczne fragmenty — tytuły, opisy, nazwy i opisy tagów, cytaty i opisy fragmentów, teksty OCR i teksty lite.
2. Nagłówek pokazuje zapytanie i łączną liczbę wyników („7 wyników we wszystkich kategoriach”).
3. Zakładka „Wszystko” grupuje wyniki według typu, każda grupa z licznikiem, w tej kolejności: Utwory, Tagi, Fragmenty, Zapiski, Maszynopisy, Teksty sekundarne, Materiały kontekstowe.
4. W grupie wyniki są sortowane według trafności (więcej wzmianek = wyżej) albo, jeśli czytelnik wybierze, według tytułu.
5. Każdy wynik pokazuje swój typ (R-04) i jest klikalny. Wynik-fragment to karta fragmentu (R-10). Wynik-utwór pokazuje autora, gatunek, rok i liczbę pasujących fragmentów.
6. Trafienie wewnątrz tekstu pokazuje urywek z wyróżnionymi wyszukiwanymi słowami; kliknięcie otwiera obiekt przewinięty do trafienia. Wyniki-utwory nie mają urywka.
7. Wyszukiwarka radzi sobie z polską odmianą: „potoku” znajduje „potok”.
8. Gdy nie ma wyników, strona to mówi, podpowiada sprawdzenie pisowni lub skrócenie frazy i pokazuje „Śladami motywów”: trzy tagi z największą liczbą wystąpień.

### US-RA-16 — Zakładki i filtry wyszukiwarki

1. Zakładki, każda z liczbą wyników: Wszystko (domyślna), Utwory, Fragmenty, Zapiski, Tagi.
2. Filtry, każda wartość z liczbą wyników:
   - Utwór: wyniki powiązane z wybranymi utworami;
   - Okres: wyniki powiązane z utworami, których pierwsze wydanie przypada na wybraną dekadę (domyślnie „Wszystkie lata”);
   - Dostępność: „Ze skanem”, „Z transkrypcją”.
3. Na telefonie przycisk „Filtry (n)” otwiera filtry w panelu pełnoekranowym z paskiem akcji przypiętym na dole. „Pokaż wyniki (n)” zamyka panel i zawsze pokazuje liczbę wyników po filtrowaniu. „Wyczyść” czyści wszystkie filtry i nie zamyka panelu.
4. Zakładka, filtry i sortowanie są zapisane w adresie URL, więc wynikami można się podzielić linkiem.
5. Puste zapytanie zwraca wszystko z wybranej zakładki i filtrów, posortowane według tytułu.

### US-RA-17 — Autouzupełnianie (Opcjonalne)

1. Podczas wpisywania (np. „czarny p…”) pasek podpowiada pasujące tytuły utworów i nazwy tagów.
2. Wybranie podpowiedzi otwiera stronę tego bytu.

---

## 3. Redaktorka (WR)

Wszystko dzieje się w panelu administracyjnym (Django admin). Każde pole z obrazem wymaga tekstu alternatywnego (R-12). Każde pole „sygnatura” to instytucja wybrana z listy (US-WR-14) plus numer.

### US-WR-01 — Logowanie

1. Konta zakłada administrator. Nie ma publicznej rejestracji.
2. Wszystkie redaktorki mają te same uprawnienia.

### US-WR-02 — Szkic i publikacja

1. Każdy byt ma status: `draft` (szkic, domyślnie) albo `published` (opublikowany).
2. Publiczne są tylko opublikowane byty (R-06).

### US-WR-03 — Dodawanie utworu

1. Pola: tytuł (wymagany); gatunek (np. „powieść”); opis (tekst z bogatym formatowaniem); okładka/grafika do kart utworów.
2. Wydania dodajemy w tym samym formularzu: wydawnictwo, miejsce, rok, opcjonalna okładka.

### US-WR-04 — Dodawanie maszynopisu

1. Pola: utwór (wymagany, musi już istnieć); tytuł (wymagany, np. „Pierwsza wersja”); opcjonalny opis; sygnatura; plik źródłowy ze skanem (wymagany); plik OCR (wymagany).
2. Plik OCR musi mieć tyle stron co skan. W przeciwnym razie zapis jest odrzucany z komunikatem podającym obie liczby stron.
3. Pole wyboru „główny maszynopis”. Tylko jeden na utwór: zaznaczenie nowego odznacza poprzedni.
4. Zapis aktualizuje indeks wyszukiwarki.

### US-WR-05 — Dodawanie zapisku

1. Pola: tytuł (wymagany, np. „Notes 18 · karta 4”); opcjonalny opis; sygnatura; treść.
2. Treść to jedno z: obrazek; dokument; zewnętrzny link audio/wideo; tekst OCR (skan + plik OCR, sprawdzany jak w US-WR-04 AC2); tekst lity (np. transkrypcja listu).
3. Może być w relacji z jednym lub wieloma utworami.

### US-WR-06 — Dodawanie tekstu sekundarnego

1. Pola: tytuł (wymagany); rodzaj (np. list, recenzja, opracowanie, nagranie); sygnatura; tekst w wersji OCR (skan + plik OCR) albo tekst lity. Opcjonalnie: opis; autor; źródło (wydawnictwo, miejsce, rok, strony, jako jedna linia tekstu); data, nadawca i adresat (dla listów).
2. Może być w relacji z jednym lub wieloma utworami. Każde powiązanie z utworem można otagować (US-WR-10).

### US-WR-07 — Dodawanie materiału kontekstowego

1. Pola: tytuł (wymagany); opcjonalny opis; sygnatura; treść.
2. Treść to jedno z: obrazek; dokument; zewnętrzny link audio/wideo; tekst OCR; tekst lity.
3. Może być w relacji z jednym lub wieloma utworami. Każde powiązanie z utworem można otagować (US-WR-10).

### US-WR-08 — Zarządzanie tagami

1. Pola: nazwa (wymagana, unikalna); rodzaj: „słowo klucz z Buczkowskiego” albo „interpretacja” (wymagany; służy do filtrowania listy w panelu, nigdy nie jest pokazywany publicznie); opis (tekst z bogatym formatowaniem: biografia albo krótkie opracowanie).
2. Relacje między tagami są symetryczne: gdy B jest powiązany z A, to A jest powiązany z B.
3. Tagu, który jest gdzieś użyty, nie można usunąć. Komunikat błędu wymienia, gdzie jest użyty.

### US-WR-09 — Tagowanie fragmentów

1. Dostępne dla głównego maszynopisu oraz dla zapisków, tekstów sekundarnych i materiałów kontekstowych z tekstem OCR lub litym.
2. Na ekranie tagowania redaktorka zaznacza zakres tekstu i przypisuje mu jeden lub więcej istniejących tagów.
3. Fragmenty mogą na siebie zachodzić, a ten sam tekst może mieć kilka tagów.
4. Fragment przechowuje zaznaczony tekst. Jeśli tekst źródłowy się zmieni i fragment przestanie pasować, fragment jest oznaczany do sprawdzenia, a nigdy po cichu przesuwany ani usuwany.
5. Redaktorka nigdy nie wpisuje znaczników ręcznie (TEI ani żadnych innych).
6. Własny formularz fragmentu ma: lokalizację (np. „rozdział I”), numer sygnatury (np. „1618.0009”; instytucja pochodzi z dokumentu), opis i pole wyboru „wyróżniony”. Wyróżnione fragmenty są pierwsze w podglądach (R-09) i mogą trafić na stronę główną (US-RA-02).

### US-WR-10 — Tagowanie całych bytów i powiązań z utworem

1. Każdy utwór, maszynopis, zapisek, tekst sekundarny i materiał kontekstowy można otagować całością.
2. Powiązanie z utworem można otagować. Jego tagi pojawiają się na stronie utworu (US-RA-05).

### US-WR-11 — Edycja treści strony głównej

1. Do edycji: wstępniak i portret.

### US-WR-12 — Edycja strony „O archiwum”

1. Do edycji: wstęp i tekst o projekcie (tekst z bogatym formatowaniem).
2. Członków zespołu można dodawać, edytować i zmieniać ich kolejność. Każda osoba ma imię i nazwisko (wymagane), funkcję, krótką biografię i grupę: „Kierownictwo projektu”, „Członkowie zespołu” albo „Opracowanie serwisu”.

### US-WR-13 — Podgląd szkicu

1. Formularz każdego bytu w panelu ma link „Pokaż na stronie” (w angielskim panelu „View on site”), także dla szkiców.
2. Zalogowana redaktorka widzi stronę szkicu z banerem „Szkic — niewidoczny publicznie” (R-06). Anonimowi czytelnicy dostają 404.

### US-WR-14 — Zarządzanie instytucjami

1. Instytucja ma skrót (wymagany, unikalny, np. „ML”) i pełną nazwę (np. „Muzeum Literatury”).
2. Sygnatury zawsze wyświetlamy jako „<skrót>, sygn. <numer>”, składane z dwóch pól, nigdy wpisywane jako jeden tekst.

---

## 4. Utrzymanie (OPS)

Uruchomienie serwisu. Te story nie mają własnej publicznej strony.

### US-OPS-01 — Środowisko testowe

1. Aplikacja działa na Render jako usługa web z obrazu Dockera budowanego z `deploy/Dockerfile`; gunicorn nasłuchuje na porcie, który Render podaje w `$PORT`. Usługi i baza danych są opisane w `render.yaml`, czyli Blueprincie Render.
2. PostgreSQL 18 to baza Render Postgres. Aplikacja łączy się z nią przez `DATABASE_URL` w prywatnej sieci Render; baza nie przyjmuje połączeń z zewnątrz. Wyszukiwanie działa z `SEARCH_TS_CONFIG=simple`, bez polskiej odmiany (architecture, sekcja 6).
3. Cały serwis, łącznie z `/admin` i `/api`, jest za HTTP basic auth wymuszanym przez middleware Django, aktywnym, gdy ustawione są `BASIC_AUTH_USER` i `BASIC_AUTH_PASSWORD`. Bez danych logowania lub z błędnymi odpowiedź to 401 z nagłówkiem `WWW-Authenticate`.
4. Przy `ROBOTS_NOINDEX=true` każda odpowiedź ma nagłówek `X-Robots-Tag: noindex, nofollow`.
5. Media są w prywatnym buckecie S3 i serwowane przez presigned URL.
6. `GET /healthz` zwraca 200, gdy baza danych jest osiągalna, w przeciwnym razie 503, niezależnie od nagłówka `Host`, i jest jedyną ścieżką wyłączoną z basic auth.
7. Push do `main` wdraża nową wersję. Migracje uruchamia pre-deploy command Render; jeśli się nie powiodą, dalej działa poprzednia wersja.
8. Cała konfiguracja pochodzi z `render.yaml` i zmiennych środowiskowych Render. Sekretów nie ma w repozytorium: Render prosi o nie przy pierwszej synchronizacji Blueprintu. `deploy/.env.example` opisuje każdą zmienną.

---

## 5. Poza zakresem v1

Na później:

- **Wersja ukraińska.** Osobny serwis, podobny strukturalnie, uproszczony. Oznaczenie „Polski / Українська” w menu i stopce zawsze przekierowuje na jego stronę główną, niezależnie od tego, z której pozycji przechodzimy. Relacje między wersjami językowymi utworu (np. „Czarny potok” pl ↔ ukr) są w serwisie ukraińskim.
- **Epicykloida.** Powolna animowana grafika w tle strony głównej (brief 5.1). Nie ma jej w Figmie.
- **Bibliografia utworu** jako osobne pole tekstowe. W v1 bibliografią jest lista tekstów sekundarnych (R-08).
- **Grafika w nagłówku** strony utworu i strony tagu.
- **Kolejne strony z tekstem** (np. strona o konferencji).
- **SEO** (pozycjonowanie w Google). v1 ma tylko tytuł i opis w meta tagach dla każdego adresu.
- **Eksport do TEI.**

Odrzucone:

- Osobna podstrona dla jakiegokolwiek fragmentu, w tym fragmentu listu (R-01).
- „Komponent relacja” powtarzany na każdej stronie. Zastąpiony wspólnym układem strony bytu (R-05).
- Ręcznie wybierany wyróżniony zapisek dla utworu i wyróżniony fragment dla powiązania zapisku lub tekstu sekundarnego. Zastąpione podglądami z wyróżnionymi fragmentami na początku (R-09).

---

## 6. Otwarte pytania

Właściciel projektu rozstrzygnął pytania 1, 2, 3 i 5 dnia 27.10.2026 (`docs/plan.md`, D31). Otwarte pozostaje tylko pytanie 4.

1. **Metryczka tagu.** Czy ma pola poza nazwą, rodzajem i opisem? *Ustalone: nie.*
2. **Kolejność list.** *Ustalone: utwory według pierwszego wydania; wydania według roku; maszynopisy według utworu, potem sygnatury; tagi alfabetycznie; fragmenty według pozycji w tekście; wszystko inne według tytułu.*
3. **Wideo i audio.** Według briefu w zapiskach są hostowane gdzie indziej. *Ustalone: tak samo w materiałach kontekstowych, więc wgrywamy tylko obrazy i dokumenty.*
4. **Przykład otagowanej relacji.** Otwarte: redakcja musi go jeszcze znaleźć.
5. **Poprawki w projekcie.** Figma wciąż pokazuje przeglądarkę maszynopisu z samym skanem i karty fragmentów z wyciętym skanem. *Ustalone: wygrywają story, a Figma nie będzie poprawiana. Czytnik ze skanem obok tekstu i przełącznikiem na telefonie (R-11) oraz kartę fragmentu z cytatem i miniaturą strony (R-10) budujemy według story z istniejących komponentów Figmy.*
