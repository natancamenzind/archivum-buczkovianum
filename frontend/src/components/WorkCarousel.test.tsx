import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { Work } from "@/components/WorkCard";
import { WorkCarousel } from "@/components/WorkCarousel";
import { axeViolations } from "@/test/render";

const WORKS: Work[] = ["Wertepy", "Czarny potok", "Dorycki krużganek"].map((title, index) => ({
  slug: `utwor-${String(index)}`,
  title,
  year: 1947 + index,
  cover_image: "",
  cover_image_alt: "",
  fragment_count: 0,
}));

function renderCarousel() {
  return render(
    <MemoryRouter>
      <WorkCarousel works={WORKS} />
    </MemoryRouter>,
  );
}

/** jsdom lays nothing out, so the row's size, scroll position and card width are set here. */
function layOut(list: HTMLElement, { scrollLeft = 0, clientWidth = 450 } = {}) {
  Object.defineProperty(list, "scrollWidth", { configurable: true, value: 1000 });
  Object.defineProperty(list, "clientWidth", { configurable: true, value: clientWidth });
  list.scrollLeft = scrollLeft;
  const card = list.firstElementChild;
  if (card !== null) {
    vi.spyOn(card, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 0, 200, 440));
  }
  const scrollBy = vi.fn();
  list.scrollBy = scrollBy;
  fireEvent.scroll(list);
  return scrollBy;
}

describe("WorkCarousel", () => {
  it("ARC-20: the works are one scrolling row, 1.5 cards in view on a phone and 4.5 on a desktop", () => {
    renderCarousel();

    const list = screen.getByRole("list");
    expect(list).toHaveClass("flex", "overflow-x-auto", "snap-x", "snap-mandatory");
    expect(list).toHaveClass("[--visible:1.5]", "xl:[--visible:4.5]");
    for (const item of screen.getAllByRole("listitem")) {
      expect(item).toHaveClass("shrink-0", "snap-start");
    }
  });

  it("ARC-20: shows no arrows when every work fits", () => {
    renderCarousel();

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("ARC-51: at the start only the next arrow shows, and it scrolls by the whole cards in view", async () => {
    const { container } = renderCarousel();
    const scrollBy = layOut(screen.getByRole("list"));

    expect(screen.queryByRole("button", { name: "Poprzednie utwory" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Następne utwory" }));
    // Two 200 px cards fit in 450 px.
    expect(scrollBy).toHaveBeenCalledWith({ left: 400 });
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-51: at the end only the previous arrow shows, and it scrolls back", () => {
    renderCarousel();
    const scrollBy = layOut(screen.getByRole("list"), { scrollLeft: 550 });

    expect(screen.queryByRole("button", { name: "Następne utwory" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Poprzednie utwory" }));
    expect(scrollBy).toHaveBeenCalledWith({ left: -400 });
  });

  it("ARC-51: the arrows sit on the row's sides at half the cards' height, shown on hover or focus and never on touch screens", () => {
    renderCarousel();
    layOut(screen.getByRole("list"), { scrollLeft: 100 });

    const previous = screen.getByRole("button", { name: "Poprzednie utwory" });
    const next = screen.getByRole("button", { name: "Następne utwory" });
    for (const arrow of [previous, next]) {
      expect(arrow).toHaveClass("absolute", "top-1/2", "-translate-y-1/2");
      expect(arrow).toHaveClass(
        "opacity-0",
        "group-hover/carousel:opacity-100",
        "group-focus-within/carousel:opacity-100",
        "pointer-coarse:hidden",
      );
    }
    expect(previous).toHaveClass("-left-16");
    expect(next).toHaveClass("-right-16");
  });

  it("ARC-20: a narrow row scrolls by one card, and the arrows follow a window resize", () => {
    renderCarousel();
    const list = screen.getByRole("list");
    const scrollBy = layOut(list, { scrollLeft: 100, clientWidth: 150 });

    fireEvent.click(screen.getByRole("button", { name: "Następne utwory" }));
    expect(scrollBy).toHaveBeenCalledWith({ left: 200 });

    Object.defineProperty(list, "clientWidth", { configurable: true, value: 1000 });
    list.scrollLeft = 0;
    fireEvent(window, new Event("resize"));
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
