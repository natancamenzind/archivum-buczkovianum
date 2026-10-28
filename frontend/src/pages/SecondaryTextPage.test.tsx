import { fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type SecondaryTextData = components["schemas"]["SecondaryTextPage"];
type Document = components["schemas"]["Document"];
type Fragment = components["schemas"]["FragmentCard"];

const PAGE_URL = "*/api/secondary-texts/4/";
const DOCUMENT_URL = "*/api/documents/20/";

const FRAGMENT: Fragment = {
  id: 5,
  url: "/typescripts/1?fragment=5",
  source_type: "typescript",
  work: "Wertepy",
  number: 1,
  location: "rozdział I",
  quote: "Grzybniak chodził od chałupy do chałupy.",
  scan: "",
  start_page: null,
  shelfmark: "ML, sygn. 1618.0009",
  description: "Grzybniak leczy chorych podczas epidemii tyfusu.",
  tags: [{ slug: "pamiec", title: "Pamięć" }],
};

const LETTER: SecondaryTextData = {
  id: 4,
  is_draft: false,
  title: "List nr 32",
  description: "<p>Transkrypcja listu z zachowaniem układu oryginału.</p>",
  kind: "letter",
  sender: "Leopold Buczkowski",
  letter_date: "1947-10-01",
  document: 20,
  works: [
    { slug: "wertepy", title: "Wertepy", year: 1947, fragment_count: 24 },
    { slug: "czarny-potok", title: "Czarny potok", year: null, fragment_count: 0 },
  ],
  fragments: {
    items: [
      FRAGMENT,
      { ...FRAGMENT, id: 6, url: "/typescripts/2?fragment=6", work: "Czarny potok", number: 2 },
    ],
    total: 5,
  },
  tags: [
    { slug: "pamiec", title: "Pamięć" },
    { slug: "pisanie", title: "Pisanie" },
    { slug: "wojna", title: "Wojna" },
  ],
};

const DOCUMENT: Document = {
  id: 20,
  is_draft: false,
  kind: "plain",
  text: "Drogi Panie, piszę z Dolinoszczęsnej.",
  page_offsets: [],
  scan: "",
  fragments: [
    {
      id: 30,
      start: 13,
      end: 18,
      number: 1,
      start_page: null,
      location: "",
      shelfmark: "",
      tags: [{ slug: "wojna", title: "Wojna" }],
    },
  ],
};

function mockPage(page: Partial<SecondaryTextData> = {}, document: Partial<Document> = {}) {
  server.use(
    http.get(PAGE_URL, () => HttpResponse.json({ ...LETTER, ...page })),
    http.get(DOCUMENT_URL, () => HttpResponse.json({ ...DOCUMENT, ...document })),
  );
}

async function renderPage(url = "/secondary-texts/4") {
  const result = renderRoute(url);
  await screen.findByRole("heading", { level: 1 });
  return result;
}

function hero(): HTMLElement {
  const header = screen
    .getByRole("heading", { level: 1 })
    .closest<HTMLElement>("[data-slot=page-header]");
  if (header === null) {
    throw new Error("The title is not inside the hero.");
  }
  return header;
}

/** The card a section heading opens. */
function card(name: string): HTMLElement {
  const element = screen
    .getByRole("heading", { level: 2, name })
    .closest<HTMLElement>("[data-slot=card]");
  if (element === null) {
    throw new Error(`'${name}' is not inside a card.`);
  }
  return element;
}

/** The block a column header heads: the header's parent. */
function column(name: string): HTMLElement {
  const element = screen.getByRole("heading", { level: 3, name }).parentElement?.parentElement;
  if (element == null) {
    throw new Error(`'${name}' heads no block.`);
  }
  return element;
}

describe("SecondaryTextPage", () => {
  const scrollIntoView = vi.fn();

  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoView;
  });

  afterEach(() => {
    scrollIntoView.mockReset();
    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("US-RA-10 AC1: a letter's hero shows kind, sender and date, title and description", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(within(hero()).getByRole("heading", { level: 1, name: "List nr 32" })).toBeVisible();
    expect(within(hero()).getByText("List · Leopold Buczkowski · 1.10.1947")).toBeVisible();
    expect(
      within(hero()).getByText("Transkrypcja listu z zachowaniem układu oryginału."),
    ).toBeVisible();
    expect(within(hero()).queryByRole("img")).not.toBeInTheDocument();
    // No navigation item is active on a secondary text page (R-07).
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).queryByRole("link", { current: "page" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    ["review", "Recenzja"],
    ["study", "Opracowanie"],
    ["recording", "Nagranie"],
    ["other", "Tekst sekundarny"],
  ] as const)(
    "US-RA-10 AC1: a %s's type line is its kind, without sender or date",
    async (kind, label) => {
      mockPage({ kind, sender: "Jan Kowalski", letter_date: "1948-02-03", description: "" });

      const { container } = await renderPage();

      expect(within(hero()).getByText(label)).toBeVisible();
      expect(hero().querySelectorAll("p")).toHaveLength(1);
      expect(await axeViolations(container)).toEqual([]);
    },
  );

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

  it("US-RA-10 AC1: a letter without sender or date shows what it has (R-02)", async () => {
    mockPage({ sender: "", letter_date: "1947-12-24" });

    const { container } = await renderPage();

    expect(within(hero()).getByText("List · 24.12.1947")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC2: 'Powiązane utwory' lists the related works with year, each linking to it", async () => {
    mockPage();

    const { container } = await renderPage();

    const works = column("Powiązane utwory");
    expect(within(works).getByText("2")).toBeVisible();
    const links = within(works).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["1947Wertepy", "Czarny potok"]);
    expect(links[0]).toHaveAttribute("href", "/works/wertepy");
    expect(links[1]).toHaveAttribute("href", "/works/czarny-potok");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC3: 'Transkrypcja' shows the full text in the reader, its fragments highlighted", async () => {
    mockPage();

    const { container } = await renderPage();

    const text = card("Transkrypcja");
    const fragment = await within(text).findByRole("button", { name: "Fragment 01: piszę" });
    expect(within(text).getByText(/Drogi Panie,/)).toBeVisible();
    fireEvent.click(fragment);
    expect(within(text).getByRole("link", { name: "Wojna" })).toHaveAttribute(
      "href",
      "/tags/wojna",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC3: an OCR text is read with its scan pages", async () => {
    mockPage({}, { kind: "ocr", page_offsets: [0, 13], fragments: [] });

    const { container } = await renderPage();

    const text = card("Transkrypcja");
    expect(await within(text).findByText("Skan · strona 2 z 2")).toBeVisible();
    expect(screen.getByRole("group", { name: "Widok" })).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC3: opened with ?fragment=, the reader scrolls to the fragment", async () => {
    mockPage();

    const { container } = await renderPage("/secondary-texts/4?fragment=30");

    const fragment = await screen.findByRole("button", { name: "Fragment 01: piszę" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC3: 'Powiązane fragmenty' previews typescript fragments as cards, with no 'all' link", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Powiązane fragmenty");
    expect(within(fragments).getByText("2 z 5")).toBeVisible();
    const cards = within(fragments).getAllByRole("article");
    expect(cards).toHaveLength(2);
    expect(
      within(fragments).getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/1?fragment=5");
    expect(
      within(fragments).getByRole("link", { name: "Czarny potok · Fragment 02 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/2?fragment=6");
    expect(within(fragments).queryByText(/Wszystkie/)).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-10 AC4: 'Powiązane tagi' shows the tags, each linking to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const tags = column("Powiązane tagi");
    expect(within(tags).getByText("3")).toBeVisible();
    expect(
      within(tags)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Pamięć", "Pisanie", "Wojna"]);
    expect(within(tags).getByRole("link", { name: "Pisanie" })).toHaveAttribute(
      "href",
      "/tags/pisanie",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a text with no works, related fragments or tags renders none of those blocks", async () => {
    mockPage({ works: [], fragments: { items: [], total: 0 }, tags: [] });

    const { container } = await renderPage();

    await screen.findByRole("button", { name: "Fragment 01: piszę" });
    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings).toEqual(["List nr 32", "Transkrypcja"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-06: a secondary text the API does not find shows the not-found page", async () => {
    server.use(http.get(PAGE_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/secondary-texts/4");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("an address that is not a secondary text number shows the not-found page", () => {
    renderRoute("/secondary-texts/list");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(PAGE_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/secondary-texts/4");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję tekst sekundarny…");
    expect(
      await screen.findByText(
        "Nie udało się wczytać tekstu sekundarnego. Spróbuj ponownie później.",
      ),
    ).toBeVisible();
  });

  it("shows the reader's loading state, then an error when the text cannot be loaded", async () => {
    server.use(
      http.get(PAGE_URL, () => HttpResponse.json(LETTER)),
      http.get(DOCUMENT_URL, () => new HttpResponse(null, { status: 500 })),
    );

    await renderPage();

    expect(within(card("Transkrypcja")).getByRole("status")).toHaveTextContent("Wczytuję tekst…");
    expect(
      await screen.findByText("Nie udało się wczytać tekstu. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
