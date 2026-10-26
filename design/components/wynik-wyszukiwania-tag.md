# Wynik wyszukiwania / Tag

Wspólna siatka wyników; typ obiektu decyduje o wariancie. W ekranach szerokość wypełnia kontener.

## Properties

- `Tytuł` (text) — default “Dezerter”
- `Opis` (text) — default “Postać dezertera w prozie Buczkowskiego: fragmenty utworów i zapiski połączone wspólnym motywem.”
- `Liczba` (text) — default “4 wystąpienia”

## Structure

- box "Wynik wyszukiwania / Tag" · flex-column · gap var(--space-8) · padding var(--space-16) 0px var(--space-16) 0px · 800px × 118px · border-bottom 1px var(--color-border-subtle)
  - text "Tytuł" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-accent) · “Dezerter”
  - text "Opis" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “Postać dezertera w prozie Buczkowskiego: fragmenty utworów i zapiski połączone wspólnym motywem.”
  - box "Akcja" · flex-row · gap var(--space-16) · align center · w hug, h hug
    - text "Liczba" · .text-cousine-metadane-male · color var(--color-text-secondary) · “4 wystąpienia”
    - **Link ze strzałką [Stan=Domyślny]** {Etykieta=“Otwórz tag”, Stan=“Domyślny”} · flex-row · gap var(--space-4) · align center · w hug, h hug

Preview: `../previews/components/wynik-wyszukiwania-tag.png`
