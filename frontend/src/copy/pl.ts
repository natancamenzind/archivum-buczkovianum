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
  /** "w 1 utworze", "w 2 utworach". */
  workLocative: { one: "utworze", few: "utworach", many: "utworach" },
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
  /** Above an entity page that staff preview as a draft (US-WR-13 AC2). */
  draftBanner: "Szkic — niewidoczny publicznie",
  /** The work card (US-RA-01 AC3), on the works list and the home page. */
  workCard: {
    /** The placeholder board for a work without a cover (plan D25, design/rules.md). */
    coverPlaceholder: "[Okładka]",
  },
  /** The home page (US-RA-01). */
  home: {
    works: "Utwory",
    worksDescription: "Wszystkie utwory w archiwum, w kolejności wydania",
    /** The featured fragment (US-RA-02). */
    featured: "Wybrany fragment",
    featuredDescription: "Wybór redakcji",
    workFragments: (work: string, count: number) =>
      `Wszystkie fragmenty „${work}” (${String(count)})`,
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
  /** The secondary text page (US-RA-10). */
  secondaryText: {
    /** The type line's kind, keyed by the API's `kind`. */
    kinds: {
      letter: "List",
      review: "Recenzja",
      study: "Opracowanie",
      recording: "Nagranie",
      other: "Tekst sekundarny",
    },
    works: "Powiązane utwory",
    text: "Transkrypcja",
    fragments: "Powiązane fragmenty",
    tags: "Powiązane tagi",
    loading: "Wczytuję tekst sekundarny…",
    error: "Nie udało się wczytać tekstu sekundarnego. Spróbuj ponownie później.",
  },
  /** The note page (US-RA-11). */
  note: {
    label: "Zapisek",
    works: "Powiązane utwory",
    fragments: "Powiązane fragmenty",
    tags: "Powiązane tagi",
    loading: "Wczytuję zapisek…",
    error: "Nie udało się wczytać zapisku. Spróbuj ponownie później.",
  },
  /** The contextual material page (US-RA-12). */
  material: {
    /** The type line's kind, keyed by the API's `content.kind`. */
    kinds: {
      image: "Materiał wizualny",
      document: "Dokument",
      external_media: "Nagranie",
      ocr_text: "Skan z transkrypcją",
      plain_text: "Tekst lity",
    },
    works: "Powiązane utwory",
    fragments: "Powiązane fragmenty",
    tags: "Powiązane tagi",
    loading: "Wczytuję materiał kontekstowy…",
    error: "Nie udało się wczytać materiału kontekstowego. Spróbuj ponownie później.",
  },
  /** The content of a note or contextual material, by its kind (US-RA-11 AC3). */
  content: {
    text: "Transkrypcja",
    page: (number: number, count: number) => `Strona ${String(number)} z ${String(count)}`,
    loading: "Wczytuję dokument…",
    download: "Pobierz plik",
    player: "Odtwarzacz nagrania",
    link: "Otwórz nagranie",
  },
  /** The tag page (US-RA-07). */
  tag: {
    /** The hero's type line: "Tag · 4 wystąpienia w 2 utworach". */
    label: (occurrences: number, works: number) => {
      const count = `Tag · ${formatCount(occurrences, nouns.occurrence)}`;
      return works > 0 ? `${count} w ${formatCount(works, nouns.workLocative)}` : count;
    },
    works: "Utwory",
    /** A work's line in the context column: "2 fragmenty z tagiem". */
    workFragments: (count: number) => `${formatCount(count, nouns.fragment)} z tagiem`,
    fragments: "Fragmenty z tagiem",
    fragmentsDescription: "W kolejności wydania utworów",
    notes: "Zapiski z tagiem",
    related: "Powiązane tagi",
    materialsDescription: "Opracowania i materiały wizualne z tym tagiem",
    loading: "Wczytuję tag…",
    error: "Nie udało się wczytać tagu. Spróbuj ponownie później.",
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
  /** The search results (US-RA-15). */
  searchResults: {
    /** An empty query lists everything in the tab and filters (US-RA-16 AC5). */
    title: (query: string) => (query === "" ? "Wszystkie wyniki" : `Wyniki dla „${query}”`),
    /** `tab` is the selected tab's name; null for "Wszystko". */
    total: (count: number, tab: string | null) =>
      tab === null
        ? `${formatCount(count, nouns.result)} we wszystkich kategoriach`
        : `${formatCount(count, nouns.result)} w kategorii „${tab}”`,
    loading: "Przeszukuję utwory, fragmenty, zapiski i tagi…",
    error: "Nie udało się wczytać wyników. Spróbuj ponownie później.",
    sort: "Sortuj",
    /** Keyed by the API's `sort`. */
    sorts: { relevance: "Trafność", title: "Tytuł" },
    /** The groups in their order (US-RA-15 AC3), keyed by the API's group names. */
    groups: {
      works: "Utwory",
      tags: "Tagi",
      fragments: "Fragmenty",
      notes: "Zapiski",
      typescripts: "Maszynopisy",
      secondary_texts: "Teksty sekundarne",
      materials: "Materiały kontekstowe",
    },
    /** Each result's type (R-04), keyed by the API's group names. */
    types: {
      works: "Utwór",
      tags: "Tag",
      notes: "Zapisek",
      typescripts: "Maszynopis",
      secondary_texts: "Tekst sekundarny",
      materials: "Materiał kontekstowy",
    },
    openTag: "Otwórz tag",
    noResults: (query: string) => (query === "" ? "Brak wyników" : `Brak wyników dla „${query}”`),
    noResultsHint:
      "Sprawdź pisownię albo skróć frazę. Wyszukiwanie obejmuje tytuły, opisy, transkrypcje i tagi.",
    /** With an empty query, only the tab and filters can be changed. */
    noResultsFilteredHint: "Wybierz inną kategorię albo wyczyść filtry.",
    suggestedTags: "Śladami motywów",
    suggestedTagsDescription:
      "Tagi łączą fragmenty z różnych utworów. Otwórz tag, by podążyć za motywem w całym archiwum.",
  },
  /** The search tabs and filters (US-RA-16). */
  searchFilters: {
    tabsLabel: "Kategorie wyników",
    /** Keyed by the API's `tab`. */
    tabs: {
      all: "Wszystko",
      works: "Utwory",
      fragments: "Fragmenty",
      notes: "Zapiski",
      tags: "Tagi",
    },
    /** A count that is still loading (design/rules.md, Stany ładowania). */
    pending: "–",
    title: "Filtry",
    open: (count: number) => `Filtry (${String(count)})`,
    close: "Zamknij filtry",
    work: "Utwór",
    availability: "Dostępność",
    hasScan: "Ze skanem",
    hasText: "Z transkrypcją",
    period: "Okres",
    allYears: "Wszystkie lata",
    decade: (decade: number, count: number) =>
      `${String(decade)}–${String(decade + 9)} (${String(count)})`,
    clear: "Wyczyść",
    /** `count` is the filtered total, or `pending` while it loads. */
    show: (count: string) => `Pokaż wyniki (${count})`,
  },
  notFound: {
    title: "Nie znaleziono strony",
    body: "Pod tym adresem nie ma żadnej strony.",
    backHome: "Wróć na stronę główną",
  },
} as const;
