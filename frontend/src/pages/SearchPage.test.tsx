import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type Results = components["schemas"]["SearchPage"];

const SEARCH_URL = "*/api/search/";

const EMPTY: Results = {
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
    renderRoute("/search?q=dezerter");

    fireEvent.change(searchBox(), { target: { value: "   " } });
    fireEvent.submit(searchForm());

    expect(searchBox()).toHaveValue("");
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
    const headings = screen.getAllByRole("heading", { level: 2 }).slice(1);
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
    server.use(
      http.get(SEARCH_URL, async () => {
        await delay("infinite");
        return HttpResponse.json(RESULTS);
      }),
    );

    const { container } = renderRoute("/search?q=dezerter");

    expect(await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…")).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Sortuj" })).toBeDisabled();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-15: the loading skeleton shows only after 300 ms", async () => {
    server.use(
      http.get(SEARCH_URL, async () => {
        await delay("infinite");
        return HttpResponse.json(RESULTS);
      }),
    );
    const skeleton = "[aria-hidden=true][data-slot=card]";

    const { container } = renderRoute("/search?q=dezerter");

    await screen.findByText("Przeszukuję utwory, fragmenty, zapiski i tagi…");
    expect(container.querySelector(skeleton)).toBeNull();
    await waitFor(() => {
      expect(container.querySelector(skeleton)).not.toBeNull();
    });
  });

  it("US-RA-15: a failed search says so", async () => {
    server.use(http.get(SEARCH_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/search?q=dezerter");

    expect(
      await screen.findByText("Nie udało się wczytać wyników. Spróbuj ponownie później."),
    ).toBeVisible();
  });

  it("US-RA-15: without a query, nothing is searched", () => {
    const requests = mockSearch();

    renderRoute("/search");

    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(requests).toEqual([]);
  });
});
