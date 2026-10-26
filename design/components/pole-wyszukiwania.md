# Pole wyszukiwania

Jedyne pole wejściowe w serwisie. Przycisk z etykietą; „Wyczyść” z aria-label.

## Properties

- `Wartość` (text) — default “Dezerter”
- `Stan` (variant): Wypełnione | Puste — default Wypełnione

## Variants

### Stan=Wypełnione

- box "Stan=Wypełnione" · flex-row · gap var(--space-12) · padding 0px var(--space-8) 0px var(--space-16) · align center · w 880px, h 56px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - **Ikona/szukaj** · w 16px, h 16px
  - text "Wartość" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “Dezerter”
  - box "Wyczyść" · flex-row · gap 0px · justify center · align center · w 40px, h 40px
    - **Ikona/zamknij** · w 16px, h 16px
  - box "Przycisk" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 40px · bg var(--color-bg-accent) · radius var(--radius-s)
    - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-inverse) · “Szukaj”

### Stan=Puste

- box "Stan=Puste" · flex-row · gap var(--space-12) · padding 0px var(--space-8) 0px var(--space-16) · align center · w 880px, h 56px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - **Ikona/szukaj** · w 16px, h 16px
  - text "Podpowiedź" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-secondary) · “Tytuł, opis, transkrypcja lub tag”
  - box "Przycisk" · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w hug, h 40px · bg var(--color-bg-accent) · radius var(--radius-s)
    - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-inverse) · “Szukaj”

Preview: `../previews/components/pole-wyszukiwania.png`
