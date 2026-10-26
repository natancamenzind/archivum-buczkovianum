# Osoba

## Properties

- `Imię i nazwisko` (text) — default “[Imię i nazwisko]”
- `Rola` (text) — default “[Rola w projekcie]”
- `Biogram` (text) — default “[Biogram: dwa, trzy zdania]”

## Structure

- box "Osoba" · flex-column · gap var(--space-4) · padding var(--space-12) 0px var(--space-12) 0px · 640px × 100px · border-bottom 1px var(--color-border-subtle)
  - text "Imię i nazwisko" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “[Imię i nazwisko]”
  - text "Rola" · w fill, h hug · .text-cousine-metadane-male · color var(--color-text-accent) · “[Rola w projekcie]”
  - text "Biogram" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “[Biogram: dwa, trzy zdania]”

Preview: `../previews/components/osoba.png`
