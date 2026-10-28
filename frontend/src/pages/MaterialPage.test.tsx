import { fireEvent, screen, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type MaterialData = components["schemas"]["MaterialPage"];
type Content = components["schemas"]["MediaContent"];
type Document = components["schemas"]["Document"];
type Fragment = components["schemas"]["FragmentCard"];

const PAGE_URL = "*/api/materials/4/";
const DOCUMENT_URL = "*/api/documents/21/";

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

const MATERIAL: MaterialData = {
  id: 4,
  title: "Buczkowski w Konstancinie",
  description: "<p>Fotografia z lat sześćdziesiątych.</p>",
  shelfmark: "ML, sygn. 1700",
  content: {
    ...NO_CONTENT,
    image: "/media/content/photo.jpg",
    image_alt: "Pisarz przy biurku",
  },
  works: [
    { slug: "wertepy", title: "Wertepy", year: 1947, fragment_count: 24 },
    { slug: "czarny-potok", title: "Czarny potok", year: null, fragment_count: 0 },
  ],
  fragments: {
    items: [FRAGMENT, { ...FRAGMENT, id: 6, url: "/typescripts/2?fragment=6", number: 2 }],
    total: 5,
  },
  tags: [
    { slug: "las", title: "Las" },
    { slug: "pamiec", title: "Pamięć" },
  ],
};

const DOCUMENT: Document = {
  id: 21,
  kind: "plain",
  text: "Dezerter idzie przez las.",
  page_offsets: [],
  scan: "",
  fragments: [
    {
      id: 31,
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

function mockPage(page: Partial<MaterialData> = {}) {
  server.use(
    http.get(PAGE_URL, () => HttpResponse.json({ ...MATERIAL, ...page })),
    http.get(DOCUMENT_URL, () => HttpResponse.json(DOCUMENT)),
  );
}

function mockContent(content: Partial<Content>) {
  mockPage({ content: { ...NO_CONTENT, ...content } });
}

async function renderPage(url = "/materials/4") {
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

describe("MaterialPage", () => {
  const scrollIntoView = vi.fn();

  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoView;
  });

  afterEach(() => {
    scrollIntoView.mockReset();
    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("US-RA-12 AC1: the hero shows the kind and shelfmark, the title and the description", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(
      within(hero()).getByRole("heading", { level: 1, name: "Buczkowski w Konstancinie" }),
    ).toBeVisible();
    expect(within(hero()).getByText("Materiał wizualny · ML, sygn. 1700")).toBeVisible();
    expect(within(hero()).getByText("Fotografia z lat sześćdziesiątych.")).toBeVisible();
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).queryByRole("link", { current: "page" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    ["document", "Dokument"],
    ["external_media", "Nagranie"],
    ["ocr_text", "Skan z transkrypcją"],
    ["plain_text", "Tekst lity"],
  ] as const)(
    "US-RA-12 AC1: a %s material without shelfmark or description shows '%s' and the title (R-02)",
    async (kind, label) => {
      mockPage({ shelfmark: "", description: "", content: { ...NO_CONTENT, kind } });

      await renderPage();

      expect(within(hero()).getByText(label)).toBeVisible();
      expect(hero().querySelectorAll("p")).toHaveLength(1);
    },
  );

  it("US-RA-12 AC2: 'Powiązane utwory' lists the related works with year, each linking to it", async () => {
    mockPage();

    const { container } = await renderPage();

    const works = column("Powiązane utwory");
    const links = within(works).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["1947Wertepy", "Czarny potok"]);
    expect(links[0]).toHaveAttribute("href", "/works/wertepy");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-12 AC3: an image is shown inline with its text alternative", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(screen.getByRole("img", { name: "Pisarz przy biurku" })).toHaveAttribute(
      "src",
      "/media/content/photo.jpg",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-12 AC3: a recording on Vimeo is an embedded player", async () => {
    mockContent({ kind: "external_media", external_url: "https://vimeo.com/76979871" });

    const { container } = await renderPage();

    expect(screen.getByTitle("Odtwarzacz nagrania")).toHaveAttribute(
      "src",
      "https://player.vimeo.com/video/76979871",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-12 AC3: a document that is not a PDF is a download", async () => {
    mockContent({ kind: "document", file: "/media/content/clipping.docx" });

    await renderPage();

    expect(screen.getByRole("link", { name: "Pobierz plik" })).toHaveAttribute(
      "href",
      "/media/content/clipping.docx",
    );
  });

  it("US-RA-12 AC3: an OCR text is read in the reader, its fragments highlighted", async () => {
    mockContent({ kind: "ocr_text", document: 21 });

    const { container } = await renderPage();

    const text = card("Transkrypcja");
    const fragment = await within(text).findByRole("button", { name: "Fragment 01: Dezerter" });
    fireEvent.click(fragment);
    expect(within(text).getByRole("link", { name: "Dezerter" })).toHaveAttribute(
      "href",
      "/tags/dezerter",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-12 AC3: opened from a search result, the reader highlights and scrolls to the match", async () => {
    mockContent({ kind: "ocr_text", document: 21 });

    await renderPage("/materials/4?q=las");

    const match = await screen.findByText("las", { selector: "mark" });
    expect(scrollIntoView.mock.contexts[0]).toBe(match);
  });

  it("US-RA-12 AC3: 'Powiązane fragmenty' previews typescript fragments as cards, with no 'all' link", async () => {
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

  it("US-RA-12 AC4: 'Powiązane tagi' shows the tags, each linking to its page", async () => {
    mockPage();

    const { container } = await renderPage();

    const tags = column("Powiązane tagi");
    expect(
      within(tags)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Las", "Pamięć"]);
    expect(within(tags).getByRole("link", { name: "Las" })).toHaveAttribute("href", "/tags/las");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a material with no works, related fragments or tags renders none of those blocks", async () => {
    mockPage({ works: [], fragments: { items: [], total: 0 }, tags: [] });

    const { container } = await renderPage();

    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings).toEqual(["Buczkowski w Konstancinie"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-06: a material the API does not find shows the not-found page", async () => {
    server.use(http.get(PAGE_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/materials/4");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("an address that is not a material number shows the not-found page", () => {
    renderRoute("/materials/list");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(
      http.get(PAGE_URL, async () => {
        await delay(50);
        return new HttpResponse(null, { status: 500 });
      }),
    );

    renderRoute("/materials/4");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję materiał kontekstowy…");
    expect(
      await screen.findByText(
        "Nie udało się wczytać materiału kontekstowego. Spróbuj ponownie później.",
      ),
    ).toBeVisible();
  });
});
