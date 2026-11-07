import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Select } from "@/components/Select";
import { axeViolations } from "@/test/render";

describe("Select", () => {
  it("ARC-25: draws the design's chevron, inset from the right edge, in place of the browser's", async () => {
    const { container } = render(
      <Select aria-label="Okres" className="grow">
        <option value="">Wszystkie lata</option>
      </Select>,
    );

    const select = screen.getByRole("combobox", { name: "Okres" });
    expect(select).toHaveClass("appearance-none", "pr-48");
    expect(select).toHaveValue("");
    const chevron = container.querySelector("svg");
    expect(chevron).toHaveClass("right-16");
    expect(chevron).toHaveAttribute("aria-hidden", "true");
    // The caller's className sizes the box around the select and its chevron.
    expect(select.parentElement).toHaveClass("relative", "grow");
    expect(await axeViolations(container)).toEqual([]);
  });
});
