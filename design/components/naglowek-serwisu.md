# Nagłówek serwisu

Mobile: ikona wyszukiwania to link do strony wyszukiwania (aria-label „Szukaj w archiwum”). Nawigacja główna mobile jest w dolnym pasku.

## Properties

- `Rozmiar` (variant): Desktop | Mobile — default Desktop

## Variants

### Rozmiar=Desktop

- box "Rozmiar=Desktop" · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w 1440px, h 88px · bg var(--color-bg-page) · border-bottom 1px var(--color-border-subtle)
  - box "Logo" · flex-row · gap var(--space-12) · align center · w hug, h hug
    - **Ikona/ksiazka** · w 20px, h 20px
    - text "Nazwa" · .text-lora-tytul-elementu · color var(--color-text-primary) · “Archivum Buczkovianum”
    - text "Podpis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Archiwum literackie”
  - box "Nawigacja" · flex-row · gap var(--space-32) · align center · w hug, h hug
    - text "O archiwum" · .text-cousine-nawigacja · color var(--color-text-primary) · “O archiwum”
    - box "Szukaj" · flex-row · gap var(--space-8) · align center · w hug, h hug
      - **Ikona/szukaj** · w 16px, h 16px
      - text "Etykieta" · .text-cousine-nawigacja · color var(--color-text-primary) · “Szukaj w archiwum”
  - rect "Listwa akcentu" · w 1440px, h 3px · position absolute at (0, 0) · bg var(--color-bg-accent)

### Rozmiar=Mobile

- box "Rozmiar=Mobile" · flex-row · padding 0px var(--layout-page-margin-mobile) 0px var(--layout-page-margin-mobile) · justify space-between · align center · w 390px, h 64px · bg var(--color-bg-page) · border-bottom 1px var(--color-border-subtle)
  - box "Logo" · flex-row · gap var(--space-12) · align center · w hug, h hug
    - **Ikona/ksiazka** · w 20px, h 20px
    - text "Nazwa" · .text-lora-tekst · color var(--color-text-primary) · “Archivum Buczkovianum”
  - box "Nawigacja" · flex-row · gap var(--space-32) · align center · w hug, h hug
    - box "Szukaj" · flex-row · gap 0px · justify center · align center · w 44px, h 44px
      - **Ikona/szukaj** · w 16px, h 16px
  - rect "Listwa akcentu" · w 390px, h 3px · position absolute at (0, 0) · bg var(--color-bg-accent)

Preview: `../previews/components/naglowek-serwisu.png`
