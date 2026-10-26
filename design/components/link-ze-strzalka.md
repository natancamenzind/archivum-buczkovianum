# Link ze strzałką

Jedyny wzorzec linku „więcej”. Etykieta zawsze mówi, dokąd prowadzi, z liczbą elementów. Najechanie: podkreślenie i strzałka odsuwa się o 4 px.

## Properties

- `Etykieta` (text) — default “Wszystkie fragmenty (24)”
- `Stan` (variant): Domyślny | Najechany — default Domyślny

## Variants

### Stan=Domyślny

- box "Stan=Domyślny" · flex-row · gap var(--space-4) · align center · w hug, h hug
  - interaction: on hover → Stan=Najechany (smart animate 180 ms, ease-out)
  - text "Etykieta" · .text-cousine-metadane · color var(--color-text-accent) · “Wszystkie fragmenty (24)”
  - **Ikona/strzalka-prawo** · w 16px, h 16px

### Stan=Najechany

- box "Stan=Najechany" · flex-row · gap var(--space-8) · align center · w hug, h hug
  - text "Etykieta" · .text-cousine-metadane · color var(--color-text-accent-hover) · “Wszystkie fragmenty (24)”
  - **Ikona/strzalka-prawo** · w 16px, h 16px

Preview: `../previews/components/link-ze-strzalka.png`
