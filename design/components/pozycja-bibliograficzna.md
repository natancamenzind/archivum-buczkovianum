# Pozycja bibliograficzna

Format: Autor, Tytuł / Wydawnictwo, miejsce rok, s. strony.

## Properties

- `Nr` (text) — default “01”
- `Opis` (text) — default “[Autor], [Tytuł opracowania]”
- `Wydanie` (text) — default “[Wydawnictwo], [miejsce] [rok], s. [strony]”

## Structure

- box "Pozycja bibliograficzna" · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · 480px × 68px · border-bottom 1px var(--color-border-subtle)
  - text "Nr" · .text-cousine-metadane-male · color var(--color-text-secondary) · “01”
  - box "Opis" · flex-column · gap var(--space-4) · w fill, h hug
    - text "Opis" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-primary) · “[Autor], [Tytuł opracowania]”
    - text "Wydanie" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “[Wydawnictwo], [miejsce] [rok], s. [strony]”

Preview: `../previews/components/pozycja-bibliograficzna.png`
