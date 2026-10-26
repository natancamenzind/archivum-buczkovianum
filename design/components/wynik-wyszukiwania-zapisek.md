# Wynik wyszukiwania / Zapisek

Wspólna siatka wyników; typ obiektu decyduje o wariancie. W ekranach szerokość wypełnia kontener.

## Properties

- `Tytuł` (text) — default “Notes 18”
- `Opis` (text) — default “Zapisek · ML, sygn. 1678.0104”
- `Dopasowanie` (text) — default “Zapisek z tagiem”

## Structure

- box "Wynik wyszukiwania / Zapisek" · flex-row · gap var(--space-16) · padding var(--space-16) 0px var(--space-16) 0px · align center · 800px × 81px · border-bottom 1px var(--color-border-subtle)
  - box "Ikona typu" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-subtle) · radius var(--radius-s)
    - **Ikona/zapisek** · w 16px, h 16px
  - box "Opis" · flex-column · gap var(--space-4) · w fill, h hug
    - text "Tytuł" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “Notes 18”
    - text "Opis" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “Zapisek · ML, sygn. 1678.0104”
  - box "Dopasowanie" · flex-row · gap var(--space-8) · align center · w hug, h hug
    - text "Dopasowanie" · .text-cousine-metadane-male · color var(--color-text-accent) · “Zapisek z tagiem”
    - **Ikona/strzalka-ukos** · w 16px, h 16px

Preview: `../previews/components/wynik-wyszukiwania-zapisek.png`
