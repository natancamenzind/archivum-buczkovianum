import { fireEvent, screen, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "@/api/schema";
import { scrollIntoViewport, scrollOutOfViewport } from "@/test/intersection";
import { setViewport } from "@/test/media";
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
  header_image: "",
  header_image_alt: "",
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
      { id: 7, number: 3, scan_number: "19", shelfmark: "ML, sygn. 1618.19" },
      { id: 5, number: 1, scan_number: "9", shelfmark: "ML, sygn. 1618.9" },
    ],
    total: 3,
  },
  tags: [
    { slug: "wies", title: "Wieś" },
    { slug: "wojna", title: "Wojna" },
  ],
  materials: {
    texts: [
      { url: "/materialy/8", author: "", title: "Film dokumentalny", publication: "" },
      {
        url: "/teksty-sekundarne/4",
        author: "Jan Kowalski",
        title: "Recenzja „Wertepów”",
        publication: "Czytelnik, Warszawa 1948, s. 3",
      },
    ],
    visuals: [
      {
        url: "/materialy/9",
        title: "Autor w Dolinie",
        shelfmark: "ML, sygn. 1700",
        image: "/media/photo.jpg",
        image_alt: "Buczkowski przy biurku",
      },
      { url: "/materialy/11", title: "Plakat", shelfmark: "", image: "", image_alt: "" },
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
      scan_number: "9",
      shelfmark: "ML, sygn. 1618.9",
      tags: [{ slug: "wies", title: "Wieś" }],
    },
    {
      id: 6,
      start: 9,
      end: 15,
      number: 2,
      start_page: 1,
      scan_number: "",
      shelfmark: "",
      tags: [],
    },
    {
      id: 7,
      start: 24,
      end: 29,
      number: 3,
      start_page: 2,
      scan_number: "19",
      shelfmark: "ML, sygn. 1618.19",
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
  scan_number: "",
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

async function renderPage(url = "/maszynopisy/1") {
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
  const heading = screen.getByRole("heading", { name });
  const element = heading.parentElement?.parentElement;
  if (element == null) {
    throw new Error(`'${name}' heads no block.`);
  }
  return element;
}

function highlight(text: string): HTMLElement {
  return screen.getByRole("button", { name: text });
}

/** Scrolls to the end of the reader until every page has loaded (ARC-57 AC6). */
function loadAllPages(reader: HTMLElement) {
  for (
    let loading = reader.querySelector("[data-loading-page]");
    loading !== null;
    loading = reader.querySelector("[data-loading-page]")
  ) {
    scrollIntoViewport(loading);
  }
}

/** The text of each paragraph the reader shows. */
function paragraphs(reader: HTMLElement): (string | null)[] {
  return Array.from(reader.querySelectorAll("p.whitespace-pre-wrap"), (p) => p.textContent);
}

/** The tag notes of the fragments (ARC-57 AC2). */
function notes(reader: HTMLElement): HTMLElement[] {
  return Array.from(reader.querySelectorAll<HTMLElement>("[data-note]"));
}

function firstNote(): HTMLElement {
  const [note] = notes(card("Skan maszynopisu"));
  if (note === undefined) {
    throw new Error("The reader has no note.");
  }
  return note;
}

function pageElement(number: number): HTMLElement {
  const element = document.querySelector<HTMLElement>(`[data-page="${String(number)}"]`);
  if (element === null) {
    throw new Error(`Page ${String(number)} is not in the reader.`);
  }
  return element;
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
    expect(link).toHaveAttribute("href", "/utwory/wertepy");
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
    expect(links[1]).toHaveAttribute("href", "/maszynopisy/2");
    expect(within(typescripts).getByText("2")).toBeVisible();
  });

  it("US-RA-08 AC3: 'Skan maszynopisu' counts the pages and shows each scan page next to its text", async () => {
    mockPage();

    const { container } = await renderPage();

    const scan = card("Skan maszynopisu");
    expect(within(scan).getByText("2 strony")).toBeVisible();
    expect(await within(scan).findByText("Skan · strona 1 z 2")).toBeVisible();
    // ARC-57 AC8: the text is "Transkrypcja".
    expect(within(scan).getByText("Transkrypcja · strona 1 z 2")).toBeVisible();
    loadAllPages(scan);
    expect(within(scan).getByText("Skan · strona 2 z 2")).toBeVisible();
    // Before pdf.js draws it, a page keeps A4 proportions, so the reader does not jump.
    for (const page of within(scan).getAllByRole("img", { name: /Skan · strona/ })) {
      expect(page).toHaveStyle({ aspectRatio: "210 / 297" });
    }
    expect(paragraphs(scan)).toEqual(["Pierwsza strona tekstu. ", "Druga strona tekstu."]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-09 AC1: a long typescript is read whole, and only the scan pages in view are drawn", async () => {
    mockLongTypescript();

    const { container } = await renderPage();

    const scan = card("Skan maszynopisu");
    await within(scan).findByText("Skan · strona 1 z 40");
    loadAllPages(scan);
    expect(within(scan).getByText("Skan · strona 40 z 40")).toBeVisible();
    expect(paragraphs(scan)).toEqual(LONG_PAGES);
    // A fragment far into the text is highlighted on its own page.
    const fragment = within(scan).getByRole("button", { name: "Fragment 04: Strona" });
    expect(scan.querySelector('[data-page="38"]')).toContainElement(fragment);
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

    await renderPage("/maszynopisy/1?fragment=9");

    const fragment = await screen.findByRole("button", { name: "Fragment 04: Strona" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    // The pages before it are there; the next one waits to be scrolled to.
    expect(screen.getByText("Skan · strona 37 z 40")).toBeVisible();
    expect(screen.getByText("Wczytywanie strony 39 z 40…")).toBeVisible();
  });

  it("ARC-57 AC6: scrolling to the end of the last page loads only the next page, under a skeleton", async () => {
    mockLongTypescript();

    const { container } = await renderPage();

    const scan = card("Skan maszynopisu");
    const loading = await within(scan).findByText("Wczytywanie strony 2 z 40…");
    expect(loading).toHaveAttribute("role", "status");
    expect(scan.querySelectorAll("[data-page]")).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);

    scrollIntoViewport(loading.parentElement ?? loading);

    expect(within(scan).getByText("Skan · strona 2 z 40")).toBeVisible();
    expect(scan.querySelectorAll("[data-page]")).toHaveLength(2);
    expect(within(scan).getByText("Wczytywanie strony 3 z 40…")).toBeVisible();
  });

  it("ARC-57 AC6: a one-page text loads nothing more", async () => {
    mockPage({}, { page_offsets: [0] });

    await renderPage();

    await screen.findByText("Skan · strona 1 z 1");
    expect(screen.queryByText(/Wczytywanie strony/)).not.toBeInTheDocument();
    // One page needs no page field.
    expect(screen.queryByRole("textbox", { name: "Numer strony" })).not.toBeInTheDocument();
  });

  it("ARC-57 AC1: on desktop the view switch shows scan and text, text only or scan only", async () => {
    mockPage();

    const { container, router } = await renderPage();

    const views = await screen.findByRole("radiogroup", { name: "Widok" });
    const radios = within(views).getAllByRole("radio");
    expect(radios.map((radio) => radio.textContent)).toEqual([
      "Skan i transkrypcja",
      "Transkrypcja",
      "Skan",
    ]);
    expect(radios[0]).toHaveAttribute("aria-checked", "true");
    const scan = card("Skan maszynopisu");
    expect(within(scan).getByRole("img", { name: "Skan · strona 1 z 2" })).toBeVisible();
    expect(paragraphs(scan)).toEqual(["Pierwsza strona tekstu. "]);
    expect(await axeViolations(container)).toEqual([]);

    fireEvent.click(within(views).getByRole("radio", { name: "Transkrypcja" }));
    expect(within(scan).queryByRole("img", { name: /Skan · strona/ })).not.toBeInTheDocument();
    expect(paragraphs(scan)).toEqual(["Pierwsza strona tekstu. "]);
    expect(router.state.location.search).toBe("?widok=transkrypcja");

    fireEvent.click(within(views).getByRole("radio", { name: "Skan" }));
    expect(within(scan).getByRole("img", { name: "Skan · strona 1 z 2" })).toBeVisible();
    expect(paragraphs(scan)).toEqual([]);
    expect(router.state.location.search).toBe("?widok=skan");
    // AC2: the tags are there in every view.
    expect(within(scan).getByRole("link", { name: "Wieś" })).toBeVisible();
  });

  it("ARC-57 AC1: the view switch is a radio group the arrow keys move through", async () => {
    mockPage();

    await renderPage();

    const views = await screen.findByRole("radiogroup", { name: "Widok" });
    const both = within(views).getByRole("radio", { name: "Skan i transkrypcja" });
    expect(both).toHaveAttribute("tabindex", "0");
    expect(within(views).getByRole("radio", { name: "Skan" })).toHaveAttribute("tabindex", "-1");
    fireEvent.keyDown(both, { key: "ArrowRight" });
    const text = within(views).getByRole("radio", { name: "Transkrypcja" });
    expect(text).toHaveAttribute("aria-checked", "true");
    expect(text).toHaveFocus();
    fireEvent.keyDown(text, { key: "ArrowLeft" });
    fireEvent.keyDown(both, { key: "ArrowLeft" });
    expect(within(views).getByRole("radio", { name: "Skan" })).toHaveFocus();
    fireEvent.keyDown(views, { key: "a" });
    expect(within(views).getByRole("radio", { name: "Skan" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("ARC-57 AC1: the view comes from ?widok=, or else the one chosen last", async () => {
    mockPage();

    const first = await renderPage("/maszynopisy/1?widok=skan");
    expect(await screen.findByRole("radio", { name: "Skan" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    fireEvent.click(screen.getByRole("radio", { name: "Transkrypcja" }));
    first.unmount();

    await renderPage();
    expect(await screen.findByRole("radio", { name: "Transkrypcja" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("R-11 AC1: on mobile a Skan / Transkrypcja toggle switches the view", async () => {
    setViewport("mobile");
    mockPage();

    const { container } = await renderPage();

    const toggle = await screen.findByRole("group", { name: "Widok" });
    expect(screen.queryByRole("radiogroup")).not.toBeInTheDocument();
    const scan = within(toggle).getByRole("button", { name: "Skan" });
    const text = within(toggle).getByRole("button", { name: "Transkrypcja" });
    expect(text).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("img", { name: /Skan · strona/ })).not.toBeInTheDocument();
    fireEvent.click(scan);
    expect(scan).toHaveAttribute("aria-pressed", "true");
    expect(text).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("img", { name: "Skan · strona 1 z 2" })).toBeVisible();
    // Under the scan, the tags of the page's fragments.
    expect(notes(card("Skan maszynopisu"))[0]).toHaveTextContent(/^Wieś$/);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-57 AC2: each fragment's tags stand in a note on the margin, without its number", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    const note = notes(card("Skan maszynopisu"));
    // Fragment 02 has no tags, so it has no note; fragment 03 is on page 2.
    expect(note).toHaveLength(1);
    expect(note[0]).toHaveTextContent(/^Wieś$/);
    expect(within(firstNote()).getByRole("link", { name: "Wieś" })).toHaveAttribute(
      "href",
      "/tagi/wies",
    );
    // A screen reader reads a fragment's tags as its description.
    expect(fragment).toHaveAccessibleDescription("Wieś");
    expect(highlight("Fragment 02: strona")).not.toHaveAttribute("aria-describedby");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-57 AC2: hovering or focusing a fragment highlights its note", async () => {
    mockPage();

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    const note = firstNote();
    expect(note).not.toHaveClass("border-accent-border");
    fireEvent.mouseEnter(fragment);
    expect(note).toHaveClass("border-accent-border");
    fireEvent.mouseLeave(fragment);
    expect(note).not.toHaveClass("border-accent-border");
    fireEvent.focus(fragment);
    expect(note).toHaveClass("border-accent-border");
    fireEvent.blur(fragment);
    expect(note).not.toHaveClass("border-accent-border");
  });

  it("ARC-57 AC2: hovering or focusing a note highlights its fragment", async () => {
    mockPage();

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    const note = firstNote();
    fireEvent.mouseEnter(note);
    expect(fragment).toHaveAttribute("data-active");
    expect(highlight("Fragment 02: strona")).not.toHaveAttribute("data-active");
    fireEvent.mouseLeave(note);
    expect(fragment).not.toHaveAttribute("data-active");
    const tag = within(note).getByRole("link", { name: "Wieś" });
    fireEvent.focus(tag);
    expect(fragment).toHaveAttribute("data-active");
    // Focus moving within the note keeps the highlight; leaving the note ends it.
    fireEvent.blur(tag, { relatedTarget: note });
    expect(fragment).toHaveAttribute("data-active");
    fireEvent.blur(tag, { relatedTarget: document.body });
    expect(fragment).not.toHaveAttribute("data-active");
  });

  it("ARC-57 AC2: a fragment clicked or pressed stays highlighted", async () => {
    mockPage();

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(fragment).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(fragment);
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(notes(card("Skan maszynopisu"))[0]).toHaveClass("border-accent-border");
    fireEvent.keyDown(highlight("Fragment 02: strona"), { key: "Tab" });
    expect(highlight("Fragment 02: strona")).toHaveAttribute("aria-pressed", "false");
    fireEvent.keyDown(highlight("Fragment 02: strona"), { key: " " });
    expect(highlight("Fragment 02: strona")).toHaveAttribute("aria-pressed", "true");
    expect(fragment).toHaveAttribute("aria-pressed", "false");
  });

  it("R-11 AC2: of fragments with the same start, a click selects the inner one", async () => {
    const outer = { ...EXTRA_FRAGMENT, id: 8, start: 0, end: 15 };
    mockPage({}, { fragments: [...DOCUMENT.fragments, outer] });

    await renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Fragment 01: Pierwsza" }));

    expect(screen.getByRole("button", { name: "Fragment 01: Pierwsza" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Fragment 02: strona" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("ARC-57 AC2: notes are stacked in the margin in the order their fragments start", async () => {
    const second = {
      ...EXTRA_FRAGMENT,
      id: 11,
      start: 16,
      end: 22,
      tags: [{ slug: "pamiec", title: "Pamięć" }],
    };
    mockPage({}, { fragments: [second, ...DOCUMENT.fragments] });

    await renderPage();

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    const note = notes(card("Skan maszynopisu"));
    expect(note.map((element) => element.textContent)).toEqual(["Wieś", "Pamięć"]);
    // jsdom lays nothing out: every fragment starts at the top, so each note moves below the last.
    const wrappers = note.map((element) => element.parentElement);
    expect(wrappers[0]).toHaveStyle({ top: "0px" });
    expect(wrappers[1]).toHaveStyle({ top: "12px" });
  });

  it("ARC-57 AC2: on mobile a note stands under the paragraph its fragment starts in", async () => {
    setViewport("mobile");
    const text = "Pierwszy akapit.\n\nDrugi akapit, z fragmentem.";
    mockPage(
      {},
      {
        text,
        page_offsets: [0],
        fragments: [
          {
            ...EXTRA_FRAGMENT,
            id: 5,
            start: 18,
            end: 23,
            tags: [{ slug: "wies", title: "Wieś" }],
          },
        ],
      },
    );

    await renderPage();

    const fragment = await screen.findByRole("button", { name: "Fragment 04: Drugi" });
    const scan = card("Skan maszynopisu");
    expect(paragraphs(scan)).toEqual(["Pierwszy akapit.", "Drugi akapit, z fragmentem."]);
    const note = notes(scan)[0];
    expect(fragment.closest("p")?.nextElementSibling).toBe(note);
  });

  it("ARC-57 AC2: a text without fragments has no margin", async () => {
    mockPage({}, { fragments: [] });

    await renderPage();

    const scan = card("Skan maszynopisu");
    await within(scan).findByText("Skan · strona 1 z 2");
    expect(scan.querySelector("[data-for]")).toBeNull();
    expect(notes(scan)).toHaveLength(0);
  });

  it("R-11: a fragment reaching past the end of the text is highlighted up to the end", async () => {
    const past = { ...EXTRA_FRAGMENT, id: 9, start: 40, end: 99 };
    mockPage({}, { fragments: [...DOCUMENT.fragments, past] });

    await renderPage();
    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    loadAllPages(card("Skan maszynopisu"));

    expect(await screen.findByRole("button", { name: "Fragment 04: stu." })).toHaveTextContent(
      /^stu\.$/,
    );
  });

  it("R-11 AC3: opened with ?fragment=, the reader shows the text, scrolls to the fragment and selects it", async () => {
    localStorage.setItem("reader-view", "skan");
    mockPage();

    await renderPage("/maszynopisy/1?fragment=7");

    const fragment = await screen.findByRole("button", { name: "Fragment 03: Druga" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
    // A reader last set to the scan alone shows the text too.
    expect(screen.getByRole("radio", { name: "Skan i transkrypcja" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("R-11 AC3: opened from a search result with ?q=, the reader fills the search, highlights every match and scrolls to the first", async () => {
    mockPage();

    const { container } = await renderPage("/maszynopisy/1?q=Tekstu");

    const match = await screen.findByText("tekstu", { selector: "mark[aria-current]" });
    expect(match.textContent).toBe(TEXT.slice(16, 22));
    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView.mock.contexts[0]).toBe(match);
    // ARC-57 AC5: the search field holds the term and counts the matches.
    expect(screen.getByRole("searchbox", { name: "Szukaj w maszynopisie" })).toHaveValue("Tekstu");
    expect(screen.getByText("1 z 2")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11 AC3: a match inside a fragment is highlighted within it", async () => {
    mockPage();

    await renderPage("/maszynopisy/1?q=pierwsza");

    const fragment = await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(within(fragment).getByText("Pierwsza", { selector: "mark" })).toHaveAttribute(
      "data-search-match",
    );
  });

  it("R-11 AC3: a ?q= the text lacks scrolls nowhere", async () => {
    mockPage();

    await renderPage("/maszynopisy/1?q=potok");

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(scrollIntoView).not.toHaveBeenCalled();
    expect(screen.getByText("Brak trafień")).toBeVisible();
  });

  it("R-11 AC3: ?q= matches whole words only, not the start of a longer one", async () => {
    mockPage();

    const { container } = await renderPage("/maszynopisy/1?q=tekst");

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(container.querySelector("mark[data-search-match]")).toBeNull();
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("R-11 AC3: a ?q= of regular expression characters is matched literally", async () => {
    mockPage();

    const { container } = await renderPage(`/maszynopisy/1?q=${encodeURIComponent(".*")}`);

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(container.querySelector("mark[data-search-match]")).toBeNull();
  });

  it("ARC-57 AC5: the search in the typescript counts the matches and moves between them", async () => {
    mockPage();

    await renderPage();

    const field = await screen.findByRole("searchbox", { name: "Szukaj w maszynopisie" });
    fireEvent.change(field, { target: { value: "strona" } });
    expect(screen.getByText("1 z 2")).toBeVisible();
    const first = screen.getByText("strona", { selector: "mark[aria-current]" });
    expect(scrollIntoView.mock.contexts.at(-1)).toBe(first);

    // The second match is on page 2, which loads to show it.
    fireEvent.keyDown(field, { key: "Enter" });
    expect(screen.getByText("2 z 2")).toBeVisible();
    const second = screen.getByText("strona", { selector: "mark[aria-current]" });
    expect(screen.getByText("Skan · strona 2 z 2")).toBeVisible();
    expect(scrollIntoView.mock.contexts.at(-1)).toBe(second);

    fireEvent.keyDown(field, { key: "Enter" });
    expect(screen.getByText("1 z 2")).toBeVisible();
    fireEvent.keyDown(field, { key: "Enter", shiftKey: true });
    expect(screen.getByText("2 z 2")).toBeVisible();
    fireEvent.keyDown(field, { key: "ArrowUp" });
    expect(screen.getByText("1 z 2")).toBeVisible();
    fireEvent.keyDown(field, { key: "ArrowDown" });
    expect(screen.getByText("2 z 2")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Poprzednie trafienie" }));
    expect(screen.getByText("1 z 2")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Następne trafienie" }));
    expect(screen.getByText("2 z 2")).toBeVisible();

    fireEvent.keyDown(field, { key: "Escape" });
    expect(field).toHaveValue("");
    expect(screen.queryByText("2 z 2")).not.toBeInTheDocument();
    expect(document.querySelector("mark[data-search-match]")).toBeNull();
  });

  it("ARC-57 AC5: the clear button empties the search; with no match there is nowhere to move", async () => {
    mockPage();

    await renderPage();

    const field = await screen.findByRole("searchbox", { name: "Szukaj w maszynopisie" });
    fireEvent.change(field, { target: { value: "potok" } });
    expect(screen.getByText("Brak trafień")).toBeVisible();
    expect(screen.getByRole("button", { name: "Następne trafienie" })).toBeDisabled();
    fireEvent.keyDown(field, { key: "Enter" });
    expect(scrollIntoView).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Wyczyść wyszukiwanie" }));
    expect(field).toHaveValue("");
  });

  it("ARC-57 AC4: the page field follows the page in view and keeps it in the address", async () => {
    mockPage();

    const { container, router } = await renderPage();

    const field = await screen.findByRole("textbox", { name: "Numer strony" });
    expect(field).toHaveValue("1");
    expect(screen.getByText("z 2")).toBeVisible();
    expect(screen.getByRole("button", { name: "Poprzednia strona" })).toBeDisabled();
    loadAllPages(card("Skan maszynopisu"));

    scrollIntoViewport(pageElement(2));
    expect(field).toHaveValue("2");
    expect(router.state.location.search).toBe("?strona=2");
    expect(screen.getByRole("button", { name: "Następna strona" })).toBeDisabled();
    scrollOutOfViewport(pageElement(2));
    expect(field).toHaveValue("2");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-57 AC4: a page number or an arrow goes to that page", async () => {
    mockPage();

    const { router } = await renderPage();

    const field = await screen.findByRole("textbox", { name: "Numer strony" });
    fireEvent.change(field, { target: { value: "2" } });
    fireEvent.keyDown(field, { key: "Enter" });
    expect(field).toHaveValue("2");
    expect(router.state.location.search).toBe("?strona=2");
    expect(scrollIntoView.mock.contexts.at(-1)).toBe(pageElement(2));

    fireEvent.click(screen.getByRole("button", { name: "Poprzednia strona" }));
    expect(field).toHaveValue("1");
    expect(scrollIntoView.mock.contexts.at(-1)).toBe(pageElement(1));
    fireEvent.click(screen.getByRole("button", { name: "Następna strona" }));
    expect(field).toHaveValue("2");

    // Esc gives up a number being typed; leaving the field does too.
    fireEvent.change(field, { target: { value: "1" } });
    fireEvent.keyDown(field, { key: "Escape" });
    expect(field).toHaveValue("2");
    fireEvent.change(field, { target: { value: "1" } });
    fireEvent.blur(field);
    expect(field).toHaveValue("2");
    fireEvent.keyDown(field, { key: "Enter" });
    expect(field).toHaveValue("2");
  });

  it("ARC-57 AC4: a number out of range says which numbers there are", async () => {
    mockPage();

    const { container } = await renderPage();

    const field = await screen.findByRole("textbox", { name: "Numer strony" });
    fireEvent.change(field, { target: { value: "5" } });
    fireEvent.keyDown(field, { key: "Enter" });
    expect(screen.getByRole("alert")).toHaveTextContent("Podaj numer od 1 do 2");
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(field).toHaveAccessibleDescription("Podaj numer od 1 do 2");
    // The number stays to be corrected, also when the field is left.
    fireEvent.blur(field);
    expect(field).toHaveValue("5");
    expect(await axeViolations(container)).toEqual([]);
    fireEvent.change(field, { target: { value: "2" } });
    fireEvent.keyDown(field, { key: "Enter" });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("ARC-57 AC4: ?strona= opens the reader at that page", async () => {
    mockLongTypescript();

    await renderPage("/maszynopisy/1?strona=12");

    expect(await screen.findByRole("textbox", { name: "Numer strony" })).toHaveValue("12");
    expect(scrollIntoView.mock.contexts[0]).toBe(pageElement(12));
  });

  it("ARC-57 AC3: the zoom opens a scan page on the whole screen, and Esc returns to the page", async () => {
    mockPage();

    const { router } = await renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Powiększ skan strony 1" }));
    const zoom = screen.getByRole("dialog", { name: "Skan · strona 1 z 2" });
    expect(zoom).toHaveAccessibleDescription(/Esc zamyka$/);
    expect(within(zoom).getByText("100%")).toBeVisible();
    fireEvent.click(within(zoom).getByRole("button", { name: "Powiększ" }));
    expect(within(zoom).getByText("125%")).toBeVisible();
    fireEvent.click(within(zoom).getByRole("button", { name: "Pomniejsz" }));
    fireEvent.click(within(zoom).getByRole("button", { name: "Pomniejsz" }));
    expect(within(zoom).getByText("80%")).toBeVisible();
    fireEvent.click(within(zoom).getByRole("button", { name: "Dopasuj do okna" }));
    expect(within(zoom).getByText("100%")).toBeVisible();
    expect(await axeViolations(zoom)).toEqual([]);

    // The arrows change the page.
    expect(within(zoom).getByRole("button", { name: "Poprzednia strona" })).toBeDisabled();
    fireEvent.keyDown(zoom, { key: "ArrowRight" });
    expect(screen.getByRole("dialog", { name: "Skan · strona 2 z 2" })).toBeVisible();
    expect(within(zoom).getByRole("button", { name: "Następna strona" })).toBeDisabled();
    fireEvent.keyDown(zoom, { key: "ArrowRight" });
    fireEvent.keyDown(zoom, { key: "ArrowLeft" });
    fireEvent.click(within(zoom).getByRole("button", { name: "Następna strona" }));
    expect(screen.getByRole("dialog", { name: "Skan · strona 2 z 2" })).toBeVisible();

    fireEvent.keyDown(zoom, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    // The reader is at the page shown last, with the focus on its zoom button.
    expect(screen.getByRole("button", { name: "Powiększ skan strony 2" })).toHaveFocus();
    expect(scrollIntoView.mock.contexts.at(-1)).toBe(pageElement(2));
    expect(router.state.location.search).toBe("?strona=2");
  });

  it("ARC-57 AC3: a click on the scan opens the zoom too, and its button closes it", async () => {
    mockPage();

    await renderPage();

    fireEvent.click(await screen.findByRole("img", { name: "Skan · strona 1 z 2" }));
    const zoom = screen.getByRole("dialog", { name: "Skan · strona 1 z 2" });
    const view = zoom.querySelector("canvas")?.parentElement;
    if (view == null) {
      throw new Error("The zoom has no scan.");
    }
    // Dragging moves the page.
    view.setPointerCapture = vi.fn();
    fireEvent.pointerDown(view, { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(view, { clientX: 60, clientY: 70 });
    expect(view.scrollLeft).toBe(40);
    expect(view.scrollTop).toBe(30);
    fireEvent.pointerUp(view);
    fireEvent.pointerMove(view, { clientX: 0, clientY: 0 });
    expect(view.scrollLeft).toBe(40);
    // Ctrl with the wheel, as a pinch on a trackpad, zooms.
    fireEvent.wheel(view, { deltaY: -1, ctrlKey: true });
    expect(within(zoom).getByText("125%")).toBeVisible();
    fireEvent.wheel(view, { deltaY: 1, ctrlKey: true });
    fireEvent.wheel(view, { deltaY: 1 });
    expect(within(zoom).getByText("100%")).toBeVisible();

    fireEvent.click(within(zoom).getByRole("button", { name: "Zamknij powiększenie" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Powiększ skan strony 1" })).toHaveFocus();
  });

  it("US-RA-08 AC3: 'Fragmenty z maszynopisu' previews the fragments as a numbered list", async () => {
    mockPage();

    const { container } = await renderPage();

    const fragments = card("Fragmenty z maszynopisu");
    expect(within(fragments).getByText("2 z 3")).toBeVisible();
    const links = within(fragments).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "03Fragment 03 · skan 19 · ML, sygn. 1618.19",
      "01Fragment 01 · skan 9 · ML, sygn. 1618.9",
      "Wszystkie fragmenty (3)",
    ]);
    expect(links[0]).toHaveAttribute("href", "/maszynopisy/1?fragment=7");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-08 AC3: a fragment in the list opens it in the reader", async () => {
    mockPage();

    await renderPage();
    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });

    fireEvent.click(
      within(card("Fragmenty z maszynopisu")).getByRole("link", { name: /Fragment 03/ }),
    );

    const fragment = await screen.findByRole("button", { name: "Fragment 03: Druga" });
    expect(fragment).toHaveAttribute("aria-pressed", "true");
    expect(scrollIntoView.mock.contexts[0]).toBe(fragment);
  });

  it("ARC-53: 'Wszystkie fragmenty (3)' is set like a fragment's quote", async () => {
    mockPage();

    await renderPage();

    expect(
      within(card("Fragmenty z maszynopisu")).getByRole("link", {
        name: "Wszystkie fragmenty (3)",
      }),
    ).toHaveClass("text-lora-tekst", "text-foreground");
  });

  it("D20: 'Wszystkie fragmenty (3)' expands the list in place, in page order", async () => {
    mockPage();

    await renderPage();
    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });

    fireEvent.click(screen.getByRole("link", { name: "Wszystkie fragmenty (3)" }));

    const fragments = card("Fragmenty z maszynopisu");
    expect(await within(fragments).findByText("3")).toBeVisible();
    const links = within(fragments).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "01Fragment 01 · skan 9 · ML, sygn. 1618.9",
      "02Fragment 02",
      "03Fragment 03 · skan 19 · ML, sygn. 1618.19",
    ]);
    expect(links[0]).toHaveFocus();
    // Opening a fragment keeps the list expanded.
    expect(links[1]).toHaveAttribute("href", "/maszynopisy/1?fragments=all&fragment=6");
  });

  it("D20: while the whole list loads, the preview stays, without the link", async () => {
    server.use(
      http.get(TYPESCRIPT_URL, () => HttpResponse.json(TYPESCRIPT)),
      http.get(DOCUMENT_URL, async () => {
        await delay("infinite");
        return HttpResponse.json(DOCUMENT);
      }),
    );

    await renderPage("/maszynopisy/1?fragments=all");

    const fragments = card("Fragmenty z maszynopisu");
    expect(within(fragments).getByText("2 z 3")).toBeVisible();
    expect(within(fragments).queryByText(/Wszystkie fragmenty/)).not.toBeInTheDocument();
  });

  it("D20: ?fragments=all, the work page's link, opens the page with the list expanded", async () => {
    mockPage();

    await renderPage("/maszynopisy/1?fragments=all");

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
    expect(within(tags).getByRole("link", { name: "Wieś" })).toHaveAttribute("href", "/tagi/wies");
    expect(within(tags).getByRole("link", { name: "Wojna" })).toHaveAttribute(
      "href",
      "/tagi/wojna",
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
    expect(within(texts).getAllByRole("link")[1]).toHaveAttribute("href", "/teksty-sekundarne/4");
    const visuals = column("Materiały wizualne");
    const photo = within(visuals).getByRole("link", { name: /Autor w Dolinie/ });
    expect(photo).toHaveAttribute("href", "/materialy/9");
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
    // ARC-57 AC7: the typescripts under the hero, then the reader.
    expect(headings).toEqual([TYPESCRIPT.title, "Maszynopisy utworu", "Skan maszynopisu"]);
    expect(screen.queryByRole("button", { name: "Fragment 01: Pierwsza" })).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-11: a plain text is shown as text, without scans or the toggle", async () => {
    mockPage({}, { kind: "plain", page_offsets: [] });

    await renderPage();

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    // ARC-57: no view switch, page field or zoom; the search stays.
    expect(screen.queryByRole("radiogroup", { name: "Widok" })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Numer strony" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Powiększ skan/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/strona/, { selector: "p.text-cousine-metadane-male" })).toBeNull();
    expect(screen.getByRole("searchbox", { name: "Szukaj w maszynopisie" })).toBeVisible();
  });

  it("R-11: on mobile a plain text has no toggle", async () => {
    setViewport("mobile");
    mockPage({}, { kind: "plain", page_offsets: [] });

    await renderPage();

    await screen.findByRole("button", { name: "Fragment 01: Pierwsza" });
    expect(screen.queryByRole("group", { name: "Widok" })).not.toBeInTheDocument();
  });

  it("R-11: a scan that cannot be loaded says so", async () => {
    mockPage({}, { scan: "/media/scans/missing.pdf" });
    server.use(
      http.get("*/media/scans/missing.pdf", () => new HttpResponse(null, { status: 404 })),
    );

    await renderPage("/maszynopisy/1?fragment=7");

    expect(await screen.findByText("Nie udało się wczytać skanu.")).toBeVisible();
    // The text, now at full width, is scrolled to the fragment again.
    expect(scrollIntoView).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("img", { name: /Skan · strona/ })).not.toBeInTheDocument();
    // The reader shows the text, without a view switch to the missing scan.
    expect(screen.queryByRole("radiogroup", { name: "Widok" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fragment 01: Pierwsza" })).toBeVisible();
  });

  it("R-06: a typescript the API does not find shows the not-found page", async () => {
    server.use(http.get(TYPESCRIPT_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/maszynopisy/1");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("an address that is not a typescript number shows the not-found page", () => {
    renderRoute("/maszynopisy/wertepy");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(TYPESCRIPT_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/maszynopisy/1");

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
