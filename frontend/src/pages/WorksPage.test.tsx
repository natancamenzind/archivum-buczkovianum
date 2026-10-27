import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type Work = components["schemas"]["WorkCard"];

const WORKS_URL = "*/api/works/";

function work(slug: string, title: string, year: number | null, fragments: number): Work {
  return {
    slug,
    title,
    genre: "powieść",
    year,
    cover_image: "",
    cover_image_alt: "",
    fragment_count: fragments,
  };
}

// In the API's order: by first edition, a work without editions last.
const WORKS: Work[] = [
  work("wertepy", "Wertepy", 1947, 1),
  work("czarny-potok", "Czarny potok", 1954, 2),
  work("dorycki-kruzganek", "Dorycki krużganek", 1957, 5),
  work("pierwsza-swietnosc", "Pierwsza świetność", null, 0),
];

function mockWorks(works: Work[] = WORKS): void {
  server.use(http.get(WORKS_URL, () => HttpResponse.json(works)));
}

function section(): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name: "Wszystkie utwory" });
  const card = heading.closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error("'Wszystkie utwory' is not inside a card.");
  }
  return card;
}

function workCards(): HTMLElement[] {
  return within(section()).getAllByRole("listitem");
}

describe("WorksPage", () => {
  it("US-RA-18 AC1: 'Utwory' in the main navigation opens the list and is the active item", async () => {
    mockWorks();
    const { container } = renderRoute("/");

    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    fireEvent.click(within(nav).getByRole("link", { name: "Utwory" }));

    expect(
      await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" }),
    ).toBeVisible();
    expect(within(nav).getByRole("link", { name: "Utwory" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(nav.querySelectorAll('[aria-current="page"]')).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-18: the hero shows the label, the title 'Utwory' and the description", async () => {
    mockWorks();

    const { container } = renderRoute("/works");

    const title = screen.getByRole("heading", { level: 1, name: "Utwory" });
    const hero = title.closest<HTMLElement>("[data-slot=page-header]");
    if (hero === null) {
      throw new Error("The title is not inside the hero.");
    }
    expect(within(hero).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(
      within(hero).getByText(
        "Wszystkie utwory Leopolda Buczkowskiego w archiwum, w kolejności wydania.",
      ),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-18 AC2: the cards come in the API's order, with the count in the section header", async () => {
    mockWorks();

    const { container } = renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const titles = workCards().map(
      (card) => within(card).getByRole("heading", { level: 3 }).textContent,
    );
    expect(titles).toEqual(["Wertepy", "Czarny potok", "Dorycki krużganek", "Pierwsza świetność"]);
    expect(within(section()).getByText("4")).toBeVisible();
    expect(within(section()).getByText("W kolejności wydania")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-18 AC2: fragment counts use the right plural for 1, 2 and 5", async () => {
    mockWorks();

    renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const [first, second, third] = workCards();
    expect(first).toHaveTextContent("1 fragment");
    expect(second).toHaveTextContent("2 fragmenty");
    expect(third).toHaveTextContent("5 fragmentów");
  });

  it("D23: a work with 0 fragments shows no count", async () => {
    mockWorks();

    renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const last = workCards().at(-1);
    expect(last).toHaveTextContent("Pierwsza świetność");
    expect(last).not.toHaveTextContent(/fragment/);
  });

  it("D25: a work without a cover shows the placeholder board", async () => {
    mockWorks([
      {
        ...work("wertepy", "Wertepy", 1947, 1),
        cover_image: "/media/works/wertepy.png",
        cover_image_alt: "Okładka",
      },
      work("czarny-potok", "Czarny potok", 1954, 2),
    ]);

    const { container } = renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const [withCover, withoutCover] = workCards();
    expect(withCover).toContainElement(screen.getByRole("img", { name: "Okładka" }));
    expect(screen.getAllByRole("img")).toHaveLength(1);
    expect(withoutCover).toHaveTextContent("[Okładka]");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-18 AC2: each card links to its work page (R-01)", async () => {
    mockWorks();

    renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const links = workCards().map((card) => within(card).getByRole("link"));
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/works/wertepy",
      "/works/czarny-potok",
      "/works/dorycki-kruzganek",
      "/works/pierwsza-swietnosc",
    ]);
  });

  it("US-RA-18: without published works the section is hidden (R-02)", async () => {
    mockWorks([]);

    renderRoute("/works");

    await waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(screen.getByRole("heading", { level: 1, name: "Utwory" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
  });

  it("says it is loading, then shows the list", async () => {
    mockWorks();

    const { container } = renderRoute("/works");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję utwory…");
    expect(await axeViolations(container)).toEqual([]);
    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says so when the API fails, keeping the title", async () => {
    server.use(http.get(WORKS_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/works");

    expect(
      await screen.findByText("Nie udało się wczytać utworów. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Utwory" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-20: one column on mobile, the Figma grid on desktop, rows of equal height", async () => {
    mockWorks();

    renderRoute("/works");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie utwory" });
    expect(within(section()).getByRole("list")).toHaveClass(
      "grid-cols-1",
      "lg:grid-cols-4",
      "auto-rows-fr",
    );
    const title = screen.getByRole("heading", { level: 1, name: "Utwory" });
    expect(title.closest("[data-slot=page-header]")).toHaveClass("px-page-mobile", "md:px-page");
    expect(section()).toHaveClass("p-card-mobile", "md:p-card");
  });
});
