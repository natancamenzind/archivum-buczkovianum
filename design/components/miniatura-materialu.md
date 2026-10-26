# Miniatura materiału

Plansza zastępcza do czasu dostarczenia zdjęć. Proporcja 3:2.

## Properties

- `Podpis` (text) — default “[Podpis], ML, sygn. [numer]”

## Structure

- box "Miniatura materiału" · flex-column · gap var(--space-8) · 176px × 160px
  - box "Obraz — do uzupełnienia" · flex-row · gap 0px · justify center · align center · w 176px, h 120px · bg var(--color-bg-media) · radius var(--radius-s)
    - **Ikona/obraz** · w 16px, h 16px
  - text "Podpis" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-secondary) · “[Podpis], ML, sygn. [numer]”

Preview: `../previews/components/miniatura-materialu.png`
