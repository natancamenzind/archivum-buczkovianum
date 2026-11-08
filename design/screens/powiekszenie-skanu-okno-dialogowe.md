# Powiększenie skanu (okno dialogowe)

Viewport: desktop, 1440px wide. Preview: `../previews/screens/powiekszenie-skanu-okno-dialogowe.png`

- box "Powiększenie skanu (okno dialogowe)" · flex-column · gap 0px · 1440px × 900px · bg var(--color-bg-inverse) · overflow hidden
  - box "Pasek" · flex-row · padding var(--space-16) var(--space-24) var(--space-16) var(--space-24) · justify space-between · align center · w fill, h hug
    - text "Opis" · w 280px, h hug · .text-cousine-metadane · color var(--color-text-inverse-secondary) · “Skan · strona 9 z 137”
    - box "Powiększenie" · flex-row · gap var(--space-8) · align center · w hug, h hug
      - box "Pomniejsz" · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · radius var(--radius-s)
        - text "Etykieta" · .text-cousine-metadane · color var(--color-text-primary) · “−”
      - text "Skala" · .text-cousine-metadane · color var(--color-text-inverse) · “150%”
      - box "Powiększ" · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · radius var(--radius-s)
        - text "Etykieta" · .text-cousine-metadane · color var(--color-text-primary) · “+”
      - box "Dopasuj do okna" · flex-row · gap 0px · padding 0px var(--space-12) 0px var(--space-12) · justify center · align center · w hug, h 32px · bg var(--color-bg-card) · radius var(--radius-s)
        - text "Etykieta" · .text-cousine-metadane · color var(--color-text-primary) · “Dopasuj”
    - box "Zamknij" · flex-row · gap var(--space-8) · justify end · align center · w 280px, h hug
      - box "Zamknij powiększenie" · flex-row · gap 0px · justify center · align center · w 32px, h 32px · bg var(--color-bg-card) · radius var(--radius-s)
        - **Ikona/zamknij** · w 16px, h 16px
  - box "Skan" · flex-row · gap var(--space-16) · padding 0px var(--space-24) 0px var(--space-24) · align center · w fill, h fill
    - box "Poprzednia strona" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-card) · radius var(--radius-full)
      - **Ikona/wstecz** · w 16px, h 16px
    - box "Widok skanu (przeciąganie przesuwa)" · free layout (children positioned) · w fill, h fill · overflow hidden
      - rect "Obraz strony" · w 1100px, h 1555px · at (86, -360) · bg image(assets/images/obraz-strony-7d71634a.*, fit)
    - box "Następna strona" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-card) · radius var(--radius-full)
      - **Ikona/dalej** · w 16px, h 16px
  - box "Podpowiedź" · flex-row · gap 0px · padding var(--space-12) var(--space-24) var(--space-16) var(--space-24) · justify center · w fill, h hug
    - text "Transkrypcja" · .text-cousine-metadane-male · color var(--color-text-inverse-secondary) · “Przeciągnij, aby przesunąć · Ctrl + kółko albo gest powiększa · ← → zmienia stronę · Esc zamyka”
