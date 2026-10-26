# Przycisk

Główny: jedna akcja na ekran. Drugorzędny: akcja pomocnicza. Wysokość 44 px (cel dotykowy). Najechanie: ciemniejszy brąz (Główny) albo ciepłe tło (Drugorzędny).

## Properties

- `Etykieta` (text) — default “Przycisk”
- `Rodzaj` (variant): Główny | Drugorzędny — default Główny
- `Stan` (variant): Domyślny | Najechany — default Domyślny

## Variants

### Rodzaj=Główny, Stan=Domyślny

- box "Rodzaj=Główny, Stan=Domyślny" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 44px · bg var(--color-bg-accent) · radius var(--radius-s)
  - interaction: on hover → Rodzaj=Główny, Stan=Najechany (smart animate 150 ms, ease-out)
  - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-inverse) · “Przycisk”

### Rodzaj=Drugorzędny, Stan=Domyślny

- box "Rodzaj=Drugorzędny, Stan=Domyślny" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 44px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - interaction: on hover → Rodzaj=Drugorzędny, Stan=Najechany (smart animate 150 ms, ease-out)
  - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-accent) · “Przycisk”

### Rodzaj=Główny, Stan=Najechany

- box "Rodzaj=Główny, Stan=Najechany" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 44px · bg var(--color-bg-accent-hover) · radius var(--radius-s)
  - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-inverse) · “Przycisk”

### Rodzaj=Drugorzędny, Stan=Najechany

- box "Rodzaj=Drugorzędny, Stan=Najechany" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 44px · bg var(--color-bg-accent-subtle) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-accent) · “Przycisk”

Preview: `../previews/components/przycisk.png`
