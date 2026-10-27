import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { WorkCard } from "@/components/WorkCard";
import { axeViolations } from "@/test/render";

type Work = components["schemas"]["WorkCard"];

const WERTEPY: Work = {
  slug: "wertepy",
  title: "Wertepy",
  genre: "powieść",
  year: 1947,
  cover_image: "/media/works/wertepy.png",
  cover_image_alt: "Okładka: koń na tle drzew",
  fragment_count: 24,
};

function renderCard(work: Partial<Work> = {}) {
  return render(
    <MemoryRouter>
      <WorkCard work={{ ...WERTEPY, ...work }} />
    </MemoryRouter>,
  );
}

function card(): HTMLElement {
  return screen.getByRole("link");
}

describe("WorkCard", () => {
  it("US-RA-01 AC3: shows the cover, genre and year, title, author and fragment count", async () => {
    const { container } = renderCard();

    expect(screen.getByRole("img", { name: "Okładka: koń na tle drzew" })).toHaveAttribute(
      "src",
      "/media/works/wertepy.png",
    );
    expect(screen.getByText("powieść · 1947")).toBeVisible();
    expect(screen.getByRole("heading", { level: 3, name: "Wertepy" })).toBeVisible();
    expect(screen.getByText("Leopold Buczkowski")).toBeVisible();
    expect(screen.getByText("24 fragmenty")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC3: the whole card is one link to the work page (R-01)", () => {
    renderCard();

    expect(card()).toHaveAttribute("href", "/works/wertepy");
    expect(card()).toContainElement(screen.getByRole("heading", { name: "Wertepy" }));
    expect(card()).toContainElement(screen.getByText("24 fragmenty"));
  });

  it.each([
    [1, "1 fragment"],
    [2, "2 fragmenty"],
    [5, "5 fragmentów"],
    [22, "22 fragmenty"],
  ])("US-RA-01 AC3: %i fragments read '%s'", (count, text) => {
    renderCard({ fragment_count: count });

    expect(screen.getByText(text)).toBeVisible();
  });

  it("D23: with 0 fragments the footer hides the count and keeps the arrow", async () => {
    const { container } = renderCard({ fragment_count: 0 });

    const footer = container.querySelector("[data-slot=work-card-footer]");
    expect(footer).toHaveTextContent("");
    expect(footer?.querySelector("svg")).not.toBeNull();
    expect(screen.queryByText(/fragment/)).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("D25: without a cover the card shows the placeholder board", async () => {
    const { container } = renderCard({ cover_image: "", cover_image_alt: "" });

    expect(screen.queryByRole("img")).toBeNull();
    expect(container.querySelector("[data-slot=cover-placeholder]")).toHaveTextContent("[Okładka]");
    expect(card()).toHaveAccessibleName("powieść · 1947 Wertepy Leopold Buczkowski 24 fragmenty");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-02: a missing year or genre is left out of the type line", () => {
    const { unmount } = renderCard({ year: null });
    expect(screen.getByText("powieść")).toBeVisible();
    unmount();

    renderCard({ genre: "" });
    expect(screen.getByText("1947")).toBeVisible();
  });

  it("R-02: without genre and year there is no type line", () => {
    const { container } = renderCard({ genre: "", year: null });

    expect(container.querySelector(".text-cousine-etykieta")).toBeNull();
  });

  it("lifts and turns the title to the accent on hover and keyboard focus, unless motion is reduced", () => {
    const { container } = renderCard();

    const panel = container.querySelector("[data-slot=card]");
    expect(panel).toHaveClass(
      "group-hover:-translate-y-4",
      "group-hover:shadow-raised",
      "group-focus-visible:-translate-y-4",
      "motion-reduce:transition-none",
      "motion-reduce:group-hover:translate-y-0",
    );
    expect(screen.getByRole("heading", { name: "Wertepy" })).toHaveClass(
      "group-hover:text-accent-foreground",
      "group-focus-visible:text-accent-foreground",
    );
    expect(card()).toHaveClass("focus-visible:outline-2", "focus-visible:outline-ring");
  });

  it("fills its grid cell and pins the footer to the bottom", () => {
    const { container } = renderCard();

    expect(card()).toHaveClass("h-full");
    expect(container.querySelector("[data-slot=card]")).toHaveClass("h-full");
    expect(container.querySelector("[data-slot=work-card-footer]")).toHaveClass("mt-auto");
  });
});
