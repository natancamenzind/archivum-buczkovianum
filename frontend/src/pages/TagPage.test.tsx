import { screen, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type TagData = components["schemas"]["TagPage"];
type Fragment = components["schemas"]["FragmentCard"];

const TAG_URL = "*/api/tags/dezerter/";
const SCAN_URL = "*/media/scans/wertepy.pdf";

const FRAGMENT: Fragment = {
  id: 5,
  url: "/typescripts/1?fragment=5",
  source_type: "typescript",
  work: "Wertepy",
  number: 1,
  location: "rozdział I",
  quote: "Dezerter stał w stodole.",
  scan: "/media/scans/wertepy.pdf",
  start_page: 3,
  shelfmark: "ML, sygn. 1618.0009",
  description: "Fragment oznaczony tagiem „Dezerter”.",
  tags: [{ slug: "dezerter", title: "Dezerter" }],
};

const TAG: TagData = {
  slug: "dezerter",
  title: "Dezerter",
  description: "<p>Postać dezertera w prozie Buczkowskiego.</p>",
  occurrences: 4,
  works: [
    { slug: "wertepy", title: "Wertepy", year: 1947, fragment_count: 2 },
    { slug: "czarny-potok", title: "Czarny potok", year: 1954, fragment_count: 1 },
    { slug: "pierwsza-swietosc", title: "Pierwsza świętość", year: null, fragment_count: 0 },
  ],
  fragments: [
    FRAGMENT,
    {
      ...FRAGMENT,
      id: 9,
      url: "/notes/3?fragment=9",
      source_type: "note",
      work: "Czarny potok",
      number: 2,
      location: "",
      quote: "Uciekł z wojska.",
      scan: "",
      start_page: null,
      shelfmark: "",
      description: "",
      tags: [],
    },
  ],
  notes: [
    {
      url: "/notes/3",
      title: "Notes 18 · karta 4",
      shelfmark: "ML, sygn. 1678.0104",
      description: "<p>Notatka o postaci dezertera.</p>",
      image: "",
      image_alt: "",
      tags: [{ slug: "dezerter", title: "Dezerter" }],
    },
  ],
  related: [
    { slug: "las", title: "Las" },
    { slug: "wojna", title: "Wojna" },
  ],
  materials: {
    texts: [
      {
        url: "/secondary-texts/4",
        author: "Jan Kowalski",
        title: "O dezerterach",
        publication: "Czytelnik, Warszawa 1948, s. 3",
      },
    ],
    visuals: [],
  },
};

function mockPage(tag: Partial<TagData> = {}) {
  server.use(
    http.get(TAG_URL, () => HttpResponse.json({ ...TAG, ...tag })),
    // pdf.js keeps the scan loading; jsdom cannot draw it anyway.
    http.get(SCAN_URL, async () => {
      await delay("infinite");
      return new HttpResponse(null);
    }),
  );
}

async function renderPage() {
  const result = renderRoute("/tags/dezerter");
  await screen.findByRole("heading", { level: 1, name: "Dezerter" });
  return result;
}

function hero(): HTMLElement {
  const title = screen.getByRole("heading", { level: 1 });
  const header = title.closest<HTMLElement>("[data-slot=page-header]");
  if (header === null) {
    throw new Error("The title is not inside the hero.");
  }
  return header;
}

/** The card a section heading opens. */
function card(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name });
  const element = heading.closest<HTMLElement>("[data-slot=card]");
  if (element === null) {
    throw new Error(`'${name}' is not inside a card.`);
  }
  return element;
}

/** The block a column header heads: the header's parent. */
function column(name: string, level: 2 | 3 = 3): HTMLElement {
  const heading = screen.getByRole("heading", { level, name });
  const element = heading.parentElement?.parentElement;
  if (element == null) {
    throw new Error(`'${name}' heads no block.`);
  }
  return element;
}

describe("TagPage", () => {
  it("US-RA-07 AC1: the hero shows occurrences in works, title and description; Tagi is active", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(within(hero()).getByText("Tag · 4 wystąpienia w 3 utworach")).toBeVisible();
    expect(within(hero()).getByText("Postać dezertera w prozie Buczkowskiego.")).toBeVisible();
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).getByRole("link", { name: "Tagi" })).toHaveAttribute("aria-current", "page");
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    [1, 1, "Tag · 1 wystąpienie w 1 utworze"],
    [5, 2, "Tag · 5 wystąpień w 2 utworach"],
    [22, 12, "Tag · 22 wystąpienia w 12 utworach"],
    // Only on items related to no published work.
    [3, 0, "Tag · 3 wystąpienia"],
    [0, 0, "Tag · 0 wystąpień"],
  ])("US-RA-07 AC1: %i occurrences in %i works read '%s'", async (occurrences, works, label) => {
    mockPage({
      occurrences,
      works: Array.from({ length: works }, (_, index) => ({
        slug: `utwor-${String(index)}`,
        title: `Utwór ${String(index)}`,
        year: 1947,
        fragment_count: 0,
      })),
    });

    await renderPage();

    expect(within(hero()).getByText(label)).toBeVisible();
  });

  it("US-RA-07 AC1: a tag without a description shows none (R-02)", async () => {
    mockPage({ description: "" });

    await renderPage();

    expect(hero().querySelectorAll("p")).toHaveLength(1);
  });

  it("US-RA-07 AC2: 'Utwory' lists the works with year, title and tagged fragment count", async () => {
    mockPage();

    const { container } = await renderPage();

    const works = column("Utwory");
    expect(within(works).getByText("3")).toBeVisible();
    const links = within(works).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "1947Wertepy2 fragmenty z tagiem",
      "1954Czarny potok1 fragment z tagiem",
      // No year without editions, no count without tagged fragments (R-02).
      "Pierwsza świętość",
    ]);
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/works/wertepy",
      "/works/czarny-potok",
      "/works/pierwsza-swietosc",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-07 AC3: 'Fragmenty z tagiem' shows every fragment as a fragment card", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Fragmenty z tagiem");
    expect(within(fragments).getByText("2")).toBeVisible();
    expect(within(fragments).getByText("W kolejności wydania utworów")).toBeVisible();
    const [first, second] = within(fragments).getAllByRole("article");
    if (first === undefined || second === undefined) {
      throw new Error("Expected two fragment cards.");
    }
    expect(
      within(first).getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/1?fragment=5");
    expect(within(first).getByText("Maszynopis")).toBeVisible();
    expect(within(first).getByRole("img", { name: "Skan · strona 3" })).toBeVisible();
    expect(within(first).getByText("ML, sygn. 1618.0009")).toBeVisible();
    expect(
      within(second).getByRole("link", { name: "Czarny potok · Fragment 02" }),
    ).toHaveAttribute("href", "/notes/3?fragment=9");
    expect(within(second).getByText("Zapisek")).toBeVisible();
    // Every fragment, not a preview (R-09): no "all" link.
    expect(
      within(fragments).queryByRole("link", { name: /Wszystkie fragmenty/ }),
    ).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-07 AC3: 'Zapiski z tagiem' shows the notes as note cards", async () => {
    mockPage();

    const { container } = await renderPage();

    const notes = card("Zapiski z tagiem");
    expect(within(notes).getByText("1")).toBeVisible();
    const [note] = within(notes).getAllByRole("article");
    if (note === undefined) {
      throw new Error("Expected a note card.");
    }
    expect(within(note).getByRole("link", { name: "Notes 18 · karta 4" })).toHaveAttribute(
      "href",
      "/notes/3",
    );
    expect(within(note).getByText("ML, sygn. 1678.0104")).toBeVisible();
    expect(within(note).getByText("Notatka o postaci dezertera.")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-07 AC4: 'Powiązane tagi' links each related tag to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const related = column("Powiązane tagi");
    expect(within(related).getByText("2")).toBeVisible();
    expect(
      within(related)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(["/tags/las", "/tags/wojna"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-07 AC6: the contextual materials with the tag", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(screen.getByRole("heading", { level: 2, name: "Materiały kontekstowe" })).toBeVisible();
    expect(screen.getByText("Opracowania i materiały wizualne z tym tagiem")).toBeVisible();
    expect(screen.getByRole("link", { name: /Jan Kowalski, O dezerterach/ })).toHaveAttribute(
      "href",
      "/secondary-texts/4",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a tag with nothing but its hero renders no blocks", async () => {
    mockPage({
      occurrences: 0,
      works: [],
      fragments: [],
      notes: [],
      related: [],
      materials: { texts: [], visuals: [] },
    });

    const { container } = await renderPage();

    expect(screen.queryAllByRole("heading", { level: 2 })).toEqual([]);
    expect(screen.queryAllByRole("heading", { level: 3 })).toEqual([]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-12: with an empty main column, the side columns are headed by h2", async () => {
    mockPage({ fragments: [], notes: [], materials: { texts: [], visuals: [] } });

    const { container } = await renderPage();

    expect(within(column("Utwory", 2)).getAllByRole("link")).toHaveLength(3);
    expect(within(column("Powiązane tagi", 2)).getAllByRole("link")).toHaveLength(2);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-06: a tag the API does not find shows the not-found page", async () => {
    server.use(http.get(TAG_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/tags/dezerter");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(TAG_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/tags/dezerter");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję tag…");
    expect(
      await screen.findByText("Nie udało się wczytać tagu. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
