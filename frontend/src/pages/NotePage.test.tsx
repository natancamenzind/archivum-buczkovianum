import { fireEvent, screen, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type NoteData = components["schemas"]["NotePage"];
type Content = components["schemas"]["MediaContent"];
type Document = components["schemas"]["Document"];
type Fragment = components["schemas"]["FragmentCard"];

const PAGE_URL = "*/api/notes/3/";
const DOCUMENT_URL = "*/api/documents/20/";
const PDF_URL = "*/media/content/notes.pdf";

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
  description: "",
  tags: [{ slug: "pamiec", title: "Pamięć" }],
};

const NO_CONTENT: Content = {
  kind: "image",
  image: "",
  image_alt: "",
  file: "",
  external_url: "",
  document: null,
};

const NOTE: NoteData = {
  id: 3,
  is_draft: false,
  title: "Notes 18 · karta 4",
  description: "<p>Notatka o postaci dezertera.</p>",
  shelfmark: "ML, sygn. 1678.0104",
  content: { ...NO_CONTENT, image: "/media/content/card.jpg", image_alt: "Karta z notesu" },
  works: [
    { slug: "wertepy", title: "Wertepy", year: 1947, fragment_count: 24 },
    { slug: "czarny-potok", title: "Czarny potok", year: null, fragment_count: 0 },
  ],
  fragments: {
    items: [FRAGMENT, { ...FRAGMENT, id: 6, url: "/typescripts/2?fragment=6", number: 2 }],
    total: 5,
  },
  tags: [
    { slug: "dezerter", title: "Dezerter" },
    { slug: "pamiec", title: "Pamięć" },
  ],
};

const DOCUMENT: Document = {
  id: 20,
  is_draft: false,
  kind: "plain",
  text: "Dezerter idzie przez las.",
  page_offsets: [],
  scan: "",
  fragments: [
    {
      id: 30,
      start: 0,
      end: 8,
      number: 1,
      start_page: null,
      location: "",
      shelfmark: "",
      tags: [{ slug: "dezerter", title: "Dezerter" }],
    },
  ],
};

function mockPage(page: Partial<NoteData> = {}, document: Partial<Document> = {}) {
  server.use(
    http.get(PAGE_URL, () => HttpResponse.json({ ...NOTE, ...page })),
    http.get(DOCUMENT_URL, () => HttpResponse.json({ ...DOCUMENT, ...document })),
  );
}

function mockContent(content: Partial<Content>) {
  mockPage({ content: { ...NO_CONTENT, ...content } });
}

async function renderPage(url = "/notes/3") {
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

describe("NotePage", () => {
  const scrollIntoView = vi.fn();

  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoView;
  });

  afterEach(() => {
    scrollIntoView.mockReset();
    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("US-RA-11 AC1: the hero shows 'Zapisek · <shelfmark>', the title and the description", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(
      within(hero()).getByRole("heading", { level: 1, name: "Notes 18 · karta 4" }),
    ).toBeVisible();
    expect(within(hero()).getByText("Zapisek · ML, sygn. 1678.0104")).toBeVisible();
    expect(within(hero()).getByText("Notatka o postaci dezertera.")).toBeVisible();
    // No navigation item is active on a note page (R-07).
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).queryByRole("link", { current: "page" })).not.toBeInTheDocument();
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

  it("US-RA-11 AC1: a note without shelfmark or description shows 'Zapisek' and the title (R-02)", async () => {
    mockPage({ shelfmark: "", description: "" });

    const { container } = await renderPage();

    expect(within(hero()).getByText("Zapisek")).toBeVisible();
    expect(hero().querySelectorAll("p")).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC2: 'Powiązane utwory' lists the related works with year, each linking to it", async () => {
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

  it("US-RA-11 AC3: an image is shown inline with its text alternative", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(screen.getByRole("img", { name: "Karta z notesu" })).toHaveAttribute(
      "src",
      "/media/content/card.jpg",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC3: a PDF is opened inline with pdf.js, not offered as a download", async () => {
    mockContent({ kind: "document", file: "/media/content/notes.pdf" });
    // pdf.js keeps the file loading; jsdom cannot draw it anyway.
    server.use(
      http.get(PDF_URL, async () => {
        await delay("infinite");
        return new HttpResponse(null);
      }),
    );

    const { container } = await renderPage();

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję dokument…");
    expect(screen.queryByRole("link", { name: "Pobierz plik" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC3: a PDF that cannot be opened is offered as a download", async () => {
    mockContent({ kind: "document", file: "/media/content/notes.pdf" });
    server.use(http.get(PDF_URL, () => new HttpResponse(null, { status: 404 })));

    await renderPage();

    expect(await screen.findByRole("link", { name: "Pobierz plik" })).toHaveAttribute(
      "href",
      "/media/content/notes.pdf",
    );
  });

  it("US-RA-11 AC3: a document that is not a PDF is a download", async () => {
    mockContent({ kind: "document", file: "/media/content/notes.docx" });

    const { container } = await renderPage();

    const download = screen.getByRole("link", { name: "Pobierz plik" });
    expect(download).toHaveAttribute("href", "/media/content/notes.docx");
    expect(download).toHaveAttribute("download");
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    [
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
    ],
    ["https://youtu.be/dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"],
    [
      "https://m.youtube.com/shorts/dQw4w9WgXcQ",
      "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
    ],
    ["https://vimeo.com/76979871", "https://player.vimeo.com/video/76979871"],
  ])("US-RA-11 AC3: a link to %s is an embedded player", async (link, player) => {
    mockContent({ kind: "external_media", external_url: link });

    const { container } = await renderPage();

    expect(screen.getByTitle("Odtwarzacz nagrania")).toHaveAttribute("src", player);
    expect(screen.queryByRole("link", { name: "Otwórz nagranie" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    "https://example.com/nagranie",
    "https://www.youtube.com/channel/abc",
    "https://vimeo.com/channels/staffpicks",
  ])("US-RA-11 AC3: a link to %s, which cannot be embedded, is a link", async (link) => {
    mockContent({ kind: "external_media", external_url: link });

    const { container } = await renderPage();

    expect(screen.getByRole("link", { name: "Otwórz nagranie" })).toHaveAttribute("href", link);
    expect(screen.queryByTitle("Odtwarzacz nagrania")).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC3: a text is read in the reader, its fragments highlighted", async () => {
    mockContent({ kind: "plain_text", document: 20 });

    const { container } = await renderPage();

    const text = card("Transkrypcja");
    const fragment = await within(text).findByRole("button", { name: "Fragment 01: Dezerter" });
    expect(within(text).getByText(/idzie przez las/)).toBeVisible();
    fireEvent.click(fragment);
    expect(within(text).getByRole("link", { name: "Dezerter" })).toHaveAttribute(
      "href",
      "/tags/dezerter",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC3: opened with ?fragment=, the reader scrolls to the fragment", async () => {
    mockContent({ kind: "plain_text", document: 20 });

    const { container } = await renderPage("/notes/3?fragment=30");

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Dezerter" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC3: opened from a search result, the reader highlights and scrolls to the match", async () => {
    mockContent({ kind: "ocr_text", document: 20 });

    await renderPage("/notes/3?q=las");

    const match = await screen.findByText("las", { selector: "mark" });
    expect(scrollIntoView.mock.contexts[0]).toBe(match);
  });

  it("shows the reader's loading state, then an error when the text cannot be loaded", async () => {
    mockContent({ kind: "plain_text", document: 20 });
    server.use(http.get(DOCUMENT_URL, () => new HttpResponse(null, { status: 500 })));

    await renderPage();

    expect(within(card("Transkrypcja")).getByRole("status")).toHaveTextContent("Wczytuję tekst…");
    expect(
      await screen.findByText("Nie udało się wczytać tekstu. Spróbuj ponownie później."),
    ).toBeVisible();
  });

  it("US-RA-11 AC3: 'Powiązane fragmenty' previews typescript fragments as cards, with no 'all' link", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Powiązane fragmenty");
    expect(within(fragments).getByText("2 z 5")).toBeVisible();
    expect(within(fragments).getAllByRole("article")).toHaveLength(2);
    expect(
      within(fragments).getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/1?fragment=5");
    expect(within(fragments).queryByText(/Wszystkie/)).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-11 AC4: 'Powiązane tagi' shows the tags, each linking to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const tags = column("Powiązane tagi");
    expect(within(tags).getByText("2")).toBeVisible();
    expect(
      within(tags)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Dezerter", "Pamięć"]);
    expect(within(tags).getByRole("link", { name: "Pamięć" })).toHaveAttribute(
      "href",
      "/tags/pamiec",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a note with no works, related fragments or tags renders none of those blocks", async () => {
    mockPage({ works: [], fragments: { items: [], total: 0 }, tags: [] });

    const { container } = await renderPage();

    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings).toEqual(["Notes 18 · karta 4"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-06: a note the API does not find shows the not-found page", async () => {
    server.use(http.get(PAGE_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/notes/3");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("an address that is not a note number shows the not-found page", () => {
    renderRoute("/notes/list");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(
      http.get(PAGE_URL, async () => {
        await delay(50);
        return new HttpResponse(null, { status: 500 });
      }),
    );

    renderRoute("/notes/3");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję zapisek…");
    expect(
      await screen.findByText("Nie udało się wczytać zapisku. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
