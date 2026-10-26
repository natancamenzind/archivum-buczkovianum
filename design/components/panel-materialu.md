# Panel materiału

Główny materiał strony tekstu sekundarnego i strony maszynopisu. Zastępuje trzy osobne wersje ekranu.

## Properties

- `Strona` (text) — default “Skan · strona 1 z 4”
- `Typ` (variant): Skan | Transkrypcja | Nagranie — default Skan

## Variants

### Typ=Skan

- box "Typ=Skan" · flex-column · gap var(--space-12) · padding var(--space-16) · w 640px, h hug · bg var(--color-bg-media) · radius var(--radius-m)
  - box "Pasek" · flex-row · justify space-between · align center · w fill, h hug
    - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Skan · strona 1 z 4”
    - box "Strony" · flex-row · gap var(--space-8) · w hug, h hug
      - **Ikona/wstecz** · w 16px, h 16px
      - **Ikona/dalej** · w 16px, h 16px
  - rect "Obraz strony" · w fill, h 780px · bg image(assets/images/obraz-strony-7d71634a.*, fit) · shadow var(--shadow-dokument)

### Typ=Transkrypcja

- box "Typ=Transkrypcja" · flex-column · gap var(--space-12) · padding var(--space-16) · w 640px, h hug · bg var(--color-bg-media) · radius var(--radius-m)
  - box "Pasek" · flex-row · gap 0px · justify space-between · align center · w fill, h hug
    - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Transkrypcja · układ oryginału zachowany”
  - box "Transkrypcja" · flex-column · gap var(--space-16) · padding var(--space-32) · w fill, h hug · bg var(--color-bg-card) · radius var(--radius-s)
    - text "Data" · w fill, h hug · .text-lora-tekst · color var(--color-text-secondary) · text-align right · “[Miejscowość, data]”
    - text "Nagłówek" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Nagłówek listu]”
    - text "Treść" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Treść listu w transkrypcji dyplomatycznej: podział na wiersze i akapity jak w oryginale, skreślenia i dopiski oznaczone zgodnie z zasadami edytorskimi archiwum.]”
    - text "Treść 2" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · “[Ciąg dalszy treści listu.]”
    - text "Podpis" · w fill, h hug · .text-lora-tekst · color var(--color-text-primary) · text-align right · “[Podpis]”

### Typ=Nagranie

- box "Typ=Nagranie" · flex-column · gap var(--space-12) · padding var(--space-16) · w 640px, h hug · bg var(--color-bg-media) · radius var(--radius-m)
  - box "Pasek" · flex-row · gap 0px · justify space-between · align center · w fill, h hug
    - text "Opis" · .text-cousine-metadane-male · color var(--color-text-secondary) · “Nagranie audio · 12:34”
  - box "Odtwarzacz" · flex-row · gap var(--space-12) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w fill, h hug · bg var(--color-bg-card) · radius var(--radius-s)
    - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-accent) · radius var(--radius-l)
      - **Ikona/odtworz** · w 16px, h 16px
    - rect "Postęp" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
    - text "Czas" · .text-cousine-metadane-male · color var(--color-text-secondary) · “00:00 / 12:34”
  - text "Opis nagrania" · w fill, h hug · .text-lora-tekst-maly · color var(--color-text-secondary) · “[Opis nagrania: kto mówi, kiedy i gdzie nagrano, źródło]”

Preview: `../previews/components/panel-materialu.png`
