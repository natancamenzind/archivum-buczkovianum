import { screen, waitFor, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { matchRoutes } from "react-router";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { routes } from "@/routes";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type WorkData = components["schemas"]["WorkPage"];
type Fragment = components["schemas"]["FragmentCard"];

const WORK_URL = "*/api/works/wertepy/";
const SCAN_URL = "*/media/scans/wertepy.pdf";

const FRAGMENT: Fragment = {
  id: 5,
  url: "/typescripts/1?fragment=5",
  source_type: "typescript",
  work: "Wertepy",
  number: 1,
  location: "rozdział I",
  quote: "Grzybniak chodził od chałupy do chałupy.",
  scan: "/media/scans/wertepy.pdf",
  start_page: 3,
  shelfmark: "ML, sygn. 1618.0009",
  description: "Grzybniak leczy chorych podczas epidemii tyfusu.",
  tags: [{ slug: "epidemia", title: "Epidemia" }],
};

const WORK: WorkData = {
  slug: "wertepy",
  is_draft: false,
  title: "Wertepy",
  description: "<p>Pierwsza powieść Leopolda Buczkowskiego.</p>",
  year: 1947,
  editions: [
    { year: 1947, publisher: "Gebethner i Wolff", place: "Warszawa" },
    { year: 1957, publisher: "Państwowy Instytut Wydawniczy", place: "Warszawa" },
  ],
  main_typescript: 1,
  fragments: {
    items: [
      FRAGMENT,
      {
        ...FRAGMENT,
        id: 7,
        url: "/typescripts/1?fragment=7",
        number: 3,
        location: "",
        quote: "Dezerter stał w stodole.",
        scan: "",
        start_page: null,
        shelfmark: "",
        description: "",
        tags: [],
      },
    ],
    total: 24,
  },
  typescripts: [
    { id: 1, title: "Pierwsza wersja", shelfmark: "ML, sygn. 1618" },
    { id: 2, title: "Druga wersja", shelfmark: "" },
  ],
  notes: [
    {
      url: "/notes/3",
      title: "Notes 18 · karta 4",
      shelfmark: "ML, sygn. 1678.0104",
      description:
        '<p>Notatka o postaci dezertera. <a href="https://example.com/notes">Źródło</a></p>',
      image: "/media/content/note.jpg",
      image_alt: "Karta notesu z rysunkiem",
      tags: [{ slug: "dezerter", title: "Dezerter" }],
    },
    {
      url: "/notes/4",
      title: "Nagranie",
      shelfmark: "",
      description: "",
      image: "",
      image_alt: "",
      tags: [],
    },
  ],
  tags: [
    { slug: "dezerter", title: "Dezerter" },
    { slug: "epidemia", title: "Epidemia" },
  ],
  materials: {
    texts: [
      {
        url: "/secondary-texts/4",
        author: "Jan Kowalski",
        title: "Recenzja „Wertepów”",
        publication: "Czytelnik, Warszawa 1948, s. 3",
      },
    ],
    visuals: [
      {
        url: "/materials/9",
        title: "Autor w Dolinie",
        shelfmark: "ML, sygn. 1700",
        image: "/media/photo.jpg",
        image_alt: "Buczkowski przy biurku",
      },
    ],
  },
};

function mockPage(work: Partial<WorkData> = {}) {
  server.use(
    http.get(WORK_URL, () => HttpResponse.json({ ...WORK, ...work })),
    // pdf.js keeps the scan loading; jsdom cannot draw it anyway.
    http.get(SCAN_URL, async () => {
      await delay("infinite");
      return new HttpResponse(null);
    }),
  );
}

async function renderPage() {
  const result = renderRoute("/works/wertepy");
  await screen.findByRole("heading", { level: 1, name: "Wertepy" });
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
function column(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 3, name });
  const element = heading.parentElement?.parentElement;
  if (element == null) {
    throw new Error(`'${name}' heads no block.`);
  }
  return element;
}

describe("WorkPage", () => {
  it("US-RA-04 AC1: the hero shows type line, title and description; Utwory is active", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(within(hero()).getByText("Utwór · Leopold Buczkowski · 1947")).toBeVisible();
    expect(within(hero()).getByText("Pierwsza powieść Leopolda Buczkowskiego.")).toBeVisible();
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).getByRole("link", { name: "Utwory" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-WR-13 AC2: a draft that staff preview shows the draft banner", async () => {
    mockPage({ is_draft: true });

    const { container } = await renderPage();

    expect(screen.getByText("Szkic — niewidoczny publicznie")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-WR-13 AC2: a published page has no draft banner", async () => {
    mockPage();

    await renderPage();

    expect(screen.queryByText("Szkic — niewidoczny publicznie")).not.toBeInTheDocument();
  });

  it("US-RA-04 AC1: a work without editions or description shows neither (R-02)", async () => {
    mockPage({ year: null, description: "", editions: [] });

    const { container } = await renderPage();

    expect(within(hero()).getByText("Utwór · Leopold Buczkowski")).toBeVisible();
    expect(hero().querySelectorAll("p")).toHaveLength(1);
    expect(screen.queryByRole("heading", { name: "Wydania" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-04 AC2: editions by year with publisher and place; the earliest is the first edition", async () => {
    mockPage();

    const { container } = await renderPage();

    const editions = column("Wydania");
    expect(within(editions).getByText("2")).toBeVisible();
    expect(
      within(editions)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual([
      "1947Gebethner i WolffWarszawa · pierwsze wydanie",
      "1957Państwowy Instytut WydawniczyWarszawa",
    ]);
    // An edition has no page of its own.
    expect(within(editions).queryByRole("link")).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-04 AC3: 'Fragmenty maszynopisu' previews the main typescript's fragments as fragment cards", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Fragmenty maszynopisu");
    expect(within(fragments).getByText("2 z 24")).toBeVisible();
    expect(within(fragments).getByText("Wybór redakcji, w kolejności tekstu")).toBeVisible();
    const [first, second] = within(fragments).getAllByRole("article");
    if (first === undefined || second === undefined) {
      throw new Error("Expected two fragment cards.");
    }
    // R-10: location line with the source type, quote, scan page, shelfmark, description, tags.
    expect(
      within(first).getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/1?fragment=5");
    expect(within(first).getByText("Maszynopis")).toBeVisible();
    expect(within(first).getByText("Grzybniak chodził od chałupy do chałupy.")).toBeVisible();
    expect(within(first).getByRole("img", { name: "Skan · strona 3" })).toBeVisible();
    expect(within(first).getByText("ML, sygn. 1618.0009")).toBeVisible();
    expect(
      within(first).getByText("Grzybniak leczy chorych podczas epidemii tyfusu."),
    ).toBeVisible();
    expect(within(first).getByRole("link", { name: "Epidemia" })).toHaveAttribute(
      "href",
      "/tags/epidemia",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-10: a fragment without scan, location, shelfmark, description or tags shows none of them", async () => {
    mockPage();

    const { container } = await renderPage();

    const second = within(card("Fragmenty maszynopisu")).getAllByRole("article")[1];
    if (second === undefined) {
      throw new Error("Expected a second fragment card.");
    }
    expect(within(second).getAllByRole("link")).toHaveLength(1);
    expect(within(second).getByRole("link")).toHaveAccessibleName("Wertepy · Fragment 03");
    expect(within(second).queryByRole("img")).not.toBeInTheDocument();
    expect(second.querySelectorAll("p")).toHaveLength(0);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-10: a scan that cannot be loaded leaves the card without a thumbnail", async () => {
    mockPage();
    server.use(http.get(SCAN_URL, () => new HttpResponse(null, { status: 404 })));

    await renderPage();

    const first = within(card("Fragmenty maszynopisu")).getAllByRole("article")[0];
    if (first === undefined) {
      throw new Error("Expected a fragment card.");
    }
    await waitFor(() => {
      expect(within(first).queryByRole("img")).not.toBeInTheDocument();
    });
  });

  it("D20: 'Wszystkie fragmenty (24)' opens the main typescript with the list expanded", async () => {
    mockPage();

    await renderPage();

    expect(
      within(card("Fragmenty maszynopisu")).getByRole("link", {
        name: "Wszystkie fragmenty (24)",
      }),
    ).toHaveAttribute("href", "/typescripts/1?fragments=all");
  });

  it("R-09: a preview showing every fragment has a plain count and no link", async () => {
    mockPage({ fragments: { ...WORK.fragments, total: 2 } });

    await renderPage();

    const fragments = card("Fragmenty maszynopisu");
    expect(within(fragments).getByText("2")).toBeVisible();
    expect(
      within(fragments).queryByRole("link", { name: /Wszystkie fragmenty/ }),
    ).not.toBeInTheDocument();
  });

  it("US-RA-04 AC3: 'Maszynopisy' numbers the work's typescripts, each linking to its page", async () => {
    mockPage();

    await renderPage();

    const typescripts = card("Maszynopisy");
    expect(within(typescripts).getByText("2")).toBeVisible();
    const links = within(typescripts).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "01Pierwsza wersja, ML, sygn. 1618",
      "02Druga wersja",
    ]);
    expect(links[1]).toHaveAttribute("href", "/typescripts/2");
  });

  it("US-RA-04 AC3: 'Zapiski' shows the notes as note cards", async () => {
    mockPage();

    const { container } = await renderPage();

    const notes = card("Zapiski");
    expect(within(notes).getByText("2")).toBeVisible();
    expect(within(notes).getByText("Zapiski autora związane z utworem")).toBeVisible();
    const [note, recording] = within(notes).getAllByRole("article");
    if (note === undefined || recording === undefined) {
      throw new Error("Expected two note cards.");
    }
    expect(within(note).getByRole("link", { name: "Notes 18 · karta 4" })).toHaveAttribute(
      "href",
      "/notes/3",
    );
    expect(within(note).getByText("Zapisek")).toBeVisible();
    expect(within(note).getByRole("img", { name: "Karta notesu z rysunkiem" })).toHaveAttribute(
      "src",
      "/media/content/note.jpg",
    );
    expect(within(note).getByText("ML, sygn. 1678.0104")).toBeVisible();
    expect(within(note).getByText(/Notatka o postaci dezertera\./)).toBeVisible();
    // A link in the description stays its own link, above the card's.
    const source = within(note).getByRole("link", { name: "Źródło" });
    expect(source).toHaveAttribute("href", "https://example.com/notes");
    expect(source.closest("[data-slot=card-description]")).not.toBeNull();
    expect(within(note).getByRole("link", { name: "Dezerter" })).toHaveAttribute(
      "href",
      "/tags/dezerter",
    );
    // Without an image, the placeholder board (design/rules.md), hidden from screen readers.
    expect(within(recording).getByText("[Skan zapisku]")).toBeInTheDocument();
    expect(within(recording).queryByRole("img")).not.toBeInTheDocument();
    expect(within(recording).getAllByRole("link")).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-04 AC4: the tag column shows the tags, each linking to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const tags = column("Tagi");
    expect(within(tags).getByText("2")).toBeVisible();
    expect(
      within(tags)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(["/tags/dezerter", "/tags/epidemia"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-05 AC1, AC2: a tag on a work link shows in the tag column and links to its tag page", async () => {
    mockPage({ tags: [...WORK.tags, { slug: "recepcja", title: "Recepcja" }] });

    const { container } = await renderPage();

    const tags = column("Tagi");
    expect(within(tags).getByText("3")).toBeVisible();
    expect(within(tags).getByRole("link", { name: "Recepcja" })).toHaveAttribute(
      "href",
      "/tags/recepcja",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-04 AC5: the contextual materials linked to the work", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(screen.getByRole("heading", { level: 2, name: "Materiały kontekstowe" })).toBeVisible();
    expect(screen.getByRole("link", { name: /Jan Kowalski, Recenzja „Wertepów”/ })).toHaveAttribute(
      "href",
      "/secondary-texts/4",
    );
    const visual = screen.getByRole("link", { name: /Autor w Dolinie, ML, sygn\. 1700/ });
    expect(visual).toHaveAttribute("href", "/materials/9");
    expect(within(visual).getByRole("img", { name: "Buczkowski przy biurku" })).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-06 AC1: every item in the main column, tag column and contextual materials links to a page", async () => {
    mockPage();

    const { container } = await renderPage();

    const hrefs = within(screen.getByRole("main"))
      .getAllByRole("link")
      .map((link) => link.getAttribute("href") ?? "");
    // The note description's own link is the only one out of the archive.
    expect([...hrefs].sort()).toEqual(
      [
        "/typescripts/1?fragment=5",
        "/tags/epidemia",
        "/typescripts/1?fragment=7",
        "/typescripts/1?fragments=all",
        "/typescripts/1",
        "/typescripts/2",
        "/notes/3",
        "https://example.com/notes",
        "/tags/dezerter",
        "/notes/4",
        "/tags/dezerter",
        "/tags/epidemia",
        "/secondary-texts/4",
        "/materials/9",
      ].sort(),
    );
    for (const href of hrefs.filter((link) => link.startsWith("/"))) {
      expect(
        matchRoutes(routes, href)?.map((match) => match.route.path),
        href,
      ).not.toContain("*");
    }
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a work with no fragments, typescripts, notes, tags or materials renders none of those blocks", async () => {
    mockPage({
      main_typescript: null,
      fragments: { items: [], total: 0 },
      typescripts: [],
      notes: [],
      tags: [],
      materials: { texts: [], visuals: [] },
    });

    const { container } = await renderPage();

    // The editions, the only block left, head the page's sections (heading order, R-12).
    expect(
      screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent),
    ).toEqual(["Wydania"]);
    expect(screen.queryByRole("heading", { name: "Tagi" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-12: with an empty main column, the tag column is headed by h2", async () => {
    mockPage({
      editions: [],
      main_typescript: null,
      fragments: { items: [], total: 0 },
      typescripts: [],
      notes: [],
      materials: { texts: [], visuals: [] },
    });

    const { container } = await renderPage();

    expect(screen.getByRole("heading", { level: 2, name: "Tagi" })).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-06: a work the API does not find shows the not-found page", async () => {
    server.use(http.get(WORK_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/works/wertepy");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(WORK_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/works/wertepy");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję utwór…");
    expect(
      await screen.findByText("Nie udało się wczytać utworu. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
