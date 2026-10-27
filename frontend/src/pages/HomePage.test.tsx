import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

describe("HomePage", () => {
  afterEach(() => {
    server.events.removeAllListeners();
  });

  it("D21: the placeholder shows the title and lead without calling the API", async () => {
    const requests: string[] = [];
    server.events.on("request:start", ({ request }) => {
      requests.push(request.url);
    });

    const { container } = renderRoute("/");

    expect(screen.getByRole("heading", { level: 1, name: "Archivum Buczkovianum" })).toBeVisible();
    expect(screen.getByText(/Strona jest w budowie\./)).toBeVisible();
    expect(screen.queryByRole("status")).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
    expect(requests).toEqual([]);
  });
});
