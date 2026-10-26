# Nagłówek strony

Jeden nagłówek dla wszystkich podstron. Etykieta: typ obiektu · autor lub kontekst · rok. Tytuł zawsze Lora.

## Properties

- `Etykieta` (text) — default “Utwór · Leopold Buczkowski · 1947”
- `Tytuł` (text) — default “Wertepy”
- `Opis` (text) — default “Pierwsza powieść Leopolda Buczkowskiego, wydana w 1947 roku. Sceny z codziennego życia podolskiej wsi w dwudziestoleciu międzywojennym.”
- `Pokaż opis` (boolean) — default true
- `Rozmiar` (variant): Desktop | Mobile — default Desktop

## Variants

### Rozmiar=Desktop

- box "Rozmiar=Desktop" · flex-column · gap var(--space-16) · padding var(--space-48) var(--layout-page-margin) var(--space-48) var(--layout-page-margin) · w 1440px, h hug · bg var(--color-bg-inverse) · paper grain (noise, white @4%)
  - box "Ornament" · w 40px, h 1px · bg var(--color-border-accent-inverse) · overflow hidden
  - text "Etykieta" · .text-cousine-etykieta · color var(--color-text-inverse-secondary) · “Utwór · Leopold Buczkowski · 1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tytul-strony · color var(--color-text-inverse) · “Wertepy”
  - text "Opis" · w 760px, h hug · .text-lora-wstep · color var(--color-text-inverse) · “Pierwsza powieść Leopolda Buczkowskiego, wydana w 1947 roku. Sceny z codziennego życia podolskiej wsi w dwudziestoleciu międzywojennym.”

### Rozmiar=Mobile

- box "Rozmiar=Mobile" · flex-column · gap var(--space-16) · padding var(--space-32) var(--layout-page-margin-mobile) var(--space-24) var(--layout-page-margin-mobile) · w 390px, h hug · bg var(--color-bg-inverse) · paper grain (noise, white @4%)
  - box "Ornament" · w 40px, h 1px · bg var(--color-border-accent-inverse) · overflow hidden
  - text "Etykieta" · w fill, h hug · .text-cousine-etykieta · color var(--color-text-inverse-secondary) · “Utwór · Leopold Buczkowski · 1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tytul-strony-mobile · color var(--color-text-inverse) · “Wertepy”
  - text "Opis" · w fill, h hug · .text-lora-glosa · color var(--color-text-inverse) · “Pierwsza powieść Leopolda Buczkowskiego, wydana w 1947 roku. Sceny z codziennego życia podolskiej wsi w dwudziestoleciu międzywojennym.”

Preview: `../previews/components/naglowek-strony.png`
