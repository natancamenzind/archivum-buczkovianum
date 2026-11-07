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
    expect(screen.getByRole("heading", { level: 1, name: "Wertepy" })).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-29: shows no image when the entity has none", async () => {
    const { container } = render(
      <PageHeader label="Utwór" title="Wertepy" image={{ src: "", alt: "" }} />,
    );

    expect(container.querySelector("img")).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });
});
