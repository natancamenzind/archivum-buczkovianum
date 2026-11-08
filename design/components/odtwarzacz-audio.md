# Odtwarzacz audio

Własny odtwarzacz nagrań podlinkowanych po URL (element audio przeglądarki), bez odtwarzaczy zewnętrznych dostawców. Szeroki: desktop, w Panelu materiału i na stronie materiału. Wąski: mobile.

Sterowanie: Odtwórz / Wstrzymaj, suwak postępu (kliknięcie i przeciąganie), czas bieżący i całkowity. Szerokość „Postęp” = czas bieżący / czas całkowity.

Stany: Wstrzymany (także przed pierwszym odtworzeniem), Odtwarzanie, Przewijanie (przeciąganie suwaka: większy uchwyt z obwódką, czas bieżący w akcencie pokazuje miejsce docelowe), Ładowanie (przed wczytaniem metadanych i przy buforowaniu: „--:--”, suwak 40%), Błąd (adres nie działa albo format jest nieobsługiwany: komunikat i link do źródła w nowej karcie). Wszystkie stany mają tę samą wysokość, żeby układ nie przeskakiwał.

Najechanie i :focus-visible: Odtwórz → tlo/akcent-najechane; uchwyt suwaka jak w stanie Przewijanie. Przejście 150 ms, wyłączone przy prefers-reduced-motion.

Dostępność: aria-label „Odtwórz” / „Wstrzymaj”. Suwak: role slider, aria-label „Postęp nagrania”, aria-valuetext „2 min 15 s z 12 min 34 s”; strzałki ±5 s, Home / End. Przycisk 44 px w układzie Wąskim (cel dotykowy). Czas w Cousine: krój o stałej szerokości, cyfry nie skaczą.

## Properties

- `Układ` (variant): Szeroki | Wąski — default Szeroki
- `Stan` (variant): Wstrzymany | Odtwarzanie | Przewijanie | Ładowanie | Błąd — default Wstrzymany

## Variants

### Układ=Szeroki, Stan=Wstrzymany

- box "Układ=Szeroki, Stan=Wstrzymany" · flex-row · gap var(--space-12) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 608px, h hug · at (24, 24) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/odtworz** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “00:00”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 16px
    - rect "Postęp" · w 0.01px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 12px, h 12px · bg var(--color-bg-accent)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Szeroki, Stan=Odtwarzanie

- box "Układ=Szeroki, Stan=Odtwarzanie" · flex-row · gap var(--space-12) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 608px, h hug · at (24, 114) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/pauza** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “02:15”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 16px
    - rect "Postęp" · w 74.16px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 12px, h 12px · bg var(--color-bg-accent)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Szeroki, Stan=Przewijanie

- box "Układ=Szeroki, Stan=Przewijanie" · flex-row · gap var(--space-12) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 608px, h hug · at (24, 204) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/pauza** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-accent) · “04:40”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 16px
    - rect "Postęp" · w 150.96px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 16px, h 16px · bg var(--color-bg-accent) · border 4px var(--color-bg-accent-subtle)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Szeroki, Stan=Ładowanie

- box "Układ=Szeroki, Stan=Ładowanie" · flex-row · gap var(--space-12) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 608px, h hug · at (24, 294) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 40px, h 40px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/ladowanie** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “--:--”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 16px · opacity 40%
    - rect "Postęp" · w 0.01px, h 4px · bg var(--color-bg-accent) · radius 2px
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “--:--”

### Układ=Szeroki, Stan=Błąd

- box "Układ=Szeroki, Stan=Błąd" · flex-row · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · justify space-between · align center · w 608px, h 66px · at (24, 384) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - text "Komunikat" · w fill, h hug · .text-cousine-metadane · color var(--color-text-secondary) · “Nie udało się wczytać nagrania.”
  - box "Link" · flex-row · gap var(--space-4) · align center · w hug, h hug
    - text "Etykieta" · .text-cousine-metadane · color var(--color-text-accent) · “Otwórz nagranie”
    - **Ikona/strzalka-ukos** · w 16px, h 16px

### Układ=Wąski, Stan=Wstrzymany

- box "Układ=Wąski, Stan=Wstrzymany" · flex-row · gap var(--space-8) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 326px, h hug · at (680, 24) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/odtworz** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “00:00”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 24px
    - rect "Postęp" · w 0.01px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 12px, h 12px · bg var(--color-bg-accent)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Wąski, Stan=Odtwarzanie

- box "Układ=Wąski, Stan=Odtwarzanie" · flex-row · gap var(--space-8) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 326px, h hug · at (680, 118) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/pauza** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “02:15”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 24px
    - rect "Postęp" · w 24.84px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 12px, h 12px · bg var(--color-bg-accent)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Wąski, Stan=Przewijanie

- box "Układ=Wąski, Stan=Przewijanie" · flex-row · gap var(--space-8) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 326px, h hug · at (680, 212) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/pauza** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-accent) · “04:40”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 24px
    - rect "Postęp" · w 49.58px, h 4px · bg var(--color-bg-accent) · radius 2px
    - ellipse "Uchwyt" · w 16px, h 16px · bg var(--color-bg-accent) · border 4px var(--color-bg-accent-subtle)
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “12:34”

### Układ=Wąski, Stan=Ładowanie

- box "Układ=Wąski, Stan=Ładowanie" · flex-row · gap var(--space-8) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · align center · w 326px, h hug · at (680, 306) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - box "Odtwórz" · flex-row · gap 0px · justify center · align center · w 44px, h 44px · bg var(--color-bg-accent) · radius var(--radius-full)
    - **Ikona/ladowanie** · w 16px, h 16px
  - text "Czas bieżący" · .text-cousine-metadane · color var(--color-text-primary) · “--:--”
  - box "Suwak" · flex-row · gap 0px · align center · w fill, h 24px · opacity 40%
    - rect "Postęp" · w 0.01px, h 4px · bg var(--color-bg-accent) · radius 2px
    - rect "Reszta" · w fill, h 4px · bg var(--color-bg-media) · radius 2px
  - text "Czas całkowity" · .text-cousine-metadane · color var(--color-text-secondary) · “--:--”

### Układ=Wąski, Stan=Błąd

- box "Układ=Wąski, Stan=Błąd" · flex-column · gap var(--space-4) · padding var(--space-12) var(--space-16) var(--space-12) var(--space-16) · justify center · w 326px, h 70px · at (680, 400) · bg var(--color-bg-subtle) · border 1px var(--color-border-subtle) · radius var(--radius-m)
  - text "Komunikat" · w fill, h hug · .text-cousine-metadane · color var(--color-text-secondary) · “Nie udało się wczytać nagrania.”
  - box "Link" · flex-row · gap var(--space-4) · align center · w hug, h hug
    - text "Etykieta" · .text-cousine-metadane · color var(--color-text-accent) · “Otwórz nagranie”
    - **Ikona/strzalka-ukos** · w 16px, h 16px

Preview: `../previews/components/odtwarzacz-audio.png`
