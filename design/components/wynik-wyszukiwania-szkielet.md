# Wynik wyszukiwania / Szkielet

Stan ładowania wyników: proporcje paska odpowiadają prawdziwemu wynikowi, więc układ nie skacze po wczytaniu. Pulsuje w prototypie (2 × 700 ms). W kodzie: animacja opacity, wyłączona przy prefers-reduced-motion.

## Properties

- `Faza` (variant): 1 | 2 — default 1

## Variants

### Faza=1

- box "Faza=1" · flex-column · gap 10px · padding var(--space-16) 0px var(--space-16) 0px · w 800px, h hug · border-bottom 1px var(--color-border-subtle)
  - interaction: after 50 ms → Faza=2 (smart animate 700 ms, ease-in-and-out)
  - box "Ścieżka" · w 120px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · overflow hidden
  - box "Tytuł" · w 320px, h 18px · bg var(--color-bg-media) · radius var(--radius-s) · overflow hidden
  - box "Opis" · w 560px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · overflow hidden
  - box "Opis 2" · w 420px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · overflow hidden
  - box "Metadane" · w 140px, h 8px · bg var(--color-bg-media) · radius var(--radius-s) · overflow hidden

### Faza=2

- box "Faza=2" · flex-column · gap 10px · padding var(--space-16) 0px var(--space-16) 0px · w 800px, h hug · border-bottom 1px var(--color-border-subtle)
  - interaction: after 50 ms → Faza=1 (smart animate 700 ms, ease-in-and-out)
  - box "Ścieżka" · w 120px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · opacity 45% · overflow hidden
  - box "Tytuł" · w 320px, h 18px · bg var(--color-bg-media) · radius var(--radius-s) · opacity 45% · overflow hidden
  - box "Opis" · w 560px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · opacity 45% · overflow hidden
  - box "Opis 2" · w 420px, h 10px · bg var(--color-bg-media) · radius var(--radius-s) · opacity 45% · overflow hidden
  - box "Metadane" · w 140px, h 8px · bg var(--color-bg-media) · radius var(--radius-s) · opacity 45% · overflow hidden

Preview: `../previews/components/wynik-wyszukiwania-szkielet.png`
