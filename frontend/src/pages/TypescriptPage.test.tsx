import { fireEvent, screen, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { scrollIntoViewport, scrollOutOfViewport } from "@/test/intersection";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type TypescriptData = components["schemas"]["TypescriptPage"];
type Document = components["schemas"]["Document"];

const TYPESCRIPT_URL = "*/api/typescripts/1/";
const DOCUMENT_URL = "*/api/documents/10/";

const TYPESCRIPT: TypescriptData = {
  id: 1,
  is_draft: false,
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
  is_draft: false,
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

const EXTRA_FRAGMENT: Document["fragments"][number] = {
  id: 0,
  start: 0,
  end: 0,
  number: 4,
  start_page: 1,
  location: "",
  shelfmark: "",
  tags: [],
};

function mockPage(typescript: Partial<TypescriptData> = {}, document: Partial<Document> = {}) {
  server.use(
    http.get(TYPESCRIPT_URL, () => HttpResponse.json({ ...TYPESCRIPT, ...typescript })),
    http.get(DOCUMENT_URL, () => HttpResponse.json({ ...DOCUMENT, ...document })),
  );
}

const LONG_PAGES = Array.from({ length: 40 }, (_, index) => `Strona ${String(index + 1)}. `);
const LONG_OFFSETS = LONG_PAGES.map((_, index) => LONG_PAGES.slice(0, index).join("").length);

/** A 40-page typescript with one fragment, the first word of page 38. */
function mockLongTypescript() {
  const start = LONG_OFFSETS[37] ?? 0;
  mockPage(
    { page_count: LONG_PAGES.length },
    {
      text: LONG_PAGES.join(""),
      page_offsets: LONG_OFFSETS,
      fragments: [{ ...EXTRA_FRAGMENT, id: 9, start, end: start + 6, start_page: 38 }],
    },
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
    // Before pdf.js draws it, a page keeps A4 proportions, so the reader does not jump.
    for (const page of within(scan).getAllByRole("img", { name: /Skan · strona/ })) {
      expect(page).toHaveStyle({ aspectRatio: "210 / 297" });
    }
    const paragraphs = Array.from(scan.querySelectorAll("p.whitespace-pre-wrap"));
    expect(paragraphs.map((p) => p.textContent)).toEqual([
      "Pierwsza strona tekstu. ",
      "Druga strona tekstu.",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-09 AC1: a long typescript is read whole, and only the scan pages in view are drawn", async () => {
    mockLongTypescript();

    const { container } = await renderPage();

    const scan = card("Skan maszynopisu");
    expect(await within(scan).findByText("Skan · strona 40 z 40")).toBeVisible();
    const paragraphs = Array.from(scan.querySelectorAll("p.whitespace-pre-wrap"));
    expect(paragraphs.map((p) => p.textContent)).toEqual(LONG_PAGES);
    // A fragment far into the text is highlighted on its own page and can be opened.
    const fragment = within(scan).getByRole("button", { name: "Fragment 04: Strona" });
    expect(paragraphs[37]).toContainElement(fragment);
    fireEvent.click(fragment);
    expect(within(scan).getByText("Fragment 04")).toBeVisible();
    expect(within(scan).getAllByRole("img", { name: /Skan · strona/ })).toHaveLength(40);
    expect(scan.querySelectorAll("canvas")).toHaveLength(0);

    const first = within(scan).getByRole("img", { name: "Skan · strona 1 z 40" });
    const second = within(scan).getByRole("img", { name: "Skan · strona 2 z 40" });
    scrollIntoViewport(first);
    scrollIntoViewport(second);
    expect(first.querySelector("canvas")).not.toBeNull();
    expect(second.querySelector("canvas")).not.toBeNull();
    expect(scan.querySelectorAll("canvas")).toHaveLength(2);

    // A page that scrolls away gives up its drawing and keeps its place in the reader.
    scrollOutOfViewport(first);
    expect(first.querySelector("canvas")).toBeNull();
    expect(first).toHaveStyle({ aspectRatio: "210 / 297" });
    expect(scan.querySelectorAll("canvas")).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-09 AC1: a link to a fragment late in a long typescript scrolls to it", async () => {
    mockLongTypescript();

    await renderPage("/typescripts/1?fragment=9");

    const fragment = await screen.findByRole("button", { name: "Fragment 04: Strona" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
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

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(highlight("Fragment 02: strona")).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(fragment);

    expect(fragment).toHaveAttribute("aria-pressed", "true");
    const details = screen.getByText("Fragment 01 · rozdział I");
    expect(details).toBeVisible();
    expect(details.closest("[aria-live=polite]")).not.toBeNull();
    const scan = card("Skan maszynopisu");
    expect(within(scan).getByRole("link", { name: "Wieś" })).toHaveAttribute("href", "/tags/wies");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11 AC2: a highlight works from the keyboard", async () => {
    mockPage();

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 03: Druga" });
    fireEvent.keyDown(fragment, { key: "Enter" });

    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Fragment 03 · rozdział III")).toBeVisible();
    fireEvent.keyDown(highlight("Fragment 02: strona"), { key: "Tab" });
    expect(highlight("Fragment 02: strona")).toHaveAttribute("aria-pressed", "false");
    fireEvent.keyDown(highlight("Fragment 02: strona"), { key: " " });
    expect(highlight("Fragment 02: strona")).toHaveAttribute("aria-pressed", "true");
  });

  it("R-11 AC2: of fragments with the same start, a click selects the inner one", async () => {
    const outer = { ...EXTRA_FRAGMENT, id: 8, start: 0, end: 15 };
    mockPage({}, { fragments: [...DOCUMENT.fragments, outer] });

    await renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Fragment 01: Pierwsza" }));

    expect(screen.getByText("Fragment 01 · rozdział I")).toBeVisible();
    expect(screen.queryByText(/^Fragment 04/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fragment 02: strona" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("R-11: a fragment reaching past the end of the text is highlighted up to the end", async () => {
    const past = { ...EXTRA_FRAGMENT, id: 9, start: 40, end: 99 };
    mockPage({}, { fragments: [...DOCUMENT.fragments, past] });

    await renderPage();

    expect(await screen.findByRole("button", { name: "Fragment 04: stu." })).toHaveTextContent(
      /^stu\.$/,
    );
  });

  it("R-11 AC3: opened with ?fragment=, the reader shows the text, scrolls to the fragment and selects it", async () => {
    mockPage();

    await renderPage("/typescripts/1?fragment=7");

    const fragment = await screen.findByRole("button", { name: "Fragment 03: Druga" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    expect(screen.getByRole("button", { name: "Transkrypcja" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("R-11 AC3: opened from a search result with ?q=, the reader shows the text, highlights the first match and scrolls to it", async () => {
    mockPage();

    const { container } = await renderPage("/typescripts/1?q=Tekstu");

    const match = await screen.findByText("tekstu", { selector: "mark" });
    expect(container.querySelectorAll("mark[data-search-match]")).toHaveLength(1);
    expect(match.textContent).toBe(TEXT.slice(16, 22));
    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView.mock.contexts[0]).toBe(match);
    expect(screen.getByRole("button", { name: "Transkrypcja" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11 AC3: a match inside a fragment is highlighted within it", async () => {
    mockPage();

    await renderPage("/typescripts/1?q=pierwsza");

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(within(fragment).getByText("Pierwsza", { selector: "mark" })).toHaveAttribute(
      "data-search-match",
    );
  });

  it("R-11 AC3: a ?q= the text lacks scrolls nowhere", async () => {
    mockPage();

    await renderPage("/typescripts/1?q=potok");

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("R-11 AC3: ?q= matches whole words only, not the start of a longer one", async () => {
    mockPage();

    const { container } = await renderPage("/typescripts/1?q=tekst");

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(container.querySelector("mark[data-search-match]")).toBeNull();
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("R-11 AC3: a ?q= of regular expression characters is matched literally", async () => {
    mockPage();

    const { container } = await renderPage(`/typescripts/1?q=${encodeURIComponent(".*")}`);

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(container.querySelector("mark[data-search-match]")).toBeNull();
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
    await screen.findByRole("button", { name: "Fragment 03: Druga" });

    fireEvent.click(
      within(card("Fragmenty z maszynopisu")).getByRole("link", { name: /Fragment 03/ }),
    );

    expect(await screen.findByText("Fragment 03 · rozdział III")).toBeVisible();
    expect(scrollIntoView.mock.contexts[0]).toBe(
      screen.getByRole("button", { name: "Fragment 03: Druga" }),
    );
  });

  it("D20: 'Wszystkie fragmenty (3)' expands the list in place, in page order", async () => {
    mockPage();

    await renderPage();
    await screen.findByRole("button", { name: "Fragment 03: Druga" });

    fireEvent.click(screen.getByRole("link", { name: "Wszystkie fragmenty (3)" }));

    const fragments = card("Fragmenty z maszynopisu");
    expect(await within(fragments).findByText("3")).toBeVisible();
    const links = within(fragments).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "01Fragment 01 · rozdział I · ML, sygn. 1618.0009",
      "02Fragment 02",
      "03Fragment 03 · rozdział III · ML, sygn. 1618.0019",
    ]);
    expect(links[0]).toHaveFocus();
    // Opening a fragment keeps the list expanded.
    expect(links[1]).toHaveAttribute("href", "/typescripts/1?fragments=all&fragment=6");
  });

  it("D20: while the whole list loads, the preview stays, without the link", async () => {
    server.use(
      http.get(TYPESCRIPT_URL, () => HttpResponse.json(TYPESCRIPT)),
      http.get(DOCUMENT_URL, async () => {
        await delay("infinite");
        return HttpResponse.json(DOCUMENT);
      }),
    );

    await renderPage("/typescripts/1?fragments=all");

    const fragments = card("Fragmenty z maszynopisu");
    expect(within(fragments).getByText("2 z 3")).toBeVisible();
    expect(within(fragments).queryByText(/Wszystkie fragmenty/)).not.toBeInTheDocument();
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
    expect(screen.queryByRole("button", { name: "Fragment 01: Pierwsza" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11: a plain text is shown as text, without scans or the toggle", async () => {
    mockPage({}, { kind: "plain", page_offsets: [] });

    await renderPage();

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(screen.queryByRole("group", { name: "Widok" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Skan · strona/)).not.toBeInTheDocument();
  });

  it("R-11: a scan that cannot be loaded says so", async () => {
    mockPage({}, { scan: "/media/scans/missing.pdf" });
    server.use(
      http.get("*/media/scans/missing.pdf", () => new HttpResponse(null, { status: 404 })),
    );

    await renderPage("/typescripts/1?fragment=7");

    expect(await screen.findByText("Nie udało się wczytać skanu.")).toBeVisible();
    // The text, now at full width, is scrolled to the fragment again.
    expect(scrollIntoView).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("img", { name: /Skan · strona/ })).not.toBeInTheDocument();
    // On mobile the reader shows the text, without a toggle to the missing scan.
    expect(screen.queryByRole("group", { name: "Widok" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fragment 01: Pierwsza" })).toBeVisible();
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
