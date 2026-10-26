# Zakładka

## Properties

- `Etykieta` (text) — default “Wszystko”
- `Liczba` (text) — default “7”
- `Stan` (variant): Domyślna | Aktywna — default Domyślna

## Variants

### Stan=Domyślna

- box "Stan=Domyślna" · flex-row · gap var(--space-8) · padding var(--space-12) 0px var(--space-12) 0px · align center · w hug, h hug
  - text "Etykieta" · .text-cousine-nawigacja · color var(--color-text-secondary) · “Wszystko”
  - text "Liczba" · .text-cousine-metadane-male · color var(--color-text-secondary) · “7”

### Stan=Aktywna

- box "Stan=Aktywna" · flex-row · gap var(--space-8) · padding var(--space-12) 0px var(--space-12) 0px · align center · w hug, h hug · border-bottom 2px var(--color-border-accent)
  - text "Etykieta" · .text-cousine-nawigacja · color var(--color-text-primary) · “Wszystko”
  - text "Liczba" · .text-cousine-metadane-male · color var(--color-text-secondary) · “7”

Preview: `../previews/components/zakladka.png`
