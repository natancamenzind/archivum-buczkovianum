# Czytnik — widok Skan

Viewport: desktop, 1312px wide. Preview: `../previews/screens/czytnik-widok-skan.png`

- box "Czytnik — widok Skan" · flex-column · gap var(--space-24) · padding var(--layout-card-padding) · 1312px × 1517px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
  - **Nagłówek sekcji** {Pokaż licznik=true, Pokaż opis=false, Opis=“Wybór redakcji, w kolejności tekstu”, Licznik=“137 stron”, Tytuł=“Skan maszynopisu”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - box "Pasek czytnika (przyklejony)" · flex-row · padding var(--space-8) var(--space-16) var(--space-8) var(--space-16) · justify space-between · align center · w fill, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Pole strony [Stan=Domyślne]** {Stan=“Domyślne”} · flex-column · gap var(--space-4) · w hug, h hug
    - **Widok czytnika [Widok=Skan]** {Widok=“Skan”} · flex-row · gap var(--space-4) · padding var(--space-4) · align center · w hug, h hug · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-s)
    - **Szukaj w maszynopisie [Stan=Puste]** {Stan=“Puste”} · flex-row · gap var(--space-8) · padding 0px var(--space-4) 0px var(--space-12) · align center · w 400px, h 40px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
  - box "Strony (przewijane, doczytywane po jednej)" · flex-column · gap var(--space-32) · w fill, h hug
    - box "Strona 9" · flex-row · gap var(--space-24) · justify center · w fill, h hug
      - box "Skan" · flex-column · gap var(--space-12) · padding var(--space-16) · w 760px, h hug · bg var(--color-bg-media) · radius var(--radius-m)
        - box "Pasek" · flex-row · justify space-between · align center · w fill, h hug
          - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Skan · strona 9 z 137”
          - **Powiększ skan** · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
        - rect "Obraz strony" · w fill, h 1029px · bg image(assets/images/obraz-strony-7d71634a.*, fit) · shadow var(--shadow-dokument)
      - box "Margines (tagi fragmentów)" · free layout (children positioned) · w 200px, h fill
        - **Tagi fragmentu (margines) [Stan=Domyślny]** {Stan=“Domyślny”} · flex-row wrap · gap var(--space-8) · padding 0px 0px 0px var(--space-12) · w 200px, h hug · at (0, 44) · border-left 1px var(--color-border-subtle)
        - **Tagi fragmentu (margines) [Stan=Podświetlony]** {Stan=“Podświetlony”} · flex-row wrap · gap var(--space-8) · padding 0px 0px 0px var(--space-12) · w 200px, h hug · at (0, 84) · border-left 2px var(--color-border-accent)
    - box "Strona 10" · flex-row · gap var(--space-24) · justify center · w fill, h 160px · overflow hidden
      - box "Skan" · flex-column · gap var(--space-12) · padding var(--space-16) · w 760px, h hug · bg var(--color-bg-media) · radius var(--radius-m)
        - box "Pasek" · flex-row · justify space-between · align center · w fill, h hug
          - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Skan · strona 10 z 137”
          - **Powiększ skan** · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-s)
        - rect "Obraz strony" · w fill, h 1029px · bg image(assets/images/obraz-strony-7d71634a.*, fit) · shadow var(--shadow-dokument)
      - box "Margines (tagi fragmentów)" · w 200px, h fill
