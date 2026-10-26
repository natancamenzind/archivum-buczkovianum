# Fragment / Zapisek

Sygnatura zawsze w formacie „ML, sygn. NNNN.NNNN”. Kadr skanu fragmentu: pełna szerokość, wysokość 160 px, obraz wypełnia kadr.

## Properties

- `Pozycja` (text) — default “Fragment 01 · rozdział I”
- `Sygnatura` (text) — default “ML, sygn. 1678.0104”
- `Opis` (text) — default “Notatka z notesu 18 o postaci dezertera.”
- `Pokaż tagi` (boolean) — default true

## Structure

- box "Fragment / Zapisek" · flex-column · gap var(--space-12) · padding 0px 0px var(--space-24) 0px · 640px × 352px · border-bottom 1px var(--color-border-subtle)
  - box "Metadane" · flex-row · justify space-between · align center · w fill, h hug
    - text "Pozycja" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Fragment 01 · rozdział I”
    - text "Rodzaj" · .text-cousine-etykieta · color var(--color-text-accent) · “Zapisek”
  - box "Skan" · flex-column · gap var(--space-8) · padding var(--space-12) · w fill, h hug · bg var(--color-bg-media) · radius var(--radius-s)
    - box "Skan zapisku — do uzupełnienia" · flex-column · gap var(--space-8) · justify center · align center · w fill, h 160px
      - **Ikona/zapisek** · w 16px, h 16px
      - text "Opis zastępczy" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Skan zapisku — do uzupełnienia”
  - text "Sygnatura" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “ML, sygn. 1678.0104”
  - text "Opis" · w fill, h hug · .text-lora-glosa · color var(--color-text-secondary) · “Notatka z notesu 18 o postaci dezertera.”
  - box "Tagi" · flex-row · gap var(--space-8) · w fill, h hug
    - **Tag [Stan=Domyślny]** {Nazwa=“Dezerter”, Stan=“Domyślny”} · flex-row · gap 0px · padding var(--space-4) var(--space-12) var(--space-4) var(--space-12) · w hug, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-full)

Preview: `../previews/components/fragment-zapisek.png`
