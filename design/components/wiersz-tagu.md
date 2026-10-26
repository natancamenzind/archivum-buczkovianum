# Wiersz tagu

Pozycja indeksu tagów. Liczba wystąpień z poprawną odmianą.

## Properties

- `Nazwa` (text) — default “Dezerter”
- `Wystąpienia` (text) — default “4 wystąpienia”

## Structure

- box "Wiersz tagu" · flex-row · padding var(--space-12) 0px var(--space-12) 0px · justify space-between · align center · 560px × 52px · border-bottom 1px var(--color-border-subtle)
  - text "Nazwa" · .text-lora-tekst · color var(--color-text-primary) · “Dezerter”
  - box "Liczba i strzałka" · flex-row · gap var(--space-12) · align center · w hug, h hug
    - text "Wystąpienia" · .text-cousine-metadane-male · color var(--color-text-secondary) · “4 wystąpienia”
    - **Ikona/strzalka-prawo** · w 16px, h 16px

Preview: `../previews/components/wiersz-tagu.png`
