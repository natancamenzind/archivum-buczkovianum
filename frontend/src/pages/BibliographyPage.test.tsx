import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type BibliographyData = components["schemas"]["BibliographyPage"];

const BIBLIOGRAPHY_URL = "*/api/works/wertepy/bibliography/";

const ENTRIES = Array.from(
  { length: 12 },
  (_, index) => `Jan Kowalski, Recenzja ${String(index + 1)}, „Twórczość” 1948, nr 3`,
);

const BIBLIOGRAPHY: BibliographyData = {
  slug: "wertepy",
  is_draft: false,
  title: "Wertepy",
  entries: ENTRIES,
  works: [
    { slug: "czarny-potok", title: "Czarny potok", year: 1932 },
    { slug: "wertepy", title: "Wertepy", year: 1947 },
    { slug: "bez-wydan", title: "Bez wydań", year: null },
  ],
};

function mockPage(bibliography: Partial<BibliographyData> = {}) {
  server.use(
    http.get(BIBLIOGRAPHY_URL, () => HttpResponse.json({ ...BIBLIOGRAPHY, ...bibliography })),
  );
}

async function renderPage() {
  const result = renderRoute("/utwory/wertepy/bibliografia");
  await screen.findByRole("heading", { level: 1, name: "Wertepy" });
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

function bibliographyCard(): HTMLElement {
  const card = screen
    .getByRole("heading", { level: 2, name: "Bibliografia" })
    .closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error("'Bibliografia' is not inside a card.");
  }
  return card;
}

describe("BibliographyPage", () => {
  it("US-RA-21 AC2: the hero shows the type line and the work's title; Utwory is active", async () => {
    mockPage();

    const { container } = await renderPage();

    expect(within(hero()).getByText("Bibliografia utworu · Leopold Buczkowski")).toBeVisible();
    expect(hero().querySelectorAll("p")).toHaveLength(1);
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).getByRole("link", { name: "Utwory" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-21 AC3: the card lists every entry, numbered, in order, with the count", async () => {
    mockPage();

    const { container } = await renderPage();

    const card = bibliographyCard();
    // The count, not the twelfth entry's number.
    expect(within(card).getByText("12", { selector: "p" })).toBeVisible();
    expect(
      within(card)
        .getAllByRole("listitem")
        .map((entry) => entry.textContent),
    ).toEqual(ENTRIES.map((text, index) => `${String(index + 1).padStart(2, "0")}${text}`));
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-21 AC4: 'Bibliografie utworów' links every work's bibliography, the current one highlighted, without the year", async () => {
    mockPage();

    const { container } = await renderPage();

    const works = screen.getByRole("navigation", { name: "Bibliografie utworów" });
    expect(within(works).getByText("3")).toBeVisible();
    const links = within(works).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Bibliografia do utworu „Czarny potok”", "/utwory/czarny-potok/bibliografia"],
      ["Bibliografia do utworu „Wertepy”", "/utwory/wertepy/bibliografia"],
      ["Bibliografia do utworu „Bez wydań”", "/utwory/bez-wydan/bibliografia"],
    ]);
    expect(links.map((link) => link.getAttribute("aria-current"))).toEqual([null, "page", null]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-21 AC4: on mobile the works come after the card", async () => {
    mockPage();

    await renderPage();

    const works = screen.getByRole("navigation", { name: "Bibliografie utworów" });
    expect(
      bibliographyCard().compareDocumentPosition(works) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("R-02: without other works' bibliographies the column is not rendered", async () => {
    mockPage({ works: [] });

    await renderPage();

    expect(
      screen.queryByRole("navigation", { name: "Bibliografie utworów" }),
    ).not.toBeInTheDocument();
  });

  it("US-WR-13 AC2: a draft that staff preview shows the draft banner", async () => {
    mockPage({ is_draft: true });

    const { container } = await renderPage();

    expect(screen.getByText("Szkic — niewidoczny publicznie")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-21 AC5: a bibliography the API does not find shows the not-found page", async () => {
    server.use(http.get(BIBLIOGRAPHY_URL, () => new HttpResponse(null, { status: 404 })));

    renderRoute("/utwory/wertepy/bibliografia");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Nie znaleziono strony" }),
    ).toBeVisible();
  });

  it("shows the loading state, then an error when the page cannot be loaded", async () => {
    server.use(http.get(BIBLIOGRAPHY_URL, () => new HttpResponse(null, { status: 500 })));

    renderRoute("/utwory/wertepy/bibliografia");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję bibliografię…");
    expect(
      await screen.findByText("Nie udało się wczytać bibliografii. Spróbuj ponownie później."),
    ).toBeVisible();
  });
});
