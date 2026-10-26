# Element listy bocznej

Aktywny = bieżący obiekt na liście kontekstu.

## Properties

- `Rok` (text) — default “1947”
- `Tytuł` (text) — default “Wertepy”
- `Opis` (text) — default “Gebethner i Wolff, Warszawa”
- `Pokaż opis` (boolean) — default true
- `Stan` (variant): Domyślny | Aktywny — default Domyślny

## Variants

### Stan=Domyślny

- box "Stan=Domyślny" · flex-column · gap var(--space-4) · padding var(--space-8) 0px var(--space-8) var(--space-12) · w 240px, h hug · border-left 1px var(--color-border-subtle)
  - text "Rok" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “Wertepy”
  - text "Opis" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “Gebethner i Wolff, Warszawa”

### Stan=Aktywny

- box "Stan=Aktywny" · flex-column · gap var(--space-4) · padding var(--space-8) 0px var(--space-8) var(--space-12) · w 240px, h hug · border-left 2px var(--color-border-accent)
  - text "Rok" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-accent) · “1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “Wertepy”
  - text "Opis" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “Gebethner i Wolff, Warszawa”

Preview: `../previews/components/element-listy-bocznej.png`
