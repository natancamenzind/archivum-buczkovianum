import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

const SCHEMA_URL = "*/api/schema/";

describe("HomePage", () => {
  it("shows the API it reached through the generated client", async () => {
    server.use(
      http.get(SCHEMA_URL, ({ request }) => {
        const format = new URL(request.url).searchParams.get("format");
        return format === "json"
          ? HttpResponse.json({ info: { title: "Archivum Buczkovianum API", version: "1.0.0" } })
          : HttpResponse.text("not json", { status: 406 });
      }),
    );

    const { container } = renderRoute("/");

    expect(screen.getByRole("heading", { level: 1, name: "Archivum Buczkovianum" })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Łączę się z archiwum…");
    expect(
      await screen.findByText("Połączono z Archivum Buczkovianum API, wersja 1.0.0."),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("says so when the API does not answer", async () => {
    server.use(http.get(SCHEMA_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/");

    expect(await screen.findByText("Nie udało się połączyć z archiwum.")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("says so when the API answers without the expected data", async () => {
    server.use(http.get(SCHEMA_URL, () => HttpResponse.json({ paths: {} })));

    const { container } = renderRoute("/");

    expect(await screen.findByText("Nie udało się połączyć z archiwum.")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });
});
