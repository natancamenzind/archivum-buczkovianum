import { screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type Home = components["schemas"]["HomePage"];
type Featured = components["schemas"]["FeaturedFragment"];

const HOME_URL = "*/api/home/";

const FEATURED: Featured = {
  fragment: {
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
    tags: [{ slug: "epidemia", title: "Epidemia" }],
  },
  work: { id: 7, title: "Wertepy", count: 24 },
};

const HOME: Home = {
  intro: "<p>Archiwum literackie <em>Leopolda Buczkowskiego</em>.</p>",
  portrait: "/media/site/portret.jpg",
  portrait_alt: "Leopold Buczkowski, portret z lat sześćdziesiątych",
  statistics: { works: 4, fragments: 62, tags: 12 },
  // In the API's order: by first edition.
  works: [
    {
      slug: "wertepy",
      title: "Wertepy",
      genre: "powieść",
      year: 1947,
      cover_image: "",
      cover_image_alt: "",
      fragment_count: 24,
    },
    {
      slug: "czarny-potok",
      title: "Czarny potok",
      genre: "powieść",
      year: 1954,
      cover_image: "",
      cover_image_alt: "",
      fragment_count: 0,
    },
  ],
  featured: FEATURED,
  // In the API's order: the most frequent first.
  tags: [
    { slug: "wojna", title: "Wojna", occurrences: 31 },
    { slug: "las", title: "Las", occurrences: 2 },
  ],
};

function mockHome(home: Partial<Home> = {}): void {
  server.use(http.get(HOME_URL, () => HttpResponse.json({ ...HOME, ...home })));
}

function hero(): HTMLElement {
  const title = screen.getByRole("heading", { level: 1, name: "Archivum Buczkovianum" });
  const element = title.closest<HTMLElement>("[data-slot=home-hero]");
  if (element === null) {
    throw new Error("The title is not inside the hero.");
  }
  return element;
}

function section(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name });
  const card = heading.closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error(`'${name}' is not inside a card.`);
  }
  return card;
}

function precedes(first: Element, second: Element): boolean {
  return (first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
}

describe("HomePage", () => {
  it("US-RA-01 AC1: header, hero, works, featured fragment, tag cloud and footer come in order", async () => {
    mockHome();

    const { container } = renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Utwory" });
    const order = [
      screen.getByRole("banner"),
      hero(),
      section("Utwory"),
      section("Wybrany fragment"),
      section("Chmura tagów"),
      screen.getByRole("contentinfo"),
    ];
    order.slice(1).forEach((element, index) => {
      expect(precedes(order[index] as Element, element)).toBe(true);
    });
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(within(nav).getByRole("link", { name: "Strona główna" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC2: the hero has the title, introduction, portrait and counts", async () => {
    mockHome();

    const { container } = renderRoute("/");

    expect(await within(hero()).findByText("4 utwory · 62 fragmenty · 12 tagów")).toBeVisible();
    expect(within(hero()).getByText("Leopolda Buczkowskiego").tagName).toBe("EM");
    expect(
      within(hero()).getByRole("img", {
        name: "Leopold Buczkowski, portret z lat sześćdziesiątych",
      }),
    ).toHaveAttribute("src", "/media/site/portret.jpg");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC2: the counts use the right plural for 1 and 5", async () => {
    mockHome({ statistics: { works: 1, fragments: 5, tags: 1 } });

    renderRoute("/");

    expect(await within(hero()).findByText("1 utwór · 5 fragmentów · 1 tag")).toBeVisible();
  });

  it("US-RA-01 AC3: the work cards come in the API's order, with the count, and link to their pages", async () => {
    mockHome();

    const { container } = renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Utwory" });
    const works = section("Utwory");
    const cards = within(works).getAllByRole("listitem");
    expect(
      cards.map((card) => within(card).getByRole("heading", { level: 3 }).textContent),
    ).toEqual(["Wertepy", "Czarny potok"]);
    expect(cards.map((card) => within(card).getByRole("link").getAttribute("href"))).toEqual([
      "/works/wertepy",
      "/works/czarny-potok",
    ]);
    expect(cards[0]).toHaveTextContent("powieść · 1947");
    expect(cards[0]).toHaveTextContent("Leopold Buczkowski");
    expect(cards[0]).toHaveTextContent("24 fragmenty");
    expect(cards[1]).not.toHaveTextContent(/fragment/);
    expect(within(works).getByText("2")).toBeVisible();
    expect(
      within(works).getByText("Wszystkie utwory w archiwum, w kolejności wydania"),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: the tag cloud links every tag to its page, with the count in the header", async () => {
    mockHome();

    const { container } = renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Chmura tagów" });
    const cloud = section("Chmura tagów");
    expect(within(cloud).getByRole("link", { name: /^Wojna/ })).toHaveAttribute(
      "href",
      "/tags/wojna",
    );
    expect(within(cloud).getByRole("link", { name: /^Las/ })).toHaveAttribute("href", "/tags/las");
    expect(within(cloud).getByText("2")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-02 AC1: the featured fragment is a fragment card counted among all visible fragments", async () => {
    mockHome();

    const { container } = renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Wybrany fragment" });
    const featured = section("Wybrany fragment");
    expect(within(featured).getByText("1 z 62")).toBeVisible();
    expect(within(featured).getByText("Wybór redakcji")).toBeVisible();
    expect(within(featured).getByText("Grzybniak chodził od chałupy do chałupy.")).toBeVisible();
    expect(
      within(featured).getByRole("link", { name: "Wertepy · Fragment 01 · rozdział I" }),
    ).toHaveAttribute("href", "/typescripts/1?fragment=5");
    expect(within(featured).getByRole("link", { name: "Epidemia" })).toHaveAttribute(
      "href",
      "/tags/epidemia",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-02 AC2: the link opens search on the Fragmenty tab filtered to the fragment's work", async () => {
    mockHome();

    const { container } = renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Wybrany fragment" });
    expect(
      within(section("Wybrany fragment")).getByRole("link", {
        name: "Wszystkie fragmenty „Wertepy” (24)",
      }),
    ).toHaveAttribute("href", "/search?tab=fragments&work=7");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a featured fragment whose source has no published work has no search link", async () => {
    mockHome({ featured: { ...FEATURED, work: null } });

    renderRoute("/");

    await screen.findByRole("heading", { level: 2, name: "Wybrany fragment" });
    expect(within(section("Wybrany fragment")).queryByText(/Wszystkie fragmenty/)).toBeNull();
  });

  it("US-RA-01 AC5: the hero shows the introduction and portrait the editors set", async () => {
    mockHome({
      intro: "<p>Nowy wstęp redakcji.</p><p>Drugi akapit.</p>",
      portrait: "/media/site/nowy.jpg",
      portrait_alt: "Nowy portret",
    });

    renderRoute("/");

    expect(await within(hero()).findByText("Drugi akapit.")).toBeVisible();
    expect(within(hero()).getByText("Nowy wstęp redakcji.")).toBeVisible();
    expect(within(hero()).getByRole("img", { name: "Nowy portret" })).toHaveAttribute(
      "src",
      "/media/site/nowy.jpg",
    );
  });

  it("R-02: without introduction, portrait, works, featured fragment or tags those parts are not rendered", async () => {
    mockHome({ intro: "", portrait: "", portrait_alt: "", works: [], featured: null, tags: [] });

    const { container } = renderRoute("/");

    await waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(hero()).toHaveTextContent(/^Archivum Buczkovianum4 utwory · 62 fragmenty · 12 tagów$/);
    expect(within(hero()).queryByRole("img")).toBeNull();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("says it is loading, then shows the page", async () => {
    mockHome();

    const { container } = renderRoute("/");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję stronę…");
    expect(await axeViolations(container)).toEqual([]);
    await screen.findByRole("heading", { level: 2, name: "Utwory" });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says so when the API fails, keeping the title", async () => {
    server.use(http.get(HOME_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/");

    expect(
      await screen.findByText("Nie udało się wczytać strony. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Archivum Buczkovianum" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });
});
