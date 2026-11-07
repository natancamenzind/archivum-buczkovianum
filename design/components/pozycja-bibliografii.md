# Pozycja bibliografii

Jedna pozycja bibliografii utworu: numer i dowolny tekst wpisany przez redakcję (jedna lub kilka linii). Używana w sekcji „Bibliografia” na stronie utworu i na stronie bibliografii.

## Properties

- `Nr` (text) — default “01”
- `Treść` (text) — default “[Autor], [Tytuł opracowania], [Wydawnictwo], [miejsce] [rok], s. [strony]”

## Structure

- box "Pozycja bibliografii" · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · 480px × 71px · border-bottom 1px var(--color-border-subtle)
  - text "Nr" · .text-cousine-metadane-male · color var(--color-text-secondary) · “01”
  - box "Treść" · flex-column · gap var(--space-4) · w fill, h hug
    - text "Treść" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-primary) · “[Autor], [Tytuł opracowania], [Wydawnictwo], [miejsce] [rok], s. [strony]”

Preview: `../previews/components/pozycja-bibliografii.png`
