import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { TagCount } from "@/components/TagCloud";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

const TAGS_URL = "*/api/tags/";

function tag(slug: string, title: string, occurrences: number): TagCount {
  return { slug, title, occurrences };
}

// In the API's order: the most frequent first.
const TAGS: TagCount[] = [
  tag("wojna", "Wojna", 31),
  tag("slad", "Ślad", 5),
  tag("dezerter", "Dezerter", 4),
  tag("laka", "Łąka", 2),
  tag("sad", "Sad", 2),
  tag("las", "Las", 1),
  tag("mak", "Mak", 1),
];

function mockTags(tags: TagCount[] = TAGS): void {
  server.use(http.get(TAGS_URL, () => HttpResponse.json(tags)));
}

function section(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name });
  const card = heading.closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error(`'${name}' is not inside a card.`);
  }
  return card;
}

function indexRows(): HTMLElement[] {
  return within(section("Wszystkie tagi")).getAllByRole("listitem");
}

describe("TagsPage", () => {
  it("US-RA-20 AC1: 'Tagi' in the main navigation opens the list and is the active item", async () => {
    mockTags();
    server.use(http.get("*/api/works/", () => HttpResponse.json([])));
    const { container } = renderRoute("/works");

    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    fireEvent.click(within(nav).getByRole("link", { name: "Tagi" }));

    expect(await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" })).toBeVisible();
    expect(within(nav).getByRole("link", { name: "Tagi" })).toHaveAttribute("aria-current", "page");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-20: the hero shows the label, the title 'Tagi' and the description", async () => {
    mockTags();

    const { container } = renderRoute("/tags");

    const title = screen.getByRole("heading", { level: 1, name: "Tagi" });
    const hero = title.closest<HTMLElement>("[data-slot=page-header]");
    if (hero === null) {
      throw new Error("The title is not inside the hero.");
    }
    expect(within(hero).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(
      within(hero).getByText("Motywy łączące fragmenty i zapiski z różnych utworów."),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-20 AC2: the tag cloud comes first, with its count and description", async () => {
    mockTags();

    const { container } = renderRoute("/tags");

    const index = await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    const cloud = section("Chmura tagów");
    expect(cloud.compareDocumentPosition(index) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(cloud).getByText("7")).toBeVisible();
    expect(
      within(cloud).getByText("Wielkość nazwy odpowiada liczbie wystąpień, w pięciu stopniach"),
    ).toBeVisible();
    expect(within(cloud).getByRole("link", { name: "Wojna 31 wystąpień" })).toHaveAttribute(
      "href",
      "/tags/wojna",
    );
    expect(within(cloud).getAllByRole("link")).toHaveLength(7);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-20 AC2: 'Wszystkie tagi' lists every tag in Polish alphabetical order", async () => {
    mockTags();

    renderRoute("/tags");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    const index = section("Wszystkie tagi");
    expect(within(index).getByText("7")).toBeVisible();
    expect(within(index).getByText("Alfabetycznie")).toBeVisible();
    expect(indexRows().map((row) => within(row).getByRole("link").firstChild?.textContent)).toEqual(
      ["Dezerter", "Las", "Łąka", "Mak", "Sad", "Ślad", "Wojna"],
    );
  });

  it("US-RA-20 AC2: each row shows the occurrence count with the right plural", async () => {
    mockTags();

    renderRoute("/tags");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    const index = section("Wszystkie tagi");
    expect(within(index).getByRole("link", { name: "Las 1 wystąpienie" })).toBeVisible();
    expect(within(index).getByRole("link", { name: "Dezerter 4 wystąpienia" })).toBeVisible();
    expect(within(index).getByRole("link", { name: "Ślad 5 wystąpień" })).toBeVisible();
  });

  it("US-RA-20 AC2: each row links to its tag page (R-01)", async () => {
    mockTags();

    renderRoute("/tags");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    expect(indexRows().map((row) => within(row).getByRole("link").getAttribute("href"))).toEqual([
      "/tags/dezerter",
      "/tags/las",
      "/tags/laka",
      "/tags/mak",
      "/tags/sad",
      "/tags/slad",
      "/tags/wojna",
    ]);
  });

  it("US-RA-20: one column on mobile, two on desktop", async () => {
    mockTags();

    renderRoute("/tags");

    await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    const list = within(section("Wszystkie tagi")).getByRole("list");
    expect(list).toHaveClass("md:columns-2");
    expect(list).not.toHaveClass("columns-2");
    expect(section("Chmura tagów")).toHaveClass("p-card-mobile", "md:p-card");
  });

  it("US-RA-20: without tags in use both sections are hidden (R-02)", async () => {
    mockTags([]);

    renderRoute("/tags");

    await waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(screen.getByRole("heading", { level: 1, name: "Tagi" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
  });

  it("says it is loading, then shows the list", async () => {
    mockTags();

    const { container } = renderRoute("/tags");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję tagi…");
    expect(await axeViolations(container)).toEqual([]);
    await screen.findByRole("heading", { level: 2, name: "Wszystkie tagi" });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says so when the API fails, keeping the title", async () => {
    server.use(http.get(TAGS_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/tags");

    expect(
      await screen.findByText("Nie udało się wczytać tagów. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Tagi" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });
});
