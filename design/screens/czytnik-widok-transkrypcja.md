# Czytnik — widok Transkrypcja

Viewport: desktop, 1312px wide. Preview: `../previews/screens/czytnik-widok-transkrypcja.png`

- box "Czytnik — widok Transkrypcja" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · 1312px × 980px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
  - **Nagłówek sekcji** {Pokaż licznik=true, Pokaż opis=false, Opis=“Wybór redakcji, w kolejności tekstu”, Licznik=“137 stron”, Tytuł=“Skan maszynopisu”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - box "Pasek czytnika (przyklejony)" · flex-row · padding var(--space-8) var(--space-16) var(--space-8) var(--space-16) · justify space-between · align center · w fill, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Pole strony [Stan=Domyślne]** {Stan=“Domyślne”} · flex-column · gap var(--space-4) · w hug, h hug
    - **Widok czytnika [Widok=Transkrypcja]** {Widok=“Transkrypcja”} · flex-row · gap var(--space-4) · padding var(--space-4) · align center · w hug, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Szukaj w maszynopisie [Stan=Puste]** {Stan=“Puste”} · flex-row · gap var(--space-8) · padding 0px var(--space-4) 0px var(--space-12) · align center · w 400px, h 40px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
  - box "Strony (przewijane, doczytywane po jednej)" · flex-column · gap var(--space-32) · w fill, h hug
    - box "Strona 9" · flex-row · gap var(--space-24) · justify center · w fill, h hug
      - box "Transkrypcja" · flex-column · gap var(--space-12) · w 720px, h hug
        - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Transkrypcja · strona 9 z 137”
        - text "Tekst strony" · w fill, h hug · mixed styles · “I.⏎⏎Po kilku dniach, podobnych do wiosny, przyszła zawieja i nawaliła tyle śniegu, że Dolinoszczęsna jakby się zapadła w rozdół biały i nieogarnięty. Ze śniegu wystawały wysokie jesiony z wronimi miotłami, na tle śnieżnej osypki, ostro, wyraźnie rysowały się długie stodoły, chaty z rudymi zakisami na dymnikach i zalane pomyjami podwórza.⏎⏎W mroźne poranki sypały się na śmietniska głodne wróble, sikory i czyżyki, a zwinna kraska, przeszukująca grzebienice, zwisała martwa na zastawionym włosieniu.⏎⏎Płynęły przeplatane śniegiem i słomą, twarde zimowe dni. W Dolinoszczęsnej wybuchła epidemia tyfusu i grypy. Chore dzieci, dusząc się na piecach, grzały gorączką młode jagnięta i psiaki. Kobiety biegały za pożyczaniem trzasek malinowych na poty.⏎⏎Grzybniak leczył, dniami i nocami biegał po Zasereciu i Dolinoszczęsnej; przedrzemawszy w domu kilka chwil koło ciepłego pieca, pił śniadanie, zmieniał przemokłe onucki i znowu szedł do chorych.⏎⏎Carkówna, wdziawszy trykotowe spodnie i buty z cholewami, stanęła we wrotach przed szkołą; przeżegnawszy się, dusząc w sobie strach, powiedziała do dzieci:”
      - box "Margines (tagi fragmentów)" · free layout (children positioned) · w 200px, h fill
        - **Tagi fragmentu (margines) [Stan=Podświetlony]** {Stan=“Podświetlony”} · flex-row wrap · gap var(--space-8) · padding 0px 0px 0px var(--space-12) · w 200px, h hug · at (0, 302) · border-left 2px var(--color-border-accent)
        - **Tagi fragmentu (margines) [Stan=Domyślny]** {Stan=“Domyślny”} · flex-row wrap · gap var(--space-8) · padding 0px 0px 0px var(--space-12) · w 200px, h hug · at (0, 492) · border-left 1px var(--color-border-subtle)
    - box "Strona 10" · flex-row · gap var(--space-24) · justify center · w fill, h 160px · overflow hidden
      - box "Transkrypcja" · flex-column · gap var(--space-12) · w 720px, h hug
        - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Transkrypcja · strona 10 z 137”
        - text "Tekst strony" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Ciąg dalszy tekstu: strona 10. Fragment 02 zaczyna się na stronie 9, więc jego tagi są na marginesie strony 9.]”
      - box "Margines (tagi fragmentów)" · w 200px, h fill
