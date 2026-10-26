# Nagłówek sekcji

Licznik: „pokazane z wszystkich” albo sama liczba elementów. Brak sortowania i zwijania w trybie czytelnika.

## Properties

- `Tytuł` (text) — default “Fragmenty maszynopisu”
- `Licznik` (text) — default “2 z 24”
- `Pokaż licznik` (boolean) — default true
- `Opis` (text) — default “Wybór redakcji, w kolejności tekstu”
- `Pokaż opis` (boolean) — default true

## Structure

- box "Nagłówek sekcji" · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · 640px × 72px · border-bottom 1px var(--color-border-subtle)
  - box "Wiersz tytułu" · flex-row · justify space-between · align end · w fill, h hug
    - text "Tytuł" · w fill, h hug · .text-lora-tytul-sekcji · color var(--color-text-primary) · “Fragmenty maszynopisu”
    - text "Licznik" · .text-cousine-metadane · color var(--color-text-secondary) · “2 z 24”
  - text "Opis" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “Wybór redakcji, w kolejności tekstu”

Preview: `../previews/components/naglowek-sekcji.png`
