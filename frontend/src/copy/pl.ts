/** Polish UI copy. Components never contain inline Polish text (AGENTS.md). */

/** The three Polish plural forms of a noun: 1 fragment, 2–4 fragmenty, 5+ fragmentów. */
export interface PluralForms {
  one: string;
  few: string;
  many: string;
}

const pluralRules = new Intl.PluralRules("pl");

/**
 * The plural form for `count`, by the Polish rules of `Intl.PluralRules`.
 *
 * "few" is used when the last digit is 2–4, except for 12–14 (22 fragmenty, 12 fragmentów).
 * Every other count except 1, including 0, takes "many". Fractions ("other" in Polish) are not
 * counts the UI shows, so they take "many" too.
 */
export function plural(count: number, forms: PluralForms): string {
  switch (pluralRules.select(count)) {
    case "one":
      return forms.one;
    case "few":
      return forms.few;
    default:
      return forms.many;
  }
}

/** A count with its noun, e.g. "24 fragmenty". */
export function formatCount(count: number, forms: PluralForms): string {
  return `${String(count)} ${plural(count, forms)}`;
}

/** Nouns of the object dictionary (design/rules.md) that are counted in the UI. */
export const nouns = {
  fragment: { one: "fragment", few: "fragmenty", many: "fragmentów" },
  occurrence: { one: "wystąpienie", few: "wystąpienia", many: "wystąpień" },
  work: { one: "utwór", few: "utwory", many: "utworów" },
  typescript: { one: "maszynopis", few: "maszynopisy", many: "maszynopisów" },
  note: { one: "zapisek", few: "zapiski", many: "zapisków" },
  tag: { one: "tag", few: "tagi", many: "tagów" },
  result: { one: "wynik", few: "wyniki", many: "wyników" },
} as const satisfies Record<string, PluralForms>;

export const copy = {
  siteName: "Archivum Buczkovianum",
  home: {
    lead: "Cyfrowe archiwum twórczości Leopolda Buczkowskiego. Strona jest w budowie.",
    apiLoading: "Łączę się z archiwum…",
    apiReady: (title: string, version: string) => `Połączono z ${title}, wersja ${version}.`,
    apiError: "Nie udało się połączyć z archiwum.",
  },
  notFound: {
    title: "Nie znaleziono strony",
    body: "Pod tym adresem nie ma żadnej strony.",
    backHome: "Wróć na stronę główną",
  },
} as const;
