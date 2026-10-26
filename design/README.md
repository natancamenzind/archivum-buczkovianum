# Design export

Generated from the Figma file "archiwum buczkowski model" (page "po korekcie") by `tools/export-figma.js`.
**Figma is the source of truth.** Never edit files in `design/` by hand: change Figma, re-export, commit the diff.

## How to build from this

1. Read `rules.md` first: object dictionary, call-number format, navigation, typography, hover and loading states.
2. Import `tokens/tokens.css` once, globally. Use only its custom properties and `.text-*` classes.
   Never hard-code a color, spacing, radius, shadow or font value that exists as a token.
3. Build components from `components/*.md` before screens. Screens are composed only of those components.
4. Screens: `screens/*.md` is the spec; `previews/**/*.png` is for visual verification only.
   If a preview and a spec disagree, the spec wins.

## Spec notation

- `box` = container, `text` = text node, **bold name** = component instance with `{property=value}`.
- `flex-row` / `flex-column` = auto layout; `gap`, `padding`, `justify`, `align` map 1:1 to flexbox.
- `w fill` = stretch on that axis (`flex: 1` / `align-self: stretch`), `hug` = fit content, a px value = fixed.
- `var(--…)` = token from `tokens.css`; a raw hex or px value means the design does not use a token there.
- `.text-…` = text style class from `tokens.css`; text in “…” is the real copy (UI language: Polish).
- `override` = instance content that differs from the component default.
- `interaction` = prototype behaviour; implement as CSS transitions (respect `prefers-reduced-motion`).
- `image(assets/images/…)` = placeholder or real image asset; icons are in `assets/icons/` (stroke uses `currentColor`).

## Components

- [Nagłówek kolumny](components/naglowek-kolumny.md)
- [Nagłówek sekcji](components/naglowek-sekcji.md)
- [Wiersz listy](components/wiersz-listy.md)
- [Pozycja bibliograficzna](components/pozycja-bibliograficzna.md)
- [Miniatura materiału](components/miniatura-materialu.md)
- [Lista rozwijana](components/lista-rozwijana.md)
- [Element listy bocznej](components/element-listy-bocznej.md)
- [Zakładka](components/zakladka.md)
- [Pole wyboru](components/pole-wyboru.md)
- [Pozycja nawigacji](components/pozycja-nawigacji.md)
- [Tag](components/tag.md)
- [Link ze strzałką](components/link-ze-strzalka.md)
- [Nagłówek serwisu](components/naglowek-serwisu.md)
- [Stopka](components/stopka.md)
- [Nagłówek strony](components/naglowek-strony.md)
- [Pole wyszukiwania](components/pole-wyszukiwania.md)
- [Fragment / Maszynopis](components/fragment-maszynopis.md)
- [Fragment / Zapisek](components/fragment-zapisek.md)
- [Panel materiału](components/panel-materialu.md)
- [Osoba](components/osoba.md)
- [Przycisk](components/przycisk.md)
- [Wiersz tagu](components/wiersz-tagu.md)
- [Materiały kontekstowe](components/materialy-kontekstowe.md)
- [Wynik wyszukiwania / Utwór](components/wynik-wyszukiwania-utwor.md)
- [Wynik wyszukiwania / Fragment](components/wynik-wyszukiwania-fragment.md)
- [Wynik wyszukiwania / Zapisek](components/wynik-wyszukiwania-zapisek.md)
- [Wynik wyszukiwania / Tag](components/wynik-wyszukiwania-tag.md)
- [Karta utworu](components/karta-utworu.md)
- [Wynik wyszukiwania / Szkielet](components/wynik-wyszukiwania-szkielet.md)

## Screens

- [Strona główna](screens/strona-glowna.md)
- [Utwór — Wertepy](screens/utwor-wertepy.md)
- [Maszynopis — Wertepy, ML, sygn. 1618](screens/maszynopis-wertepy-ml-sygn-1618.md)
- [Tag — Dezerter](screens/tag-dezerter.md)
- [Tekst sekundarny — List nr 32](screens/tekst-sekundarny-list-nr-32.md)
- [O archiwum](screens/o-archiwum.md)
- [Wyszukiwanie — wyniki](screens/wyszukiwanie-wyniki.md)
- [Wyszukiwanie — brak wyników](screens/wyszukiwanie-brak-wynikow.md)
- [Lista — Utwory](screens/lista-utwory.md)
- [Lista — Maszynopisy](screens/lista-maszynopisy.md)
- [Lista — Tagi](screens/lista-tagi.md)
- [Wyszukiwanie — ładowanie](screens/wyszukiwanie-ladowanie.md)
- [Utwór — Wertepy (mobile)](screens/utwor-wertepy-mobile.md) (mobile)
- [Wyszukiwanie — wyniki (mobile)](screens/wyszukiwanie-wyniki-mobile.md) (mobile)
- [Wyszukiwanie — panel filtrów (mobile)](screens/wyszukiwanie-panel-filtrow-mobile.md) (mobile)
