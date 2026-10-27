import { fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type TypescriptData = components["schemas"]["TypescriptPage"];
type Document = components["schemas"]["Document"];

const TYPESCRIPT_URL = "*/api/typescripts/1/";
const DOCUMENT_URL = "*/api/documents/10/";

const TYPESCRIPT: TypescriptData = {
  id: 1,
  title: "Maszynopis „Wertepów”",
  description: "<p>Pierwsza wersja maszynopisu powieści.</p>",
  shelfmark: "ML, sygn. 1618",
  document: 10,
  page_count: 2,
  work: { slug: "wertepy", title: "Wertepy", year: 1947, fragment_count: 24 },
  work_typescripts: [
    { id: 1, title: "Pierwsza wersja", shelfmark: "ML, sygn. 1618" },
    { id: 2, title: "Druga wersja", shelfmark: "ML, sygn. 1619" },
  ],
  fragments: {
    items: [
      { id: 7, number: 3, location: "rozdział III", shelfmark: "ML, sygn. 1618.0019" },
      { id: 5, number: 1, location: "rozdział I", shelfmark: "ML, sygn. 1618.0009" },
    ],
    total: 3,
  },
  tags: [
    { slug: "wies", title: "Wieś" },
    { slug: "wojna", title: "Wojna" },
  ],
  materials: {
    texts: [
      { url: "/materials/8", author: "", title: "Film dokumentalny", publication: "" },
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
      { url: "/materials/11", title: "Plakat", shelfmark: "", image: "", image_alt: "" },
    ],
  },
};

const TEXT = "Pierwsza strona tekstu. Druga strona tekstu.";

const DOCUMENT: Document = {
  id: 10,
  kind: "ocr",
  text: TEXT,
  page_offsets: [0, 24],
  scan: "",
  fragments: [
    {
      id: 5,
      start: 0,
      end: 8,
      number: 1,
      start_page: 1,
      location: "rozdział I",
      shelfmark: "ML, sygn. 1618.0009",
      tags: [{ slug: "wies", title: "Wieś" }],
    },
    {
      id: 6,
      start: 9,
      end: 15,
      number: 2,
      start_page: 1,
      location: "",
      shelfmark: "",
      tags: [],
    },
    {
      id: 7,
      start: 24,
      end: 29,
      number: 3,
      start_page: 2,
      location: "rozdział III",
      shelfmark: "ML, sygn. 1618.0019",
      tags: [{ slug: "wojna", title: "Wojna" }],
    },
  ],
};

function mockPage(typescript: Partial<TypescriptData> = {}, document: Partial<Document> = {}) {
  server.use(
    http.get(TYPESCRIPT_URL, () => HttpResponse.json({ ...TYPESCRIPT, ...typescript })),
    http.get(DOCUMENT_URL, () => HttpResponse.json({ ...DOCUMENT, ...document })),
  );
}

async function renderPage(url = "/typescripts/1") {
  const result = renderRoute(url);
  await screen.findByRole("heading", { level: 1, name: TYPESCRIPT.title });
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

function highlight(text: string): HTMLElement {
  return screen.getByRole("button", { name: text });
}

describe("TypescriptPage", () => {
  const scrollIntoView = vi.fn();

  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoView;
  });

  afterEach(() => {
    scrollIntoView.mockReset();
    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("US-RA-08 AC1: the hero shows type line, title and description; Maszynopisy is active", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(within(hero()).getByText("Maszynopis · ML, sygn. 1618 · 1947")).toBeVisible();
    expect(within(hero()).getByText("Pierwsza wersja maszynopisu powieści.")).toBeVisible();
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).getByRole("link", { name: "Maszynopisy" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-08 AC1: a missing shelfmark, year and description are left out (R-02)", async () => {
    mockPage({ shelfmark: "", description: "", work: null });

    await renderPage();

    expect(within(hero()).getByText("Maszynopis")).toBeVisible();
    expect(hero().querySelectorAll("p")).toHaveLength(1);
  });

  it("US-RA-08 AC2: the context column shows the work with year and fragment count", async () => {
    mockPage();

    const { container } = await renderPage();

    const work = column("Utwór");
    const link = within(work).getByRole("link", { name: /Wertepy/ });
    expect(link).toHaveAttribute("href", "/works/wertepy");
    expect(link).toHaveTextContent(/^1947Wertepy24 fragmenty$/);
    expect(within(work).getByText("1")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-08 AC2: a work with no fragments shows no count (plan D23)", async () => {
    mockPage({ work: { slug: "wertepy", title: "Wertepy", year: null, fragment_count: 0 } });

    await renderPage();

    expect(within(column("Utwór")).getByRole("link")).toHaveTextContent(/^Wertepy$/);
  });

  it("US-RA-08 AC2: the work's typescripts with shelfmark and title, the current one marked", async () => {
    mockPage();

    await renderPage();

    const typescripts = column("Maszynopisy utworu");
    const links = within(typescripts).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "ML, sygn. 1618Pierwsza wersja",
      "ML, sygn. 1619Druga wersja",
    ]);
    expect(links[0]).toHaveAttribute("aria-current", "page");
    expect(links[1]).not.toHaveAttribute("aria-current");
    expect(links[1]).toHaveAttribute("href", "/typescripts/2");
    expect(within(typescripts).getByText("2")).toBeVisible();
  });

  it("US-RA-08 AC3: 'Skan maszynopisu' counts the pages and shows each scan page next to its text", async () => {
    mockPage();

    const { container } = await renderPage();

    const scan = card("Skan maszynopisu");
    expect(within(scan).getByText("2 strony")).toBeVisible();
    expect(await within(scan).findByText("Skan · strona 1 z 2")).toBeVisible();
    expect(within(scan).getByText("Skan · strona 2 z 2")).toBeVisible();
    const paragraphs = Array.from(scan.querySelectorAll("p.whitespace-pre-wrap"));
    expect(paragraphs.map((p) => p.textContent)).toEqual([
      "Pierwsza strona tekstu. ",
      "Druga strona tekstu.",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11 AC1: on mobile a Skan / Transkrypcja toggle switches the view", async () => {
    mockPage();

    await renderPage();

    const toggle = await screen.findByRole("group", { name: "Widok" });
    const scan = within(toggle).getByRole("button", { name: "Skan" });
    const text = within(toggle).getByRole("button", { name: "Transkrypcja" });
    expect(scan).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(text);
    expect(text).toHaveAttribute("aria-pressed", "true");
    expect(scan).toHaveAttribute("aria-pressed", "false");
  });

  it("R-11 AC2: fragments are highlighted; clicking one shows its tags, each linking to its tag page", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragment = await screen.findByRole("button", { name: "Pierwsza" });
    expect(highlight("strona")).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(fragment);

    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Fragment 01 · rozdział I")).toBeVisible();
    const scan = card("Skan maszynopisu");
    expect(within(scan).getByRole("link", { name: "Wieś" })).toHaveAttribute("href", "/tags/wies");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11 AC2: a highlight works from the keyboard", async () => {
    mockPage();

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Druga" });
    fireEvent.keyDown(fragment, { key: "Enter" });

    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Fragment 03 · rozdział III")).toBeVisible();
    fireEvent.keyDown(highlight("strona"), { key: "Tab" });
    expect(highlight("strona")).toHaveAttribute("aria-pressed", "false");
    fireEvent.keyDown(highlight("strona"), { key: " " });
    expect(highlight("strona")).toHaveAttribute("aria-pressed", "true");
  });

  it("R-11 AC3: opened with ?fragment=, the reader shows the text, scrolls to the fragment and selects it", async () => {
    mockPage();

    await renderPage("/typescripts/1?fragment=7");

    const fragment = await screen.findByRole("button", { name: "Druga" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    expect(screen.getByRole("button", { name: "Transkrypcja" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("US-RA-08 AC3: 'Fragmenty z maszynopisu' previews the fragments as a numbered list", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Fragmenty z maszynopisu");
    expect(within(fragments).getByText("2 z 3")).toBeVisible();
    const links = within(fragments).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "03Fragment 03 · rozdział III · ML, sygn. 1618.0019",
      "01Fragment 01 · rozdział I · ML, sygn. 1618.0009",
      "Wszystkie fragmenty (3)",
    ]);
    expect(links[0]).toHaveAttribute("href", "/typescripts/1?fragment=7");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-08 AC3: a fragment in the list opens it in the reader", async () => {
    mockPage();

    await renderPage();
    await screen.findByRole("button", { name: "Druga" });

    fireEvent.click(
      within(card("Fragmenty z maszynopisu")).getByRole("link", { name: /Fragment 03/ }),
    );

    expect(await screen.findByText("Fragment 03 · rozdział III")).toBeVisible();
    expect(scrollIntoView.mock.contexts[0]).toBe(screen.getByRole("button", { name: "Druga" }));
  });

  it("D20: 'Wszystkie fragmenty (3)' expands the list in place, in page order", async () => {
    mockPage();

    await renderPage();
    await screen.findByRole("button", { name: "Druga" });

    fireEvent.click(screen.getByRole("link", { name: "Wszystkie fragmenty (3)" }));

    const fragments = card("Fragmenty z maszynopisu");
    expect(await within(fragments).findByText("3")).toBeVisible();
    expect(
      within(fragments)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual([
      "01Fragment 01 · rozdział I · ML, sygn. 1618.0009",
      "02Fragment 02",
      "03Fragment 03 · rozdział III · ML, sygn. 1618.0019",
    ]);
  });

  it("D20: ?fragments=all, the work page's link, opens the page with the list expanded", async () => {
    mockPage();

    await renderPage("/typescripts/1?fragments=all");

    const fragments = card("Fragmenty z maszynopisu");
    expect(await within(fragments).findByText("Fragment 02")).toBeVisible();
    expect(within(fragments).queryByText("Wszystkie fragmenty (3)")).not.toBeInTheDocument();
  });

  it("R-09: a preview showing every fragment has a plain count and no link", async () => {
    mockPage({ fragments: { ...TYPESCRIPT.fragments, total: 2 } });

    await renderPage();

    const fragments = card("Fragmenty z maszynopisu");
    expect(within(fragments).getByText("2")).toBeVisible();
    expect(within(fragments).queryByText(/Wszystkie fragmenty/)).not.toBeInTheDocument();
  });

  it("US-RA-08 AC4: the tag column shows the tags, each linking to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const tags = column("Tagi");
    expect(within(tags).getByText("2")).toBeVisible();
    expect(within(tags).getByRole("link", { name: "Wieś" })).toHaveAttribute("href", "/tags/wies");
    expect(within(tags).getByRole("link", { name: "Wojna" })).toHaveAttribute(
      "href",
      "/tags/wojna",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-08 AC5: the contextual materials of the work, in the block's two parts", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(screen.getByRole("heading", { level: 2, name: "Materiały kontekstowe" })).toBeVisible();
    const texts = column("Teksty sekundarne");
    expect(
      within(texts)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual([
      "01Film dokumentalny",
      "02Jan Kowalski, Recenzja „Wertepów”Czytelnik, Warszawa 1948, s. 3",
    ]);
    expect(within(texts).getAllByRole("link")[1]).toHaveAttribute("href", "/secondary-texts/4");
    const visuals = column("Materiały wizualne");
    const photo = within(visuals).getByRole("link", { name: /Autor w Dolinie/ });
    expect(photo).toHaveAttribute("href", "/materials/9");
    expect(photo).toHaveTextContent("Autor w Dolinie, ML, sygn. 1700");
    expect(within(photo).getByRole("img", { name: "Buczkowski przy biurku" })).toBeVisible();
    const poster = within(visuals).getByRole("link", { name: "Plakat" });
    expect(within(poster).queryByRole("img")).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a page with no work, fragments, tags or materials renders none of those blocks", async () => {
    mockPage(
      {
        work: null,
        fragments: { items: [], total: 0 },
        tags: [],
        materials: { texts: [], visuals: [] },
      },
      { fragments: [] },
    );

    const { container } = await renderPage();

    await screen.findByText("Skan · strona 1 z 2");
    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    // In the mobile order (R-05): main column, then context.
    expect(headings).toEqual([TYPESCRIPT.title, "Skan maszynopisu", "Maszynopisy utworu"]);
    expect(screen.queryByRole("button", { name: "Pierwsza" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11: a plain text is shown as text, without scans or the toggle", async () => {
    mockPage({}, { kind: "plain", page_offsets: [] });

    await renderPage();

    await screen.findByRole("button", { name: "Pierwsza" });
    expect(screen.queryByRole("group", { name: "Widok" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Skan · strona/)).not.toBeInTheDocument();
  });

  it("R-11: a scan that cannot be loaded says so", async () => {
    mockPage({}, { scan: "/media/scans/missing.pdf" });
    server.use(
      http.get("*/media/scans/missing.pdf", () => new HttpResponse(null, { status: 404 })),
    );

    await renderPage();

    expect(await screen.findByText("Nie udało się wczytać skanu.")).toBeVisible();
    expect(screen.queryByRole("img", { name: /Skan · strona/ })).not.toBeInTheDocument();
  });

  it("R-06: a typescript the API does not find shows the not-found page", async () => {
    server.use(http.get(TYPESCRIPT_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/typescripts/1");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("an address that is not a typescript number shows the not-found page", () => {
    renderRoute("/typescripts/wertepy");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(TYPESCRIPT_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/typescripts/1");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję maszynopis…");
    expect(
      await screen.findByText("Nie udało się wczytać maszynopisu. Spróbuj ponownie później."),
    ).toBeVisible();
  });

  it("shows the reader's loading state, then an error when the text cannot be loaded", async () => {
    server.use(
      http.get(TYPESCRIPT_URL, () => HttpResponse.json(TYPESCRIPT)),
      http.get(DOCUMENT_URL, () => new HttpResponse(null, { status: 500 })),
    );

    await renderPage();

    expect(within(card("Skan maszynopisu")).getByRole("status")).toHaveTextContent(
      "Wczytuję tekst…",
    );
    expect(
      await screen.findByText("Nie udało się wczytać tekstu. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
