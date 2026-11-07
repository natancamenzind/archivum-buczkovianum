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

  it("ARC-20: at the start the previous arrow is disabled and the next one scrolls by the whole cards in view", async () => {
    const { container } = renderCarousel();
    const scrollBy = layOut(screen.getByRole("list"));

    expect(screen.getByRole("button", { name: "Poprzednie utwory" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Następne utwory" }));
    // Two 200 px cards fit in 450 px.
    expect(scrollBy).toHaveBeenCalledWith({ left: 400 });
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-20: at the end the next arrow is disabled and the previous one scrolls back", () => {
    renderCarousel();
    const scrollBy = layOut(screen.getByRole("list"), { scrollLeft: 550 });

    expect(screen.getByRole("button", { name: "Następne utwory" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Poprzednie utwory" }));
    expect(scrollBy).toHaveBeenCalledWith({ left: -400 });
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
