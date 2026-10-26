# Pole wyboru

## Properties

- `Etykieta` (text) — default “Wertepy”
- `Liczba` (text) — default “2”
- `Pokaż liczbę` (boolean) — default true
- `Zaznaczone` (variant): Nie | Tak — default Nie

## Variants

### Zaznaczone=Nie

- box "Zaznaczone=Nie" · flex-row · gap var(--space-8) · align center · w hug, h hug
  - box "Pole" · flex-row · gap 0px · justify center · align center · w 16px, h 16px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - text "Etykieta" · .text-cousine-metadane · color var(--color-text-primary) · “Wertepy”
  - text "Liczba" · .text-cousine-metadane-male · color var(--color-text-secondary) · “2”

### Zaznaczone=Tak

- box "Zaznaczone=Tak" · flex-row · gap var(--space-8) · align center · w hug, h hug
  - box "Pole" · flex-row · gap 0px · justify center · align center · w 16px, h 16px · bg var(--color-bg-accent) · border 1px var(--color-border-accent) · radius var(--radius-s)
    - **Ikona/zaznacz** · w 12px, h 12px
  - text "Etykieta" · .text-cousine-metadane · color var(--color-text-primary) · “Wertepy”
  - text "Liczba" · .text-cousine-metadane-male · color var(--color-text-secondary) · “2”

Preview: `../previews/components/pole-wyboru.png`
