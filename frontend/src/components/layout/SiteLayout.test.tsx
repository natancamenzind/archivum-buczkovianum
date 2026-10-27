import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

const NAV_ITEMS = [
  ["Strona główna", "/"],
  ["Utwory", "/works"],
  ["Maszynopisy", "/typescripts"],
  ["Tagi", "/tags"],
] as const;

function mainNav(): HTMLElement {
  return screen.getByRole("navigation", { name: "Menu główne" });
}

function currentNavItem(): HTMLElement | null {
  return mainNav().querySelector('[aria-current="page"]');
}

describe("SiteLayout", () => {
  beforeEach(() => {
    // The placeholder home page asks the API for its schema.
    server.use(http.get("*/api/schema/", () => HttpResponse.json({ paths: {} })));
  });

  it("US-RA-03 AC1: the header links the service name to home and 'O archiwum' to /about", async () => {
    const { container } = renderRoute("/about");

    const header = screen.getByRole("banner");
    expect(
      within(header).getByRole("link", { name: "Archivum Buczkovianum Archiwum literackie" }),
    ).toHaveAttribute("href", "/");
    expect(within(header).getByRole("link", { name: "O archiwum" })).toHaveAttribute(
      "href",
      "/about",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-03 AC1: the header has no search control yet (step 29)", () => {
    renderRoute("/about");

    const header = screen.getByRole("banner");
    expect(within(header).queryByRole("searchbox")).toBeNull();
    expect(within(header).queryByRole("button")).toBeNull();
    expect(within(header).getAllByRole("link")).toHaveLength(2);
  });

  it("US-RA-03 AC1: the main navigation lists Strona główna, Utwory, Maszynopisy, Tagi", async () => {
    const { container } = renderRoute("/about");

    const links = within(mainNav()).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual(NAV_ITEMS);
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    ["/", "Strona główna"],
    ["/works", "Utwory"],
    ["/works/wertepy", "Utwory"],
    ["/typescripts", "Maszynopisy"],
    ["/typescripts/1", "Maszynopisy"],
    ["/tags", "Tagi"],
    ["/tags/dezerter", "Tagi"],
  ])("US-RA-03 AC1: on %s the active navigation item is %s", async (url, label) => {
    const { container } = renderRoute(url);

    expect(currentNavItem()).toHaveTextContent(label);
    expect(mainNav().querySelectorAll('[aria-current="page"]')).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each(["/about", "/search", "/notes/1", "/secondary-texts/1", "/materials/1"])(
    "US-RA-03 AC1: on %s no navigation item is active",
    (url) => {
      renderRoute(url);

      expect(currentNavItem()).toBeNull();
    },
  );

  it("US-RA-03 AC1: the footer shows the service name, subtitle, navigation and funding note", async () => {
    const { container } = renderRoute("/about");

    const footer = screen.getByRole("contentinfo");
    expect(within(footer).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(within(footer).getByText("Archiwum literackie Leopolda Buczkowskiego")).toBeVisible();
    expect(within(footer).getByRole("navigation", { name: "Menu główne" })).toBe(mainNav());
    expect(within(footer).getByText(/finansowani/i)).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-03 AC1: the navigation is a bottom bar on mobile and sits in the footer on desktop", () => {
    renderRoute("/about");

    // Mobile first: fixed to the bottom of the viewport; from `md` up, part of the footer row.
    expect(mainNav()).toHaveClass("fixed", "bottom-0", "md:static");
    // The page leaves room for the bar on mobile, so it never covers the footer.
    expect(screen.getByRole("contentinfo")).toHaveClass("pb-64", "md:pb-0");
  });

  it("R-12: every header and navigation link shows a focus outline, the active item too", () => {
    renderRoute("/works");

    const links = [
      ...within(screen.getByRole("banner")).getAllByRole("link"),
      ...within(mainNav()).getAllByRole("link"),
    ];
    // A colour shift alone is invisible on the active item, which is already in the accent colour.
    for (const link of links) {
      expect(link).toHaveClass("focus-visible:outline-2", "focus-visible:outline-ring");
    }
  });

  it("US-RA-03 AC1: every page renders inside the shell, a missing one too", () => {
    renderRoute("/works");

    expect(screen.getByRole("banner")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });
});
