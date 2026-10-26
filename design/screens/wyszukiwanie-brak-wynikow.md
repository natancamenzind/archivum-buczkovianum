# Wyszukiwanie — brak wyników

Viewport: desktop, 1440px wide. Preview: `../previews/screens/wyszukiwanie-brak-wynikow.png`

- box "Wyszukiwanie — brak wyników" · flex-column · gap 0px · 1440px × 671px · bg var(--color-bg-page)
  - **Nagłówek serwisu [Rozmiar=Desktop]** {Rozmiar=“Desktop”} · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w fill, h 88px · bg var(--color-bg-page) · border-bottom 1px var(--color-border-subtle)
  - box "Wyszukiwanie" · flex-column · gap var(--space-12) · padding var(--space-48) var(--layout-page-margin) 0px var(--layout-page-margin) · w fill, h hug
    - **Pole wyszukiwania [Stan=Wypełnione]** {Wartość=“dezerterka”, Stan=“Wypełnione”} · flex-row · gap var(--space-12) · padding 0px var(--space-8) 0px var(--space-16) · align center · w 880px, h 56px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
    - text "Zakres" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Przeszukiwane: tytuły, opisy, transkrypcje i tagi”
  - box "Treść" · flex-column · gap 0px · padding var(--space-32) var(--layout-page-margin) var(--space-64) var(--layout-page-margin) · w fill, h hug
    - box "Brak wyników" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · w 880px, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
      - text "Tytuł" · w fill, h hug · .text-lora-tytul-sekcji · color var(--color-text-primary) · “Brak wyników dla „dezerterka””
      - text "Podpowiedź" · w fill, h hug · .text-lora-tekst · color var(--color-text-secondary) · “Sprawdź pisownię albo skróć frazę. Wyszukiwanie obejmuje tytuły, opisy, transkrypcje i tagi.”
      - box "Śladami motywów" · flex-column · gap var(--space-8) · w fill, h hug
        - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Śladami motywów”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
        - text "Opis" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “Tagi łączą fragmenty z różnych utworów. Otwórz tag, by podążyć za motywem w całym archiwum.”
        - box "Tagi" · flex-row wrap · gap var(--space-8) · w fill, h hug
          - **Tag [Stan=Domyślny]** {Nazwa=“Dezerter”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
          - **Tag [Stan=Domyślny]** {Nazwa=“Wojna”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
          - **Tag [Stan=Domyślny]** {Nazwa=“Wieś”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
          - **Tag [Stan=Domyślny]** {Nazwa=“Pamięć”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
          - **Tag [Stan=Domyślny]** {Nazwa=“Podole”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
          - **Tag [Stan=Domyślny]** {Nazwa=“Ucieczka”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
  - **Stopka [Rozmiar=Desktop]** {Rozmiar=“Desktop”} · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w fill, h 88px · bg var(--color-bg-page) · border-top 1px var(--color-border-subtle)
