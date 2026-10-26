# Wynik wyszukiwania / Fragment

Wspólna siatka wyników; typ obiektu decyduje o wariancie. W ekranach szerokość wypełnia kontener.

## Properties

- `Ścieżka` (text) — default “Wertepy · maszynopis”
- `Tytuł` (text) — default “Wertepy — fragment 01”
- `Opis` (text) — default “Fragment oznaczony tagiem „Dezerter”. Skan i miejsce w tekście utworu.”
- `Sygnatura` (text) — default “ML, sygn. 1618.0009”

## Structure

- box "Wynik wyszukiwania / Fragment" · flex-column · gap var(--space-8) · padding var(--space-16) 0px var(--space-16) 0px · 800px × 151px · border-bottom 1px var(--color-border-subtle)
  - text "Ścieżka" · w fill, h hug · .text-cousine-etykieta · color var(--color-text-secondary) · “Wertepy · maszynopis”
  - box "Wiersz tytułu" · flex-row · justify space-between · align center · w fill, h hug
    - text "Tytuł" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “Wertepy — fragment 01”
    - **Ikona/strzalka-ukos** · w 16px, h 16px
  - text "Opis" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “Fragment oznaczony tagiem „Dezerter”. Skan i miejsce w tekście utworu.”
  - box "Stopka" · flex-row · justify space-between · align center · w fill, h hug
    - text "Sygnatura" · .text-cousine-metadane-male · color var(--color-text-secondary) · “ML, sygn. 1618.0009”
    - **Tag [Stan=Domyślny]** {Nazwa=“Dezerter”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)

Preview: `../previews/components/wynik-wyszukiwania-fragment.png`
