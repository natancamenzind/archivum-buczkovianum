# Karta utworu

Stała wysokość, stopka przypięta do dołu niezależnie od długości tytułu. Okładka: plansza zastępcza do czasu dostarczenia skanów. Najechanie: karta unosi się (Cień/uniesiony), tytuł przechodzi w akcent.

## Properties

- `Kategoria i rok` (text) — default “Powieść · 1947”
- `Tytuł` (text) — default “Wertepy”
- `Autor` (text) — default “Leopold Buczkowski”
- `Fragmenty` (text) — default “24 fragmenty”
- `Stan` (variant): Domyślny | Najechany — default Domyślny

## Variants

### Stan=Domyślny

- box "Stan=Domyślny" · flex-column · gap var(--space-12) · padding var(--space-16) · w 304px, h 440px · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
  - interaction: on hover → Stan=Najechany (smart animate 180 ms, ease-out)
  - box "Okładka" · flex-column · gap var(--space-8) · justify center · align center · w fill, h 200px · bg image(assets/images/okladka-2f232c11.*, fit) over var(--color-bg-media) · radius var(--radius-s)
  - text "Kategoria" · w fill, h hug · .text-cousine-etykieta · color var(--color-text-accent) · “Powieść · 1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-primary) · “Wertepy”
  - text "Autor" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “Leopold Buczkowski”
  - box "Odstęp" · flex-column · gap 0px · w fill, h fill
  - box "Stopka karty" · flex-row · padding var(--space-12) 0px 0px 0px · justify space-between · align center · w fill, h hug · border-top 1px var(--color-border-subtle)
    - text "Fragmenty" · .text-cousine-metadane-male · color var(--color-text-secondary) · “24 fragmenty”
    - **Ikona/strzalka-ukos** · w 16px, h 16px

### Stan=Najechany

- box "Stan=Najechany" · flex-column · gap var(--space-12) · padding var(--space-16) · w 304px, h 440px · bg var(--color-bg-card) · border 1px var(--color-border-accent-subtle) · radius var(--radius-m) · shadow var(--shadow-uniesiony)
  - box "Okładka" · flex-column · gap var(--space-8) · justify center · align center · w fill, h 200px · bg image(assets/images/okladka-2f232c11.*, fit) over var(--color-bg-media) · radius var(--radius-s)
  - text "Kategoria" · w fill, h hug · .text-cousine-etykieta · color var(--color-text-accent) · “Powieść · 1947”
  - text "Tytuł" · w fill, h hug · .text-lora-tytul-elementu · color var(--color-text-accent) · “Wertepy”
  - text "Autor" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “Leopold Buczkowski”
  - box "Odstęp" · flex-column · gap 0px · w fill, h fill
  - box "Stopka karty" · flex-row · padding var(--space-12) 0px 0px 0px · justify space-between · align center · w fill, h hug · border-top 1px var(--color-border-accent-subtle)
    - text "Fragmenty" · .text-cousine-metadane-male · color var(--color-text-secondary) · “24 fragmenty”
    - **Ikona/strzalka-ukos** · w 16px, h 16px

Preview: `../previews/components/karta-utworu.png`
