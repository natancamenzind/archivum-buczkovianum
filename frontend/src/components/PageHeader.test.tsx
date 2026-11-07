import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PageHeader } from "@/components/PageHeader";
import { axeViolations } from "@/test/render";

describe("PageHeader", () => {
  it("ARC-29: shows the header image behind the title, with its text alternative", async () => {
    const { container } = render(
      <PageHeader
        label="Utwór"
        title="Wertepy"
        image={{ src: "/media/headers/wertepy.webp", alt: "Pejzaż podolski" }}
      />,
    );

    expect(screen.getByRole("img", { name: "Pejzaż podolski" })).toHaveAttribute(
      "src",
      "/media/headers/wertepy.webp",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-29: shows no image when the entity has none", async () => {
    const { container } = render(<PageHeader label="Utwór" title="Wertepy" />);

    expect(container.querySelector("img")).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-32: draws the hypocycloid behind the title when there is no header image", async () => {
    const { container } = render(<PageHeader label="Utwór" title="Wertepy" />);

    const curve = container.querySelector('[data-slot="hypocycloid"]');
    expect(curve).toHaveAttribute("aria-hidden", "true");
    expect(curve).toHaveClass("stroke-inverse-border");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-32: a header image replaces the hypocycloid", () => {
    const { container } = render(
      <PageHeader
        label="Utwór"
        title="Wertepy"
        image={{ src: "/media/headers/wertepy.webp", alt: "Pejzaż podolski" }}
      />,
    );

    expect(container.querySelector('[data-slot="hypocycloid"]')).toBeNull();
  });
});
