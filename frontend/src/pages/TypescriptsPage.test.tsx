import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type TypescriptGroup = components["schemas"]["TypescriptGroup"];

const TYPESCRIPTS_URL = "*/api/typescripts/";

// In the API's order: works by first edition, typescripts by shelfmark.
const GROUPS: TypescriptGroup[] = [
  {
    slug: "wertepy",
    title: "Wertepy",
    genre: "powieść",
    year: 1947,
    typescripts: [
      { id: 1, title: "Pierwsza wersja", shelfmark: "ML, sygn. 1618" },
      { id: 2, title: "Druga wersja", shelfmark: "ML, sygn. 1619" },
    ],
  },
  {
    slug: "czarny-potok",
    title: "Czarny potok",
    genre: "",
    year: null,
    typescripts: [{ id: 3, title: "Maszynopis", shelfmark: "" }],
  },
];

function mockTypescripts(groups: TypescriptGroup[] = GROUPS): void {
  server.use(http.get(TYPESCRIPTS_URL, () => HttpResponse.json(groups)));
}

function group(title: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name: title });
  const card = heading.closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error(`'${title}' is not inside a card.`);
  }
  return card;
}

function rows(title: string): HTMLElement[] {
  return within(group(title)).getAllByRole("listitem");
}

describe("TypescriptsPage", () => {
  it("US-RA-19 AC1: 'Maszynopisy' in the main navigation opens the list and is the active item", async () => {
    mockTypescripts();
    const { container } = renderRoute("/");

    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    fireEvent.click(within(nav).getByRole("link", { name: "Maszynopisy" }));

    expect(await screen.findByRole("heading", { level: 2, name: "Wertepy" })).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Maszynopisy" })).toBeVisible();
    expect(within(nav).getByRole("link", { name: "Maszynopisy" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-19: the hero shows the label, the title 'Maszynopisy' and the description", async () => {
    mockTypescripts();

    const { container } = renderRoute("/typescripts");

    const title = screen.getByRole("heading", { level: 1, name: "Maszynopisy" });
    const hero = title.closest<HTMLElement>("[data-slot=page-header]");
    if (hero === null) {
      throw new Error("The title is not inside the hero.");
    }
    expect(within(hero).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(
      within(hero).getByText(
        "Jednostki archiwalne z maszynopisami utworów, pogrupowane według utworu.",
      ),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-19 AC2: one group per work, in the API's order", async () => {
    mockTypescripts();

    const { container } = renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(["Wertepy", "Czarny potok"]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-19 AC2: the group header shows the work's genre, year and count", async () => {
    mockTypescripts();

    renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    expect(within(group("Wertepy")).getByText("powieść · 1947")).toBeVisible();
    expect(within(group("Wertepy")).getByText("2")).toBeVisible();
    expect(within(group("Czarny potok")).getByText("1")).toBeVisible();
  });

  it("R-02: a work without genre and year shows no description line", async () => {
    mockTypescripts();

    renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Czarny potok" });
    // Title, count and the one card: nothing between them.
    expect(group("Czarny potok")).toHaveTextContent(/^Czarny potok101Maszynopis$/);
  });

  it("US-RA-19 AC2: each card shows its number, title and shelfmark", async () => {
    mockTypescripts();

    renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    const [first, second] = rows("Wertepy");
    expect(first).toHaveTextContent("01Pierwsza wersja, ML, sygn. 1618");
    expect(second).toHaveTextContent("02Druga wersja, ML, sygn. 1619");
    // Without a shelfmark only the title is shown (R-02).
    expect(rows("Czarny potok")[0]).toHaveTextContent(/^01Maszynopis$/);
  });

  it("US-RA-19 AC2: each card opens the typescript page", async () => {
    mockTypescripts();

    renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    const links = [...rows("Wertepy"), ...rows("Czarny potok")].map((row) =>
      within(row).getByRole("link"),
    );
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/typescripts/1",
      "/typescripts/2",
      "/typescripts/3",
    ]);
    expect(links[0]).toHaveAccessibleName("Pierwsza wersja, ML, sygn. 1618");
  });

  it("US-RA-19 AC2: two cards per row on desktop, one column on mobile", async () => {
    mockTypescripts();

    renderRoute("/typescripts");

    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    const grid = group("Wertepy").closest("ul");
    expect(grid).toHaveClass("grid-cols-1", "md:grid-cols-2");
    expect(group("Wertepy")).toHaveClass("p-card-mobile", "md:p-card");
  });

  it("R-02: without published typescripts no group is shown", async () => {
    mockTypescripts([]);

    renderRoute("/typescripts");

    await waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(screen.getByRole("heading", { level: 1, name: "Maszynopisy" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
  });

  it("says it is loading, then shows the list", async () => {
    mockTypescripts();

    const { container } = renderRoute("/typescripts");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję maszynopisy…");
    expect(await axeViolations(container)).toEqual([]);
    await screen.findByRole("heading", { level: 2, name: "Wertepy" });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says so when the API fails, keeping the title", async () => {
    server.use(http.get(TYPESCRIPTS_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/typescripts");

    expect(
      await screen.findByText("Nie udało się wczytać maszynopisów. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Maszynopisy" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });
});
