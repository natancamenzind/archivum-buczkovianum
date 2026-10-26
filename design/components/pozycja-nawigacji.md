# Pozycja nawigacji

Poziomy: stopka desktop. Pionowy: dolna nawigacja mobile. Aktywna = sekcja typu bieżącej strony.

## Properties

- `Ikona` (instance_swap)
- `Etykieta` (text) — default “Strona główna”
- `Układ` (variant): Poziomy | Pionowy — default Poziomy
- `Stan` (variant): Domyślna | Aktywna — default Domyślna

## Variants

### Układ=Poziomy, Stan=Domyślna

- box "Układ=Poziomy, Stan=Domyślna" · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px
  - **Ikona/dom** · w 16px, h 16px
  - text "Etykieta" · .text-cousine-nawigacja · color var(--color-text-secondary) · “Strona główna”

### Układ=Poziomy, Stan=Aktywna

- box "Układ=Poziomy, Stan=Aktywna" · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px · border-top 2px var(--color-border-accent)
  - **Ikona/dom** · w 16px, h 16px
  - text "Etykieta" · .text-cousine-nawigacja · color var(--color-text-accent) · “Strona główna”

### Układ=Pionowy, Stan=Domyślna

- box "Układ=Pionowy, Stan=Domyślna" · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w 88px, h 64px
  - **Ikona/dom** · w 16px, h 16px
  - text "Etykieta" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Strona główna”

### Układ=Pionowy, Stan=Aktywna

- box "Układ=Pionowy, Stan=Aktywna" · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w 88px, h 64px · border-top 2px var(--color-border-accent)
  - **Ikona/dom** · w 16px, h 16px
  - text "Etykieta" · .text-cousine-metadane-male · color var(--color-text-accent) · “Strona główna”

Preview: `../previews/components/pozycja-nawigacji.png`
