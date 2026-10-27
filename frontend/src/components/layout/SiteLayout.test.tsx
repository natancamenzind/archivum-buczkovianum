import { fireEvent, screen, within } from "@testing-library/react";
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
    // Most cases render /about or /works, which ask the API for their content.
    server.use(
      http.get("*/api/about/", () => HttpResponse.json({ intro: "", project: "", team: [] })),
      http.get("*/api/works/", () => HttpResponse.json([])),
    );
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

  it.each(["/", "/about", "/works", "/search", "/no-such-page"])(
    "US-RA-14 AC1: on %s the header has the search field",
    async (url) => {
      const { container } = renderRoute(url);

      const header = screen.getByRole("banner");
      const form = within(header).getByRole("search", { name: "Szukaj w archiwum" });
      expect(within(form).getByRole("searchbox", { name: "Szukaj w archiwum" })).toHaveAttribute(
        "placeholder",
        "Szukaj w archiwum",
      );
      expect(await axeViolations(container)).toEqual([]);
    },
  );

  it("US-RA-14 AC1: submitting the header field opens the search page with the query", () => {
    renderRoute("/about");

    const header = screen.getByRole("banner");
    const field = within(header).getByRole("searchbox", { name: "Szukaj w archiwum" });
    fireEvent.change(field, { target: { value: " Dezerter " } });
    fireEvent.submit(within(header).getByRole("search"));

    expect(screen.getByRole("heading", { level: 1, name: "Wyszukiwanie" })).toBeInTheDocument();
    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("searchbox")).toHaveValue("Dezerter");
    expect(field).toHaveValue("");
  });

  it("US-RA-14 AC1: a header search on the search page replaces the query", () => {
    renderRoute("/search?q=dezerter");

    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("searchbox"), { target: { value: "potok" } });
    fireEvent.submit(within(header).getByRole("search"));

    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("searchbox")).toHaveValue("potok");
  });

  it("US-RA-14 AC1: a header search for the current query drops unsubmitted edits", () => {
    renderRoute("/search?q=dezerter");

    const pageField = within(screen.getByRole("search", { name: "Wyszukiwanie" })).getByRole(
      "searchbox",
    );
    fireEvent.change(pageField, { target: { value: "potok" } });
    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("searchbox"), { target: { value: "dezerter" } });
    fireEvent.submit(within(header).getByRole("search"));

    expect(pageField).toHaveValue("dezerter");
  });

  it("US-RA-14 AC1: a blank header search opens the search page without a query", () => {
    renderRoute("/about");

    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("searchbox"), { target: { value: "  " } });
    fireEvent.submit(within(header).getByRole("search"));

    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("searchbox")).toHaveValue("");
  });

  it("US-RA-14 AC1: on mobile the header search is an icon linking to the search page", () => {
    renderRoute("/about");

    const header = screen.getByRole("banner");
    const icon = within(header).getByRole("link", { name: "Szukaj w archiwum" });
    expect(icon).toHaveAttribute("href", "/search");
    expect(icon).toHaveClass("md:hidden");
    // The field is the desktop form; "O archiwum" stays on both (plan, step 29).
    expect(within(header).getByRole("search")).toHaveClass("hidden", "md:flex");
    expect(within(header).getByRole("link", { name: "O archiwum" })).not.toHaveClass("hidden");
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

  it("R-12: every header control and navigation link shows a focus outline, the active item too", () => {
    renderRoute("/works");

    const links = [
      ...within(screen.getByRole("banner")).getAllByRole("link"),
      within(screen.getByRole("banner")).getByRole("searchbox"),
      ...within(mainNav()).getAllByRole("link"),
    ];
    // A colour shift alone is invisible on the active item, which is already in the accent colour.
    for (const link of links) {
      expect(link).toHaveClass("focus-visible:outline-2", "focus-visible:outline-ring");
    }
  });

  it("US-RA-03 AC1: every page renders inside the shell, a missing one too", () => {
    renderRoute("/no-such-page");

    expect(screen.getByRole("banner")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });
});
