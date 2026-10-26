# Tag

Pigułka: tag to etykieta tematyczna, nie przycisk. Klik prowadzi do strony tagu. Najechanie: ciepłe tło i akcent, przejście 180 ms.

## Properties

- `Nazwa` (text) — default “Dezerter”
- `Stan` (variant): Domyślny | Najechany — default Domyślny

## Variants

### Stan=Domyślny

- box "Stan=Domyślny" · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)
  - interaction: on hover → Stan=Najechany (smart animate 180 ms, ease-out)
  - text "Nazwa" · .text-cousine-metadane · color var(--color-text-primary) · “Dezerter”

### Stan=Najechany

- box "Stan=Najechany" · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-accent-subtle) · border 1px var(--color-border-accent) · radius var(--radius-full)
  - text "Nazwa" · .text-cousine-metadane · color var(--color-text-accent) · “Dezerter”

Preview: `../previews/components/tag.png`
