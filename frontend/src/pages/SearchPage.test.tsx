import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type Results = components["schemas"]["SearchPage"];

const SEARCH_URL = "*/api/search/";

const EMPTY: Results = {
  facets: {
    tabs: { all: 0, works: 0, fragments: 0, notes: 0, tags: 0 },
    works: [],
    decades: [],
    has_scan: 0,
    has_text: 0,
  },
  total: 0,
  works: [],
  tags: [],
  fragments: [],
  notes: [],
  typescripts: [],
  secondary_texts: [],
  materials: [],
  suggested_tags: [],
};

const RESULTS: Results = {
  facets: {
    tabs: { all: 8, works: 1, fragments: 1, notes: 1, tags: 1 },
    works: [
      { id: 1, title: "Wertepy", count: 5 },
      { id: 2, title: "Czarny potok", count: 2 },
    ],
    decades: [
      { decade: 1940, count: 5 },
      { decade: 1950, count: 2 },
    ],
    has_scan: 3,
    has_text: 0,
  },
  total: 8,
  works: [{ url: "/works/wertepy", title: "Wertepy", genre: "powieść", year: 1947, fragments: 2 }],
  tags: [
    {
      url: "/tags/dezerter",
      title: "Dezerter",
      occurrences: 4,
      snippet: "Postać <mark>dezertera</mark> w prozie.",
    },
  ],
  fragments: [
    {
      id: 7,
      url: "/typescripts/1?fragment=7",
      source_type: "typescript",
      work: "Wertepy",
      number: 1,
      location: "rozdział I",
      quote: "Szedł dezerter przez las.",
      scan: "",
      start_page: null,
      shelfmark: "ML, sygn. 1618.0009",
      description: "",
      tags: [{ slug: "dezerter", title: "Dezerter" }],
    },
  ],
  notes: [
    {
      url: "/notes/3?q=dezerterze",
      title: "Notes 18",
      shelfmark: "ML, sygn. 1678.0104",
      snippet: "Notatka o <mark>dezerterze</mark>.",
    },
  ],
  typescripts: [
    {
      url: "/typescripts/1?q=dezerter",
      title: "Maszynopis Wertepów",
      shelfmark: "ML, sygn. 1618",
      snippet: "Szedł <mark>dezerter</mark> przez las.",
    },
  ],
  secondary_texts: [
    {
      url: "/secondary-texts/4",
      title: "Recenzja",
      shelfmark: "",
      snippet: "O &lt;dezerterze&gt;.",
    },
  ],
  materials: [
    {
      url: "/materials/8?q=Dezerter",
      title: "Dezerter na zdjęciu",
      shelfmark: "",
      snippet: "<mark>Dezerter</mark> w lesie.",
    },
  ],
  suggested_tags: [],
};

/** Answers every search with `results`; returns the URLs asked for. */
function mockSearch(results: Results = RESULTS): URL[] {
  const requests: URL[] = [];
  server.use(
    http.get(SEARCH_URL, ({ request }) => {
      requests.push(new URL(request.url));
      return HttpResponse.json(results);
    }),
  );
  return requests;
}

/** A search that never answers, so the page stays loading. */
function mockPendingSearch(): void {
  server.use(
    http.get(SEARCH_URL, async () => {
      await delay("infinite");
      return HttpResponse.json(RESULTS);
    }),
  );
}

function group(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name });
  const panel = heading.closest<HTMLElement>("[data-slot=card]");
  if (panel === null) {
    throw new Error(`No panel for ${name}.`);
  }
  return panel;
}

function searchForm(): HTMLElement {
  return screen.getByRole("search", { name: "Wyszukiwanie" });
}

function searchBox(): HTMLInputElement {
  return within(searchForm()).getByRole<HTMLInputElement>("combobox", {
    name: "Szukaj w archiwum",
  });
}

describe("SearchPage", () => {
  beforeEach(() => {
    mockSearch(EMPTY);
  });

  it("US-RA-14 AC1: the search page shows the submitted query in its field", async () => {
    const { container } = renderRoute("/search?q=dezerter+w+stodole");

    expect(screen.getByRole("heading", { level: 1, name: "Wyszukiwanie" })).toBeInTheDocument();
    expect(searchBox()).toHaveValue("dezerter w stodole");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-14 AC1: submitting the page's field searches for the new query", () => {
    renderRoute("/search?q=dezerter");

    fireEvent.change(searchBox(), { target: { value: "  potok " } });
    fireEvent.click(within(searchForm()).getByRole("button", { name: "Szukaj" }));

    expect(searchBox()).toHaveValue("potok");
  });

  it("US-RA-14 AC1: submitting keeps the focus in the field", () => {
    renderRoute("/search?q=dezerter");

    searchBox().focus();
    fireEvent.change(searchBox(), { target: { value: "potok" } });
    fireEvent.submit(searchForm());

    expect(searchBox()).toHaveValue("potok");
    expect(searchBox()).toHaveFocus();
  });

  it("US-RA-14 AC2: a quoted phrase survives the trip through the URL", () => {
    renderRoute("/search");
    const phrase = "„dezerter w stodole” & ł#?+";

    fireEvent.change(searchBox(), { target: { value: phrase } });
    fireEvent.submit(searchForm());

    // The field shows the query decoded from the new URL.
    expect(searchBox()).toHaveValue(phrase);
  });

  it("US-RA-14 AC1: the empty field shows the placeholder and no clear button", async () => {
    const { container } = renderRoute("/search");

    expect(searchBox()).toHaveValue("");
    expect(searchBox()).toHaveAttribute("placeholder", "Tytuł, opis, transkrypcja lub tag");
    expect(within(searchForm()).queryByRole("button", { name: "Wyczyść" })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-14 AC1: 'Wyczyść' empties the field and keeps the focus in it", () => {
    renderRoute("/search?q=dezerter");

    fireEvent.click(within(searchForm()).getByRole("button", { name: "Wyczyść" }));

    expect(searchBox()).toHaveValue("");
    expect(searchBox()).toHaveFocus();
    expect(within(searchForm()).queryByRole("button", { name: "Wyczyść" })).toBeNull();
  });

  it("US-RA-14 AC1: a blank query opens the search page without one", () => {
    const { router } = renderRoute("/search?q=dezerter&sort=title");

    fireEvent.change(searchBox(), { target: { value: "   " } });
    fireEvent.submit(searchForm());

    expect(searchBox()).toHaveValue("");
    expect(router.state.location.search).toBe("");
  });

  it("US-RA-14 AC2: under the field, what is searched and the exact-phrase hint", async () => {
    const { container } = renderRoute("/search");

    expect(
      screen.getByText("Przeszukiwane: tytuły, opisy, transkrypcje i tagi"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Dokładna fraza: użyj cudzysłowu, np. „dezerter w stodole”"),
    ).toBeInTheDocument();
    expect(searchBox()).toHaveAccessibleDescription(
      "Przeszukiwane: tytuły, opisy, transkrypcje i tagi Dokładna fraza: użyj cudzysłowu, np. „dezerter w stodole”",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-12: the field and its buttons show a focus outline", () => {
    renderRoute("/search?q=dezerter");

    expect(searchForm()).toHaveClass("has-[input:focus-visible]:outline-2");
    for (const name of ["Wyczyść", "Szukaj"]) {
      expect(within(searchForm()).getByRole("button", { name })).toHaveClass(
        "focus-visible:outline-2",
        "focus-visible:outline-ring",
      );
    }
  });

  it("US-RA-15 AC2: the header shows the query and the total", async () => {
    const requests = mockSearch();

    const { container } = renderRoute("/search?q=dezerter");

    expect(await screen.findByText("8 wyników we wszystkich kategoriach")).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "Wyniki dla „dezerter”" })).toBeVisible();
    expect(requests[0]?.searchParams.get("q")).toBe("dezerter");
    expect(requests[0]?.searchParams.get("sort")).toBe("relevance");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15 AC3: results are grouped by type, each group with its count, in order", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    // After the filters' heading and the results' title.
    const headings = screen.getAllByRole("heading", { level: 2 }).slice(2);
    expect(headings.map((heading) => heading.textContent)).toEqual([
      "Utwory",
      "Tagi",
      "Fragmenty",
      "Zapiski",
      "Maszynopisy",
      "Teksty sekundarne",
      "Materiały kontekstowe",
    ]);
    expect(within(group("Fragmenty")).getByText("1")).toBeVisible();
  });

  it("US-RA-15 AC3: groups without results are left out", async () => {
    mockSearch({
      ...RESULTS,
      total: 1,
      tags: [],
      fragments: [],
      notes: [],
      typescripts: [],
      secondary_texts: [],
      materials: [],
    });

    renderRoute("/search?q=wertepy");

    await screen.findByText("1 wynik we wszystkich kategoriach");
    expect(screen.queryByRole("heading", { level: 2, name: "Tagi" })).toBeNull();
    expect(screen.getByRole("heading", { level: 2, name: "Utwory" })).toBeVisible();
  });

  it("US-RA-15 AC4: the reader can sort by title, kept in the URL", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?q=dezerter");

    const sort = await screen.findByRole<HTMLSelectElement>("combobox", { name: "Sortuj" });
    await screen.findByText("8 wyników we wszystkich kategoriach");
    expect(sort).toHaveValue("relevance");
    fireEvent.change(sort, { target: { value: "title" } });

    expect(await screen.findByRole("combobox", { name: "Sortuj" })).toHaveValue("title");
    expect(router.state.location.search).toBe("?q=dezerter&sort=title");
    await screen.findByText("8 wyników we wszystkich kategoriach");
    expect(requests.at(-1)?.searchParams.get("sort")).toBe("title");
  });

  it("US-RA-15 AC4: sorting back by relevance drops the sort from the URL", async () => {
    mockSearch();

    const { router } = renderRoute("/search?q=dezerter&sort=title");

    const sort = await screen.findByRole("combobox", { name: "Sortuj" });
    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.change(sort, { target: { value: "relevance" } });

    expect(router.state.location.search).toBe("?q=dezerter");
  });

  it("US-RA-15 AC5: a work shows its type, author, genre, year and matching fragments", async () => {
    mockSearch();

    const { container } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    const link = within(group("Utwory")).getByRole("link");
    expect(link).toHaveAttribute("href", "/works/wertepy");
    expect(link).toHaveTextContent("Wertepy");
    expect(link).toHaveTextContent("Utwór · Leopold Buczkowski · powieść · 1947");
    expect(link).toHaveTextContent("2 fragmenty");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15 AC5: a fragment result is a fragment card", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    const card = within(group("Fragmenty"));
    expect(card.getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" })).toHaveAttribute(
      "href",
      "/typescripts/1?fragment=7",
    );
    expect(card.getByText("Maszynopis")).toBeVisible();
    expect(card.getByText("Szedł dezerter przez las.")).toBeVisible();
  });

  it("US-RA-15 AC5: every result shows its type and links to its page", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    expect(within(group("Zapiski")).getByRole("link")).toHaveTextContent(
      "Zapisek · ML, sygn. 1678.0104",
    );
    expect(within(group("Maszynopisy")).getByRole("link")).toHaveTextContent(
      "Maszynopis · ML, sygn. 1618",
    );
    expect(within(group("Teksty sekundarne")).getByRole("link")).toHaveTextContent(
      "Tekst sekundarny",
    );
    expect(within(group("Materiały kontekstowe")).getByRole("link")).toHaveTextContent(
      "Materiał kontekstowy",
    );
    const tag = within(group("Tagi"));
    expect(tag.getByText("Tag")).toBeVisible();
    expect(tag.getByText("4 wystąpienia")).toBeVisible();
    expect(tag.getByRole("link", { name: "Otwórz tag" })).toHaveAttribute("href", "/tags/dezerter");
  });

  it("US-RA-15 AC6: a text match shows a highlighted snippet and opens at the match", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    const note = within(group("Zapiski")).getByRole("link");
    expect(within(note).getByText("dezerterze", { selector: "mark" })).toBeVisible();
    expect(note).toHaveAttribute("href", "/notes/3?q=dezerterze");
    expect(within(group("Tagi")).getByText("dezertera", { selector: "mark" })).toBeVisible();
    // The snippet is the API's escaped text, never markup of its own.
    expect(within(group("Teksty sekundarne")).getByRole("link")).toHaveTextContent(
      "O <dezerterze>.",
    );
  });

  it("US-RA-15 AC6: a work shows no snippet", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    expect(within(group("Utwory")).queryByText(/dezerter/i)).toBeNull();
  });

  it("US-RA-15 AC8: with no results, the page says so and suggests three tags", async () => {
    mockSearch({
      ...EMPTY,
      suggested_tags: [
        { slug: "dezerter", title: "Dezerter", occurrences: 4 },
        { slug: "wojna", title: "Wojna", occurrences: 3 },
        { slug: "wies", title: "Wieś", occurrences: 2 },
      ],
    });

    const { container } = renderRoute("/search?q=dezerterka");

    expect(
      await screen.findByRole("heading", { level: 2, name: "Brak wyników dla „dezerterka”" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Sprawdź pisownię albo skróć frazę. Wyszukiwanie obejmuje tytuły, opisy, transkrypcje i tagi.",
      ),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 3, name: "Śladami motywów" })).toBeVisible();
    expect(
      screen
        .getAllByRole("link")
        .filter((link) => link.getAttribute("href")?.startsWith("/tags/"))
        .map((link) => link.textContent),
    ).toEqual(["Dezerter", "Wojna", "Wieś"]);
    expect(screen.queryByRole("combobox", { name: "Sortuj" })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15: while results load, the page says it is searching and disables sorting", async () => {
    mockPendingSearch();

    const { container } = renderRoute("/search?q=dezerter");

    expect(await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…")).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Sortuj" })).toBeDisabled();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15: the loading skeleton shows only after 300 ms", async () => {
    mockPendingSearch();
    const skeleton = "[aria-hidden=true][data-slot=card]";

    const { container } = renderRoute("/search?q=dezerter");

    await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…");
    expect(container.querySelector(skeleton)).toBeNull();
    await waitFor(() => {
      expect(container.querySelector(skeleton)).not.toBeNull();
    });
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15: a failed search says so", async () => {
    server.use(http.get(SEARCH_URL, () => new HttpResponse(null, { status: 500 })));

    const { container } = renderRoute("/search?q=dezerter");

    expect(
      await screen.findByText("Nie udało się wczytać wyników. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15: without a query, a tab or a filter, nothing is searched", () => {
    const requests = mockSearch();

    renderRoute("/search?sort=title");

    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(requests).toEqual([]);
  });
});

describe("SearchPage tabs and filters", () => {
  function tabs(): HTMLElement {
    return screen.getByRole("navigation", { name: "Kategorie wyników" });
  }

  function filters(): HTMLElement {
    const heading = screen.getByRole("heading", { level: 2, name: "Filtry" });
    const aside = heading.closest("aside");
    if (aside === null) {
      throw new Error("No filters column.");
    }
    return aside;
  }

  async function openPanel(): Promise<HTMLElement> {
    const button = await screen.findByRole("button", { name: /^Filtry \(\d+\)$/ });
    await waitFor(() => {
      expect(button).toBeEnabled();
    });
    fireEvent.click(button);
    return screen.findByRole("dialog", { name: "Filtry" });
  }

  it("US-RA-16 AC1: the tabs, each with its count, 'Wszystko' by default", async () => {
    mockSearch();

    const { container } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    expect(
      within(tabs())
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Wszystko 8", "Utwory 1", "Fragmenty 1", "Zapiski 1", "Tagi 1"]);
    expect(within(tabs()).getByRole("link", { name: "Wszystko 8" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-16 AC1: a tab shows only its results and keeps the query and filters", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?q=dezerter&work=1");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.click(within(tabs()).getByRole("link", { name: "Utwory 1" }));

    expect(await screen.findByText("8 wyników w kategorii „Utwory”")).toBeVisible();
    expect(router.state.location.search).toBe("?q=dezerter&tab=works&work=1");
    expect(requests.at(-1)?.searchParams.get("tab")).toBe("works");
    expect(within(tabs()).getByRole("link", { name: "Utwory 1" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("US-RA-16 AC1: while results load, the tab counts show a dash", async () => {
    mockPendingSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…");
    expect(within(tabs()).getByRole("link", { name: "Utwory –" })).toBeVisible();
  });

  it("US-RA-16 AC2: every filter value shows its count", async () => {
    mockSearch();

    const { container } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    const column = within(filters());
    expect(
      column.getByRole("heading", { level: 3, name: "Utwór" }).parentElement,
    ).toHaveTextContent("Utwór2");
    expect(column.getByRole("checkbox", { name: "Wertepy 5" })).not.toBeChecked();
    expect(column.getByRole("checkbox", { name: "Czarny potok 2" })).not.toBeChecked();
    expect(column.getByRole("checkbox", { name: "Ze skanem 3" })).not.toBeChecked();
    expect(column.getByRole("checkbox", { name: "Z transkrypcją 0" })).not.toBeChecked();
    const period = column.getByRole<HTMLSelectElement>("combobox", { name: "Okres" });
    expect(period).toHaveValue("");
    expect([...period.options].map((option) => option.text)).toEqual([
      "Wszystkie lata",
      "1940–1949 (5)",
      "1950–1959 (2)",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-16 AC2: choosing works filters the results by them", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Wertepy 5" }));
    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Czarny potok 2" }));
    await screen.findByText("8 wyników we wszystkich kategoriach");

    expect(router.state.location.search).toBe("?q=dezerter&work=1&work=2");
    expect(requests.at(-1)?.searchParams.getAll("work")).toEqual(["1", "2"]);
    expect(within(filters()).getByRole("checkbox", { name: "Wertepy 5" })).toBeChecked();

    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Wertepy 5" }));
    expect(router.state.location.search).toBe("?q=dezerter&work=2");
    await screen.findByText("8 wyników we wszystkich kategoriach");
  });

  it("US-RA-16 AC2: choosing a decade filters by it; 'Wszystkie lata' clears it", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.change(within(filters()).getByRole("combobox", { name: "Okres" }), {
      target: { value: "1950" },
    });
    await screen.findByText("8 wyników we wszystkich kategoriach");

    expect(router.state.location.search).toBe("?q=dezerter&decade=1950");
    expect(requests.at(-1)?.searchParams.get("decade")).toBe("1950");
    fireEvent.change(within(filters()).getByRole("combobox", { name: "Okres" }), {
      target: { value: "" },
    });
    expect(router.state.location.search).toBe("?q=dezerter");
    await screen.findByText("8 wyników we wszystkich kategoriach");
  });

  it("US-RA-16 AC2: the availability filters keep results with a scan or a transcription", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Ze skanem 3" }));
    await screen.findByText("8 wyników we wszystkich kategoriach");
    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Z transkrypcją 0" }));
    await screen.findByText("8 wyników we wszystkich kategoriach");

    expect(router.state.location.search).toBe("?q=dezerter&has_scan=1&has_text=1");
    expect(requests.at(-1)?.searchParams.get("has_scan")).toBe("true");
    expect(requests.at(-1)?.searchParams.get("has_text")).toBe("true");
  });

  it("US-RA-16 AC2: while results load, the previous filters stay, dimmed", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    mockPendingSearch();
    fireEvent.click(within(filters()).getByRole("checkbox", { name: "Wertepy 5" }));

    expect(await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…")).toBeVisible();
    expect(filters()).toHaveClass("opacity-40");
    expect(filters()).toHaveAttribute("aria-busy", "true");
    expect(within(filters()).getByRole("checkbox", { name: "Wertepy 5" })).toBeChecked();
  });

  it("US-RA-16 AC3: 'Filtry (n)' opens the filters in a full-screen panel", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter&work=1&has_scan=1");

    const panel = within(await openPanel());
    expect(panel.getByRole("heading", { name: "Filtry" })).toBeVisible();
    expect(panel.getByRole("checkbox", { name: "Wertepy 5" })).toBeChecked();
    expect(panel.getByRole("checkbox", { name: "Ze skanem 3" })).toBeChecked();
    expect(panel.getByRole("button", { name: "Zamknij filtry" })).toBeVisible();
    expect(panel.getByRole("button", { name: "Pokaż wyniki (8)" })).toBeVisible();
    expect(await axeViolations(document.body)).toEqual([]);
  });

  it("US-RA-16 AC3: 'Filtry (n)' counts the selected filter values", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter&work=1&work=2&decade=1940&has_text=1");

    expect(await screen.findByRole("button", { name: "Filtry (4)" })).toBeVisible();
  });

  it("US-RA-16 AC3: 'Pokaż wyniki (n)' shows the filtered count and closes the panel", async () => {
    server.use(
      http.get(SEARCH_URL, ({ request }) => {
        const filtered = new URL(request.url).searchParams.has("work");
        return HttpResponse.json(filtered ? { ...RESULTS, total: 3 } : RESULTS);
      }),
    );

    renderRoute("/search?q=dezerter");

    const panel = within(await openPanel());
    fireEvent.click(panel.getByRole("checkbox", { name: "Wertepy 5" }));
    const show = await panel.findByRole("button", { name: "Pokaż wyniki (3)" });
    fireEvent.click(show);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(screen.getByText("3 wyniki we wszystkich kategoriach")).toBeVisible();
  });

  it("US-RA-16 AC3: 'Wyczyść' clears every filter and keeps the panel open", async () => {
    mockSearch();

    const { router } = renderRoute(
      "/search?q=dezerter&tab=works&work=1&decade=1940&has_scan=1&sort=title",
    );

    const panel = within(await openPanel());
    fireEvent.click(panel.getByRole("button", { name: "Wyczyść" }));

    expect(router.state.location.search).toBe("?q=dezerter&tab=works&sort=title");
    expect(screen.getByRole("dialog", { name: "Filtry" })).toBeVisible();
    expect(await panel.findByRole("checkbox", { name: "Wertepy 5" })).not.toBeChecked();
  });

  it("US-RA-16 AC3: 'Wyczyść' without a query keeps listing everything, panel open", async () => {
    mockSearch();

    const { router } = renderRoute("/search?work=1");

    const panel = within(await openPanel());
    fireEvent.click(panel.getByRole("button", { name: "Wyczyść" }));

    expect(router.state.location.search).toBe("?tab=all");
    expect(await panel.findByRole("button", { name: "Pokaż wyniki (8)" })).toBeVisible();
  });

  it("US-RA-16 AC3: the panel stays open when clearing its filters finds nothing", async () => {
    server.use(
      http.get(SEARCH_URL, ({ request }) => {
        const filtered = new URL(request.url).searchParams.has("work");
        return HttpResponse.json(filtered ? RESULTS : { ...EMPTY, facets: RESULTS.facets });
      }),
    );

    renderRoute("/search?q=dezerter&work=1");

    const panel = within(await openPanel());
    fireEvent.click(panel.getByRole("button", { name: "Wyczyść" }));

    expect(await panel.findByRole("button", { name: "Pokaż wyniki (0)" })).toBeVisible();
    expect(screen.getByRole("dialog", { name: "Filtry" })).toBeVisible();
  });

  it("US-RA-16 AC3: while results load, the panel's filters are dimmed", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    const panel = within(await openPanel());
    mockPendingSearch();
    const scan = panel.getByRole("checkbox", { name: "Ze skanem 3" });
    fireEvent.click(scan);

    expect(await panel.findByRole("button", { name: "Pokaż wyniki (–)" })).toBeVisible();
    const filtersArea = scan.closest("[aria-busy]");
    expect(filtersArea).toHaveAttribute("aria-busy", "true");
    expect(filtersArea).toHaveClass("opacity-40");
  });

  it("US-RA-16 AC3: the close icon closes the panel", async () => {
    mockSearch();

    renderRoute("/search?q=dezerter");

    const panel = within(await openPanel());
    fireEvent.click(panel.getByRole("button", { name: "Zamknij filtry" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });

  it("US-RA-16 AC4: a link restores the tab, filters and sort", async () => {
    const requests = mockSearch();

    renderRoute("/search?q=dezerter&tab=fragments&work=2&decade=1950&has_text=1&sort=title");

    await screen.findByText("8 wyników w kategorii „Fragmenty”");
    const query = requests[0]?.searchParams;
    expect(query?.get("tab")).toBe("fragments");
    expect(query?.getAll("work")).toEqual(["2"]);
    expect(query?.get("decade")).toBe("1950");
    expect(query?.get("has_text")).toBe("true");
    expect(query?.get("sort")).toBe("title");
    expect(within(tabs()).getByRole("link", { name: "Fragmenty 1" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(filters()).getByRole("checkbox", { name: "Czarny potok 2" })).toBeChecked();
    expect(within(filters()).getByRole("combobox", { name: "Okres" })).toHaveValue("1950");
    expect(screen.getByRole("combobox", { name: "Sortuj" })).toHaveValue("title");
  });

  it("US-RA-16 AC4: values that are not valid in a link are ignored", async () => {
    const requests = mockSearch();

    renderRoute("/search?q=dezerter&tab=drafts&work=wertepy&work=0&work=2147483648&decade=1945");

    await screen.findByText("8 wyników we wszystkich kategoriach");
    const query = requests[0]?.searchParams;
    expect(query?.get("tab")).toBe("all");
    expect(query?.getAll("work")).toEqual([]);
    expect(query?.has("decade")).toBe(false);
  });

  it("US-RA-16 AC4: a new search from the page's field keeps the tab, filters and sort", async () => {
    mockSearch();

    const { router } = renderRoute("/search?q=dezerter&tab=works&work=1&sort=title");

    await screen.findByText("8 wyników w kategorii „Utwory”");
    fireEvent.change(searchBox(), { target: { value: "potok" } });
    fireEvent.submit(searchForm());

    expect(router.state.location.search).toBe("?q=potok&tab=works&work=1&sort=title");
    await screen.findByText("8 wyników w kategorii „Utwory”");
  });

  it("US-RA-16 AC4: a search from the header's field starts afresh", async () => {
    mockSearch();

    const { router } = renderRoute("/search?q=dezerter&tab=works&work=1");

    await screen.findByText("8 wyników w kategorii „Utwory”");
    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("combobox"), { target: { value: "potok" } });
    fireEvent.submit(within(header).getByRole("search"));

    expect(router.state.location.search).toBe("?q=potok");
    await screen.findByText("8 wyników we wszystkich kategoriach");
  });

  it("US-RA-16 AC5: an empty query lists everything in the tab and filters by title", async () => {
    const requests = mockSearch();

    const { container } = renderRoute("/search?tab=works&work=1");

    expect(
      await screen.findByRole("heading", { level: 2, name: "Wszystkie wyniki" }),
    ).toBeVisible();
    expect(requests[0]?.searchParams.get("q")).toBe("");
    expect(requests[0]?.searchParams.get("tab")).toBe("works");
    const sort = screen.getByRole("combobox", { name: "Sortuj" });
    expect(sort).toHaveValue("title");
    expect(sort).toBeDisabled();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-16 AC5: without a query, 'Wszystko' lists everything", async () => {
    const requests = mockSearch();

    const { router } = renderRoute("/search?tab=works");

    await screen.findByText("8 wyników w kategorii „Utwory”");
    fireEvent.click(within(tabs()).getByRole("link", { name: "Wszystko 8" }));

    expect(await screen.findByText("8 wyników we wszystkich kategoriach")).toBeVisible();
    expect(router.state.location.search).toBe("?tab=all");
    expect(requests.at(-1)?.searchParams.get("tab")).toBe("all");
  });

  it("US-RA-16 AC5: clearing the field keeps the tab and lists everything in it", async () => {
    mockSearch();

    const { router } = renderRoute("/search?q=dezerter&tab=works");

    await screen.findByText("8 wyników w kategorii „Utwory”");
    fireEvent.click(within(searchForm()).getByRole("button", { name: "Wyczyść" }));
    fireEvent.submit(searchForm());

    expect(router.state.location.search).toBe("?tab=works");
    expect(
      await screen.findByRole("heading", { level: 2, name: "Wszystkie wyniki" }),
    ).toBeVisible();
  });

  it("US-RA-16 AC2: with no filtered results, the tabs and filters stay to change them", async () => {
    mockSearch({ ...EMPTY, facets: RESULTS.facets });

    const { container } = renderRoute("/search?tab=notes&has_scan=1");

    expect(await screen.findByRole("heading", { level: 2, name: "Brak wyników" })).toBeVisible();
    expect(screen.getByText("Wybierz inną kategorię albo wyczyść filtry.")).toBeVisible();
    expect(within(tabs()).getByRole("link", { name: "Zapiski 1" })).toBeVisible();
    expect(within(filters()).getByRole("checkbox", { name: "Ze skanem 3" })).toBeChecked();
    expect(await axeViolations(container)).toEqual([]);
  });
});
