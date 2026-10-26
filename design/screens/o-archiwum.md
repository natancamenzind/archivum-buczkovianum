# O archiwum

Viewport: desktop, 1440px wide. Preview: `../previews/screens/o-archiwum.png`

- box "O archiwum" · flex-column · gap 0px · 1440px × 1513px · bg var(--color-bg-page)
  - **Nagłówek serwisu [Rozmiar=Desktop]** {Rozmiar=“Desktop”} · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w fill, h 88px · bg var(--color-bg-page) · border-bottom 1px var(--color-border-subtle)
  - **Nagłówek strony [Rozmiar=Desktop]** {Tytuł=“O archiwum”, Pokaż opis=false, Opis=“Pierwsza powieść Leopolda Buczkowskiego, wydana w 1947 roku. Sceny z codziennego życia podolskiej wsi w dwudziestoleciu międzywojennym.”, Etykieta=“Archivum Buczkovianum”, Rozmiar=“Desktop”} · flex-column · gap var(--space-16) · padding var(--space-48) var(--layout-page-margin) var(--space-48) var(--layout-page-margin) · w fill, h hug · bg var(--color-bg-inverse) · paper grain (noise, white @4%)
  - box "Treść" · flex-column · gap 0px · padding var(--space-48) var(--layout-page-margin) var(--space-64) var(--layout-page-margin) · align center · w fill, h hug
    - box "Kolumna tekstu" · flex-column · gap var(--space-32) · w 760px, h hug
      - box "O projekcie" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · w fill, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
        - **Nagłówek sekcji** {Pokaż licznik=false, Pokaż opis=false, Opis=“Wybór redakcji, w kolejności tekstu”, Licznik=“2 z 24”, Tytuł=“O projekcie”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
        - text "Opis" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Opis projektu: cel archiwum, zakres zbiorów, instytucje partnerskie i źródło finansowania. Dwa, trzy akapity.]”
      - box "Zespół" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · w fill, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
        - **Nagłówek sekcji** {Pokaż licznik=false, Pokaż opis=false, Opis=“Wybór redakcji, w kolejności tekstu”, Licznik=“2 z 24”, Tytuł=“Zespół”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
        - box "Kierownictwo projektu" · flex-column · gap var(--space-8) · w fill, h hug
          - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Kierownictwo projektu”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
          - **Osoba** {Biogram=“[Biogram: dwa, trzy zdania]”, Rola=“[Rola w projekcie]”, Imię i nazwisko=“[Imię i nazwisko]”} · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
        - box "Członkowie zespołu" · flex-column · gap var(--space-8) · w fill, h hug
          - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Członkowie zespołu”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
          - **Osoba** {Biogram=“[Biogram: dwa, trzy zdania]”, Rola=“[Rola w projekcie]”, Imię i nazwisko=“[Imię i nazwisko]”} · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
          - **Osoba** {Biogram=“[Biogram: dwa, trzy zdania]”, Rola=“[Rola w projekcie]”, Imię i nazwisko=“[Imię i nazwisko]”} · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
        - box "Opracowanie serwisu" · flex-column · gap var(--space-8) · w fill, h hug
          - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Opracowanie serwisu”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
          - **Osoba** {Biogram=“[Biogram: dwa, trzy zdania]”, Rola=“[Rola w projekcie]”, Imię i nazwisko=“[Imię i nazwisko]”} · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
          - **Osoba** {Biogram=“[Biogram: dwa, trzy zdania]”, Rola=“[Rola w projekcie]”, Imię i nazwisko=“[Imię i nazwisko]”} · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - **Stopka [Rozmiar=Desktop]** {Rozmiar=“Desktop”} · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w fill, h 88px · bg var(--color-bg-page) · border-top 1px var(--color-border-subtle)
