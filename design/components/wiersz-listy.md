# Wiersz listy

## Properties

- `Nr` (text) — default “01”
- `Tytuł` (text) — default “Maszynopis „Wertepów”, ML, sygn. 1618”

## Structure

- box "Wiersz listy" · flex-row · padding var(--space-12) 0px var(--space-12) 0px · justify space-between · align center · 560px × 48px · border-bottom 1px var(--color-border-subtle)
  - box "Treść" · flex-row · gap var(--space-12) · align center · w fill, h hug
    - text "Nr" · .text-cousine-metadane-male · color var(--color-text-secondary) · “01”
    - text "Tytuł" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-primary) · “Maszynopis „Wertepów”, ML, sygn. 1618”
  - **Ikona/strzalka-prawo** · w 16px, h 16px

Preview: `../previews/components/wiersz-listy.png`
