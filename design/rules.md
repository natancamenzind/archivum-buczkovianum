# Zasady i słownik

## Tryb

Makiety pokazują wyłącznie tryb czytelnika. Jedynym miejscem wprowadzania danych jest wyszukiwarka: pole, zakładki kategorii, filtry i sortowanie.

Nie ma list lektur, zakładek, przesyłania plików ani statusów redakcyjnych. Panel redakcyjny to osobny projekt.

## Słownik typów obiektów

Utwór — dzieło literackie, np. „Wertepy”. Wydanie — publikacja utworu: rok, wydawca, miejsce. Maszynopis — jednostka archiwalna z maszynopisem utworu. Fragment — oznaczony wycinek skanu maszynopisu z sygnaturą i tagami. Zapisek — rękopiśmienna notatka autora (notes, karta). Tekst sekundarny — materiał kontekstowy: list, recenzja, opracowanie, nagranie. Materiał wizualny — zdjęcie lub skan ilustracyjny. Tag — motyw łączący fragmenty i zapiski.

W interfejsie używamy wyłącznie tych nazw. Nie używamy: „książki”, „rękopisy”, „notatki”, „content page”.

## Sygnatura

Format: „ML, sygn. 1618.0009” dla jednostki, „ML, sygn. 1618” dla całego maszynopisu. ML — Muzeum Literatury.

W kodzie składana z pól instytucja i numer sygnatury, nigdy wpisywana ręcznie jako jeden tekst.

## Nawigacja główna

Pozycje: Strona główna, Utwory, Maszynopisy, Tagi. Aktywna pozycja wynika z typu strony: strona główna → Strona główna; utwór → Utwory; maszynopis → Maszynopisy; tag → Tagi. Wyszukiwanie, tekst sekundarny i O archiwum nie mają aktywnej pozycji.

Desktop: nawigacja w stopce, wyszukiwanie i „O archiwum” w nagłówku. Mobile: nawigacja w dolnym pasku, wyszukiwanie jako ikona w nagłówku.

## Liczniki i linki

Licznik w nagłówku sekcji to liczba elementów („3”) albo pokazane z wszystkich („2 z 24”). Link „więcej” zawsze nazywa cel i podaje liczbę: „Wszystkie fragmenty (24)”.

## Chmura tagów

Pięć stopni wielkości według liczby wystąpień: 1–3 → stopień 1 (15 px), 4–7 → 2 (18 px), 8–15 → 3 (22 px), 16–25 → 4 (28 px), 26 i więcej → 5 (36 px). Stopnie 4–5 w kolorze akcentu. Bez krawędzi i grafu.

Układ chmury: największe tagi w środkowym rzędzie, mniejsze wokół; każdy wyraz ma stałe przesunięcie w pionie (0–24 px), żeby linie bazowe się nie zrównywały. W kodzie: deterministyczne tasowanie (stałe ziarno), flex-wrap wyśrodkowany, translateY według indeksu.

## Siatka

Desktop 1440 px, margines 64 px, treść 1312 px. Podstrony: kolumna kontekstu 240 px, treść, kolumna tagów 240 px, odstęp 32 px.

Mobile 390 px, margines 16 px, jedna kolumna w kolejności: treść główna, kontekst, tagi, materiały kontekstowe.

## Materiały zastępcze

Szare plansze z ikoną i opisem oznaczają brakujący materiał: okładki, zdjęcia, skany zapisków, teksty sekundarne. Opisy w nawiasach kwadratowych pokazują wzór zapisu.

Skan fragmentu i strony to próbka druku „Wertepów”; docelowo skany maszynopisu. Okładka na kartach utworów: tymczasowo ta sama okładka „Wertepów” dla każdego utworu. Portret w nagłówku strony głównej: domena publiczna, Wikimedia Commons (skan z: Z. Trziszka, „Leopold Buczkowski”, PIW 1987), 1173 × 1789 px — przy pełnej szerokości 1440 px obraz jest powiększony, docelowo skan w wyższej rozdzielczości.

## Dane przykładowe (spójne na wszystkich ekranach)

Wertepy · powieść · 1947 · 24 fragmenty · maszynopisy ML, sygn. 1618 (pierwsza wersja) i 1619 (druga wersja) · wydania: 1947 Gebethner i Wolff, Warszawa; 1957 Państwowy Instytut Wydawniczy, Warszawa; 1973 Wydawnictwo Literackie, Kraków.

Czarny potok · 1954 · 18 fragmentów. Dorycki krużganek · 1957 · 12 fragmentów. Pierwsza świetność · 1966 · 8 fragmentów. Razem 62 fragmenty, 12 tagów.

Tag „Dezerter”: 4 wystąpienia (3 fragmenty, 1 zapisek) w 2 utworach. Wyszukiwanie „Dezerter”: 7 wyników — 2 utwory, 3 fragmenty, 1 zapisek, 1 tag.

Fragmenty: Wertepy ML, sygn. 1618.0009 (rozdz. I) i 1618.0019 (rozdz. III); Czarny potok ML, sygn. 1609.0012; zapisek Notes 18, ML, sygn. 1678.0104; List nr 32 z 1.10.1947, ML, sygn. 1701.0032.

Maszynopisy (5): Wertepy ML, sygn. 1618 i 1619; Czarny potok ML, sygn. 1609; Dorycki krużganek ML, sygn. 1625; Pierwsza świetność ML, sygn. 1640.

## Panel filtrów (mobile)

Otwierany przyciskiem „Filtry (n)” na liście wyników, zajmuje cały ekran i przykrywa nagłówek serwisu. Pasek akcji przypięty do dołu ekranu, treść przewija się nad nim. Te same grupy co na desktopie. Zamknięcie: ikona w nagłówku (aria-label „Zamknij filtry”) albo „Pokaż wyniki (n)” — przycisk zawsze podaje liczbę wyników po zastosowaniu filtrów. „Wyczyść” odznacza wszystko bez zamykania panelu.

## Strony list

Utwory: siatka kart w kolejności wydania. Maszynopisy: karty pogrupowane według utworu, po dwie w rzędzie. Tagi: chmura i pełny indeks alfabetyczny z liczbą wystąpień (poprawna odmiana: 1 wystąpienie, 2–4 wystąpienia, 5+ wystąpień). Wersje mobile list: jedna kolumna z tych samych komponentów, bez osobnych makiet.

## Typografia

Lora dla treści i tytułów, Cousine dla metadanych, etykiet i nawigacji. Krój maszynowy odsyła do maszynopisów, które są rdzeniem archiwum.

Duże tytuły mają zmniejszone światło między literami: Display −2%, Tytuł strony −1,5%, Tytuł strony mobile −1%, Tytuł sekcji −0,5%. Tytuł elementu (karty, sygnatury, logo) w Lora Medium.

Etykiety (Cousine/Etykieta): wersaliki, krój zwykły 11 px, rozstrzelenie 12%. Etykiet nie pogrubiamy.

Kursywa to głos redakcji: Lora/Wstęp (19 px) pod tytułem strony, Lora/Glosa (15 px) jako komentarz pod fragmentem. Tekst Buczkowskiego nie dostaje kursywy redakcyjnej.

## Kolor, głębia i ornamenty

Brąz w trzech odcieniach: 300 (linie na ciemnym tle, obwódka najechania), 600 (akcent podstawowy), 700 (najechanie na akcent). Tło akcentu subtelne (braz-50) wyłącznie dla stanów najechania i zaznaczenia.

Cienie w odcieniu atramentu, nie szarości. Cień/karta: każdy panel i karta na tle strony. Cień/dokument: skany i okładki. Cień/uniesiony: wyłącznie stan najechania. Innych cieni nie dodajemy.

Ornamenty: brązowa listwa 3 px u góry nagłówka serwisu; linia 40 × 1 px nad etykietą w ciemnych nagłówkach stron; ziarno papieru (szum 4%) tylko na ciemnych nagłówkach.

## Stany najechania

Karta utworu, Tag, Link ze strzałką i Przycisk mają warianty Stan = Domyślny / Najechany, połączone w prototypie płynnym przejściem (tryb prezentacji).

Karta: unosi się, tytuł przechodzi w akcent, obwódka braz-300. Tag: ciepłe tło i akcentowa obwódka. Link: podkreślenie 1 px z odstępem 3 px, strzałka odsuwa się o 4 px. Przycisk: ciemniejszy brąz (Główny) albo ciepłe tło (Drugorzędny).

W kodzie: przejście 150–180 ms z wygaszaniem, wyłączone przy prefers-reduced-motion. Ten sam stan pokazujemy przy :focus-visible, bo z klawiatury i na ekranach dotykowych najechania nie ma.

## Stany ładowania

Wyniki wczytują się w miejscu docelowym: panel z czterema szkieletami (Wynik wyszukiwania / Szkielet) o proporcjach prawdziwego wyniku, więc układ nie przeskakuje po wczytaniu. Ekran: „Wyszukiwanie — ładowanie”.

Podczas ładowania liczniki w zakładkach pokazują „–”, a filtry i sortowanie są wyszarzone (40%) i nieaktywne. Pod tytułem kursywą: „Przeszukuję utwory, fragmenty, zapiski i tagi…”.

Szkielet pulsuje łagodnie (700 ms w jedną stronę). Pokazujemy go dopiero po 300 ms, żeby szybkie odpowiedzi nie migały; przy prefers-reduced-motion szkielet stoi bez animacji.

## Otwarte kwestie

Skany maszynopisów, zapisków i okładek oraz portret autora — czekają na materiały.

Zmienne układu mają osobne wartości desktop i mobile, bo plan Starter pozwala na jeden tryb w kolekcji. Po przeniesieniu pliku na plan płatny: jedna kolekcja z trybami Desktop i Mobile.
