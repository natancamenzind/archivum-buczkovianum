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

  it("D24: the counter and description are each optional", () => {
    const { unmount } = render(<SectionHeader title="Fragmenty" count="2 z 24" />);
    expect(screen.getByText("2 z 24")).toBeVisible();
    expect(document.querySelectorAll("p")).toHaveLength(1);
    unmount();

    render(<SectionHeader title="Fragmenty" description="Wybór redakcji" />);
    expect(screen.getByText("Wybór redakcji")).toBeVisible();
    expect(document.querySelectorAll("p")).toHaveLength(1);
  });
});
