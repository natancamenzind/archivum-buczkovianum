import { fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

const NAV_ITEMS = [
  ["Strona główna", "/"],
  ["Utwory", "/utwory"],
  ["Maszynopisy", "/maszynopisy"],
  ["Tagi", "/tagi"],
] as const;

function mainNav(): HTMLElement {
  return screen.getByRole("navigation", { name: "Menu główne" });
}

function currentNavItem(): HTMLElement | null {
  return mainNav().querySelector('[aria-current="page"]');
}

describe("SiteLayout", () => {
  beforeEach(() => {
    // Most cases render /o-archiwum or /utwory, which ask the API for their content.
    server.use(
      http.get("*/api/about/", () => HttpResponse.json({ intro: "", project: "", team: [] })),
      http.get("*/api/works/", () => HttpResponse.json([])),
      http.get("*/api/tags/", () => HttpResponse.json([])),
    );
  });

  it("US-RA-03 AC1: the header links the service name to home and 'O archiwum' to /o-archiwum", async () => {
    const { container } = renderRoute("/o-archiwum");

    const header = screen.getByRole("banner");
    expect(
      within(header).getByRole("link", { name: "Archivum Buczkovianum Archiwum literackie" }),
    ).toHaveAttribute("href", "/");
    expect(within(header).getByRole("link", { name: "O archiwum" })).toHaveAttribute(
      "href",
      "/o-archiwum",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each(["/", "/o-archiwum", "/utwory", "/szukaj", "/no-such-page"])(
    "US-RA-14 AC1: on %s the header has the search field",
    async (url) => {
      const { container } = renderRoute(url);

      const header = screen.getByRole("banner");
      const form = within(header).getByRole("search", { name: "Szukaj w archiwum" });
      expect(within(form).getByRole("combobox", { name: "Szukaj w archiwum" })).toHaveAttribute(
        "placeholder",
        "Szukaj w archiwum",
      );
      expect(await axeViolations(container)).toEqual([]);
    },
  );

  it("US-RA-14 AC1: submitting the header field opens the search page with the query", () => {
    renderRoute("/o-archiwum");

    const header = screen.getByRole("banner");
    const field = within(header).getByRole("combobox", { name: "Szukaj w archiwum" });
    fireEvent.change(field, { target: { value: " Dezerter " } });
    fireEvent.submit(within(header).getByRole("search"));

    expect(screen.getByRole("heading", { level: 1, name: "Wyszukiwanie" })).toBeInTheDocument();
    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("combobox")).toHaveValue("Dezerter");
    expect(field).toHaveValue("");
  });

  it("US-RA-14 AC1: a header search on the search page replaces the query", () => {
    renderRoute("/szukaj?q=dezerter");

    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("combobox"), { target: { value: "potok" } });
    fireEvent.submit(within(header).getByRole("search"));

    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("combobox")).toHaveValue("potok");
  });

  it("US-RA-14 AC1: a header search for the current query drops unsubmitted edits", () => {
    renderRoute("/szukaj?q=dezerter");

    const pageField = within(screen.getByRole("search", { name: "Wyszukiwanie" })).getByRole(
      "combobox",
    );
    fireEvent.change(pageField, { target: { value: "potok" } });
    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("combobox"), { target: { value: "dezerter" } });
    fireEvent.submit(within(header).getByRole("search"));

    expect(pageField).toHaveValue("dezerter");
  });

  it("US-RA-14 AC1: a blank header search opens the search page without a query", () => {
    const { router } = renderRoute("/o-archiwum");

    const header = screen.getByRole("banner");
    fireEvent.change(within(header).getByRole("combobox"), { target: { value: "  " } });
    fireEvent.submit(within(header).getByRole("search"));

    const pageForm = screen.getByRole("search", { name: "Wyszukiwanie" });
    expect(within(pageForm).getByRole("combobox")).toHaveValue("");
    expect(router.state.location.pathname).toBe("/szukaj");
    expect(router.state.location.search).toBe("");
  });

  it("US-RA-14 AC1: on mobile the header search is an icon linking to the search page", () => {
    renderRoute("/o-archiwum");

    const header = screen.getByRole("banner");
    const icon = within(header).getByRole("link", { name: "Szukaj w archiwum" });
    expect(icon).toHaveAttribute("href", "/szukaj");
    expect(icon).toHaveClass("md:hidden");
    // The field is the desktop form; "O archiwum" stays on both (plan, step 29).
    expect(within(header).getByRole("search")).toHaveClass("hidden", "md:flex");
    expect(within(header).getByRole("link", { name: "O archiwum" })).not.toHaveClass("hidden");
  });

  it("US-RA-03 AC1: the main navigation lists Strona główna, Utwory, Maszynopisy, Tagi", async () => {
    const { container } = renderRoute("/o-archiwum");

    const links = within(mainNav()).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual(NAV_ITEMS);
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    ["/", "Strona główna"],
    ["/utwory", "Utwory"],
    ["/utwory/wertepy", "Utwory"],
    ["/maszynopisy", "Maszynopisy"],
    ["/maszynopisy/1", "Maszynopisy"],
    ["/tagi", "Tagi"],
    ["/tagi/dezerter", "Tagi"],
  ])("US-RA-03 AC1: on %s the active navigation item is %s", async (url, label) => {
    const { container } = renderRoute(url);

    expect(currentNavItem()).toHaveTextContent(label);
    expect(mainNav().querySelectorAll('[aria-current="page"]')).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each(["/o-archiwum", "/szukaj", "/zapiski/1", "/teksty-sekundarne/1", "/materialy/1"])(
    "US-RA-03 AC1: on %s no navigation item is active",
    (url) => {
      renderRoute(url);

      expect(currentNavItem()).toBeNull();
    },
  );

  it("US-RA-03 AC1: the footer shows the service name, subtitle, navigation and funding note", async () => {
    const { container } = renderRoute("/o-archiwum");

    const footer = screen.getByRole("contentinfo");
    expect(within(footer).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(within(footer).getByText("Archiwum literackie Leopolda Buczkowskiego")).toBeVisible();
    expect(within(footer).getByRole("navigation", { name: "Menu główne" })).toBe(mainNav());
    expect(within(footer).getByText(/finansowani/i)).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-03 AC1: the navigation is a bottom bar on mobile and sits in the footer on desktop", () => {
    renderRoute("/o-archiwum");

    // Mobile first: fixed to the bottom of the viewport; from `md` up, part of the footer row.
    expect(mainNav()).toHaveClass("fixed", "bottom-0", "md:static");
    // The page leaves room for the bar on mobile, so it never covers the footer.
    expect(screen.getByRole("contentinfo")).toHaveClass("pb-64", "md:pb-0");
  });

  it("ARC-5: a navigation label that wraps on mobile stays centred", () => {
    renderRoute("/o-archiwum");

    // "Strona główna" breaks onto two lines on a narrow bar; the lines centre like the other labels.
    for (const [name] of NAV_ITEMS) {
      expect(within(mainNav()).getByRole("link", { name })).toHaveClass("text-center");
    }
  });

  it("ARC-9: the funding note is right-aligned in the desktop footer", () => {
    renderRoute("/o-archiwum");

    // It closes the footer row, so its lines align to the right edge of the page.
    expect(within(screen.getByRole("contentinfo")).getByText(/finansowani/i)).toHaveClass(
      "md:text-right",
    );
  });

  it("ARC-27: the funding note never overlaps the navigation", () => {
    renderRoute("/o-archiwum");

    // A link that can't shrink spills past a shrunk bar, under the note. So the links shrink with
    // the bar (labels wrap) on narrow desktops, and from `lg` the bar keeps their full width.
    expect(mainNav()).toHaveClass("lg:shrink-0");
    for (const [name] of NAV_ITEMS) {
      expect(within(mainNav()).getByRole("link", { name })).toHaveClass(
        "md:flex-initial",
        "lg:flex-none",
      );
    }
  });

  it("R-12: every header control and navigation link shows a focus outline, the active item too", () => {
    renderRoute("/utwory");

    const links = [
      ...within(screen.getByRole("banner")).getAllByRole("link"),
      within(screen.getByRole("banner")).getByRole("combobox"),
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
