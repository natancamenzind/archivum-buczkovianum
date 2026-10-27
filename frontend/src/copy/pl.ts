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
  page: { one: "strona", few: "strony", many: "stron" },
} as const satisfies Record<string, PluralForms>;

/** A section header's counter (R-09): "3", or "2 z 24" when the section is a preview. */
export function previewCount(shown: number, total: number): string {
  return shown < total ? `${String(shown)} z ${String(total)}` : String(total);
}

/** A fragment's number in its document, with two digits: "Fragment 01" (R-10). */
export function fragmentLabel(number: number): string {
  return `Fragment ${String(number).padStart(2, "0")}`;
}

export const copy = {
  siteName: "Archivum Buczkovianum",
  /** Header, main navigation and footer (R-07). */
  layout: {
    headerSubtitle: "Archiwum literackie",
    footerSubtitle: "Archiwum literackie Leopolda Buczkowskiego",
    about: "O archiwum",
    navLabel: "Menu główne",
    nav: {
      home: "Strona główna",
      works: "Utwory",
      typescripts: "Maszynopisy",
      tags: "Tagi",
    },
    // PLACEHOLDER: the owner supplies the exact text (plan D7).
    fundingNote: "[Informacja o finansowaniu projektu — tekst do uzupełnienia]",
  },
  /** The archive covers one author, so every work card names him (plan D22). */
  author: "Leopold Buczkowski",
  /** The work card (US-RA-01 AC3), on the works list and the home page. */
  workCard: {
    /** The placeholder board for a work without a cover (plan D25, design/rules.md). */
    coverPlaceholder: "[Okładka]",
  },
  /** The home page (US-RA-01). */
  home: {
    works: "Utwory",
    worksDescription: "Wszystkie utwory w archiwum, w kolejności wydania",
    loading: "Wczytuję stronę…",
    error: "Nie udało się wczytać strony. Spróbuj ponownie później.",
  },
  /** The About page (US-RA-13). */
  about: {
    title: "O archiwum",
    project: "O projekcie",
    team: "Zespół",
    /** Team groups, keyed by `TeamMember.Group` in the API. */
    groups: {
      leadership: "Kierownictwo projektu",
      team: "Członkowie zespołu",
      site: "Opracowanie serwisu",
    },
    loading: "Wczytuję stronę…",
    error: "Nie udało się wczytać strony. Spróbuj ponownie później.",
  },
  /** The works list (US-RA-18). */
  works: {
    title: "Utwory",
    description: "Wszystkie utwory Leopolda Buczkowskiego w archiwum, w kolejności wydania.",
    all: "Wszystkie utwory",
    allDescription: "W kolejności wydania",
    loading: "Wczytuję utwory…",
    error: "Nie udało się wczytać utworów. Spróbuj ponownie później.",
  },
  /** The typescripts list (US-RA-19). */
  typescripts: {
    title: "Maszynopisy",
    description: "Jednostki archiwalne z maszynopisami utworów, pogrupowane według utworu.",
    loading: "Wczytuję maszynopisy…",
    error: "Nie udało się wczytać maszynopisów. Spróbuj ponownie później.",
  },
  /** The tag cloud (US-RA-01 AC4), on the tags list and the home page. */
  tagCloud: {
    title: "Chmura tagów",
    description: "Wielkość nazwy odpowiada liczbie wystąpień, w pięciu stopniach",
  },
  /** The tags list (US-RA-20). */
  tags: {
    title: "Tagi",
    description: "Motywy łączące fragmenty i zapiski z różnych utworów.",
    all: "Wszystkie tagi",
    allDescription: "Alfabetycznie",
    loading: "Wczytuję tagi…",
    error: "Nie udało się wczytać tagów. Spróbuj ponownie później.",
  },
  /** The typescript page (US-RA-08). */
  typescript: {
    type: "Maszynopis",
    work: "Utwór",
    workTypescripts: "Maszynopisy utworu",
    scan: "Skan maszynopisu",
    fragments: "Fragmenty z maszynopisu",
    fragmentsDescription: "W kolejności stron",
    allFragments: (count: number) => `Wszystkie fragmenty (${String(count)})`,
    loading: "Wczytuję maszynopis…",
    error: "Nie udało się wczytać maszynopisu. Spróbuj ponownie później.",
  },
  /** The work page (US-RA-04). */
  work: {
    type: "Utwór",
    editions: "Wydania",
    firstEdition: "pierwsze wydanie",
    fragments: "Fragmenty maszynopisu",
    fragmentsDescription: "Wybór redakcji, w kolejności tekstu",
    typescripts: "Maszynopisy",
    notes: "Zapiski",
    notesDescription: "Zapiski autora związane z utworem",
    loading: "Wczytuję utwór…",
    error: "Nie udało się wczytać utworu. Spróbuj ponownie później.",
  },
  /** The fragment card (R-10) and the note card (US-RA-04 AC3). */
  card: {
    /** The source type chip, keyed by the API's `source_type`. */
    types: {
      typescript: "Maszynopis",
      note: "Zapisek",
      secondary_text: "Tekst sekundarny",
      material: "Materiał kontekstowy",
    },
    scan: (page: number) => `Skan · strona ${String(page)}`,
    /** The placeholder board for a note without an image (design/rules.md). */
    notePlaceholder: "[Skan zapisku]",
  },
  /** The reader (R-11). */
  reader: {
    views: "Widok",
    scan: "Skan",
    text: "Transkrypcja",
    page: (number: number, count: number) => `Skan · strona ${String(number)} z ${String(count)}`,
    scanError: "Nie udało się wczytać skanu.",
    loading: "Wczytuję tekst…",
    error: "Nie udało się wczytać tekstu. Spróbuj ponownie później.",
  },
  /** The contextual materials block (R-08). */
  materials: {
    title: "Materiały kontekstowe",
    description: "Opracowania i materiały wizualne związane z utworem",
    texts: "Teksty sekundarne",
    visuals: "Materiały wizualne",
  },
  /** The search field in the header and on the search page (US-RA-14). */
  search: {
    title: "Wyszukiwanie",
    /** The header field's text, the mobile icon's name and the fields' accessible name. */
    label: "Szukaj w archiwum",
    placeholder: "Tytuł, opis, transkrypcja lub tag",
    submit: "Szukaj",
    clear: "Wyczyść",
    scope: "Przeszukiwane: tytuły, opisy, transkrypcje i tagi",
    hint: "Dokładna fraza: użyj cudzysłowu, np. „dezerter w stodole”",
    /** The list of suggestions under both fields (US-RA-17), and each suggestion's type. */
    suggestions: "Podpowiedzi",
    suggestionTypes: { work: "Utwór", tag: "Tag" },
  },
  notFound: {
    title: "Nie znaleziono strony",
    body: "Pod tym adresem nie ma żadnej strony.",
    backHome: "Wróć na stronę główną",
  },
} as const;
