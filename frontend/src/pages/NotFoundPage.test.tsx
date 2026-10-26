import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";

describe("NotFoundPage", () => {
  it("is shown for an unknown URL and links back home", async () => {
    const { container } = renderRoute("/no-such-page");

    expect(screen.getByRole("heading", { level: 1, name: "Nie znaleziono strony" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Wróć na stronę główną" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});
