# Czytnik — przewijanie doczytuje następną stronę

Viewport: desktop, 1312px wide. Preview: `../previews/screens/czytnik-przewijanie-doczytuje-nastepna-strone.png`

- box "Czytnik — przewijanie doczytuje następną stronę" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · 1312px × 1275px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
  - **Nagłówek sekcji** {Pokaż licznik=true, Pokaż opis=false, Opis=“Wybór redakcji, w kolejności tekstu”, Licznik=“137 stron”, Tytuł=“Skan maszynopisu”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - box "Pasek czytnika (przyklejony)" · flex-row · padding var(--space-8) var(--space-16) var(--space-8) var(--space-16) · justify space-between · align center · w fill, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Pole strony [Stan=Domyślne]** {Stan=“Domyślne”} · flex-column · gap var(--space-4) · w hug, h hug
      - override "Wartość": text “10”
    - **Widok czytnika [Widok=Skan i transkrypcja]** {Widok=“Skan i transkrypcja”} · flex-row · gap var(--space-4) · padding var(--space-4) · align center · w hug, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Szukaj w maszynopisie [Stan=Puste]** {Stan=“Puste”} · flex-row · gap var(--space-8) · padding 0px var(--space-4) 0px var(--space-12) · align center · w 400px, h 40px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
  - box "Strony (przewijane, doczytywane po jednej)" · flex-column · gap var(--space-32) · w fill, h hug
    - box "Strona 10" · flex-row · gap var(--space-24) · w fill, h hug
      - box "Skan" · flex-column · gap var(--space-12) · padding var(--space-16) · w fill, h hug · bg var(--color-bg-media) · radius var(--radius-m)
        - box "Pasek" · flex-row · justify space-between · align center · w fill, h hug
          - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Skan · strona 10 z 137”
          - **Powiększ skan** · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
        - rect "Obraz strony" · w fill, h 639px · bg image(assets/images/obraz-strony-7d71634a.*, fit) · shadow var(--shadow-dokument)
      - box "Transkrypcja" · flex-column · gap var(--space-12) · w fill, h hug
        - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Transkrypcja · strona 10 z 137”
        - text "Tekst strony" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Ciąg dalszy tekstu: strona 10. Fragment 02 zaczyna się na stronie 9, więc jego tagi są na marginesie strony 9.]”
      - box "Margines (tagi fragmentów)" · w 200px, h fill
    - box "Strona 11 — wczytywanie" · flex-column · gap var(--space-12) · w fill, h hug · overflow hidden
      - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Wczytywanie strony 11 z 137…”
      - box "Szkielet" · flex-row · gap var(--space-24) · w fill, h hug
        - rect "Skan (szkielet)" · w fill, h 280px · bg var(--color-bg-subtle) · radius var(--radius-m)
        - box "Tekst (szkielet)" · flex-column · gap var(--space-12) · w fill, h hug
          - rect "Wiersz" · w fill, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 449px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 473px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 293px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w fill, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 415px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 459px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
          - rect "Wiersz" · w 195px, h 12px · bg var(--color-bg-subtle) · radius var(--radius-s)
        - rect "Margines (pusty)" · w 200px, h 1px · bg var(--color-bg-card)
