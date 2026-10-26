# Stopka

Aktywna pozycja wynika z typu strony: strona główna → Strona główna; utwór → Utwory; maszynopis → Maszynopisy; tag → Tagi; wyszukiwanie, tekst sekundarny, O archiwum → brak aktywnej.

## Properties

- `Rozmiar` (variant): Desktop | Mobile — default Desktop

## Variants

### Rozmiar=Desktop

- box "Rozmiar=Desktop" · flex-row · padding 0px var(--layout-page-margin) 0px var(--layout-page-margin) · justify space-between · align center · w 1440px, h 88px · bg var(--color-bg-page) · border-top 1px var(--color-border-subtle)
  - box "Sygnatura" · flex-column · gap var(--space-4) · w hug, h hug
    - text "Nazwa" · .text-cousine-etykieta · color var(--color-text-primary) · “Archivum Buczkovianum”
    - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Archiwum literackie Leopolda Buczkowskiego”
  - box "Nawigacja główna" · flex-row · gap 0px · w hug, h hug
    - **Pozycja nawigacji [Układ=Poziomy, Stan=Domyślna]** {Etykieta=“Strona główna”, Układ=“Poziomy”, Stan=“Domyślna”} · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px
    - **Pozycja nawigacji [Układ=Poziomy, Stan=Domyślna]** {Etykieta=“Utwory”, Układ=“Poziomy”, Stan=“Domyślna”} · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px
    - **Pozycja nawigacji [Układ=Poziomy, Stan=Domyślna]** {Etykieta=“Maszynopisy”, Układ=“Poziomy”, Stan=“Domyślna”} · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px
    - **Pozycja nawigacji [Układ=Poziomy, Stan=Domyślna]** {Etykieta=“Tagi”, Układ=“Poziomy”, Stan=“Domyślna”} · flex-row · gap var(--space-8) · padding 0px var(--space-16) 0px var(--space-16) · align center · w hug, h 88px
  - text "Język" · .text-cousine-metadane · color var(--color-text-secondary) · “Polski / Українська”

### Rozmiar=Mobile

- box "Rozmiar=Mobile" · flex-column · gap 0px · w 390px, h hug · bg var(--color-bg-page) · border-top 1px var(--color-border-subtle)
  - box "Nawigacja główna" · flex-row · gap 0px · w fill, h hug
    - **Pozycja nawigacji [Układ=Pionowy, Stan=Domyślna]** {Etykieta=“Strona główna”, Układ=“Pionowy”, Stan=“Domyślna”} · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w fill, h 64px
    - **Pozycja nawigacji [Układ=Pionowy, Stan=Domyślna]** {Etykieta=“Utwory”, Układ=“Pionowy”, Stan=“Domyślna”} · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w fill, h 64px
    - **Pozycja nawigacji [Układ=Pionowy, Stan=Domyślna]** {Etykieta=“Maszynopisy”, Układ=“Pionowy”, Stan=“Domyślna”} · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w fill, h 64px
    - **Pozycja nawigacji [Układ=Pionowy, Stan=Domyślna]** {Etykieta=“Tagi”, Układ=“Pionowy”, Stan=“Domyślna”} · flex-column · gap var(--space-4) · padding var(--space-8) var(--space-4) var(--space-8) var(--space-4) · justify center · align center · w fill, h 64px
  - box "Język" · flex-row · gap 0px · padding var(--space-8) 0px var(--space-8) 0px · justify center · w fill, h hug
    - text "Język" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Polski / Українська”

Preview: `../previews/components/stopka.png`
