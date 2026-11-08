import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SectionHeader } from "@/components/SectionHeader";
import { axeViolations } from "@/test/render";

describe("SectionHeader", () => {
  it("shows the title alone when given no counter or description", async () => {
    const { container } = render(<SectionHeader title="Zespół" />);

    expect(screen.getByRole("heading", { level: 2, name: "Zespół" })).toBeVisible();
    expect(container.querySelectorAll("p")).toHaveLength(0);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("D24: shows the counter next to the title and the description below it", async () => {
    const { container } = render(
      <SectionHeader title="Wszystkie utwory" count="4" description="W kolejności wydania" />,
    );

    const heading = screen.getByRole("heading", { level: 2, name: "Wszystkie utwory" });
    const counter = screen.getByText("4");
    // The counter shares the title's row; the description is the next row.
    expect(counter.parentElement).toBe(heading.parentElement);
    expect(screen.getByText("W kolejności wydania").previousElementSibling).toBe(
      heading.parentElement,
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-40: keeps the counter on one line next to a long title", () => {
    render(<SectionHeader title="Fragmenty maszynopisu" count="2 z 24" />);

    // jsdom has no layout, so assert the classes: the counter never wraps or shrinks,
    // the title takes the squeeze and wraps instead.
    expect(screen.getByText("2 z 24")).toHaveClass("whitespace-nowrap", "shrink-0");
    expect(screen.getByRole("heading", { level: 2 })).toHaveClass("min-w-0");
  });

  it.each([
    ["counter", { count: "2 z 24" }, "2 z 24"],
    ["description", { description: "Wybór redakcji" }, "Wybór redakcji"],
  ])("D24: the %s alone is shown without the other", (_, props, text) => {
    render(<SectionHeader title="Fragmenty" {...props} />);

    expect(screen.getByText(text)).toBeVisible();
    expect(document.querySelectorAll("p")).toHaveLength(1);
  });
});
