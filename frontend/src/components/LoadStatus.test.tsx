import { screen } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "@/test/server";
import { axeViolations, renderRoute } from "@/test/render";

/** The hypocycloid of the not-found page; the dark heroes draw theirs in another tone. */
const CURVE = 'main [data-slot="hypocycloid"].stroke-accent-border';

/** Every API request fails, after a moment so the loading state shows first. */
function failApi() {
  server.use(
    http.get("*/api/*", async () => {
      await delay(50);
      return new HttpResponse(null, { status: 500 });
    }),
  );
}

describe("LoadStatus", () => {
  it.each([
    ["/", "Nie udało się wczytać strony."],
    ["/utwory", "Nie udało się wczytać utworów."],
    ["/maszynopisy", "Nie udało się wczytać maszynopisów."],
    ["/tagi", "Nie udało się wczytać tagów."],
    ["/o-archiwum", "Nie udało się wczytać strony."],
    ["/utwory/wertepy", "Nie udało się wczytać utworu."],
    ["/utwory/wertepy/bibliografia", "Nie udało się wczytać bibliografii."],
    ["/tagi/dezerter", "Nie udało się wczytać tagu."],
    ["/maszynopisy/1", "Nie udało się wczytać maszynopisu."],
    ["/zapiski/3", "Nie udało się wczytać zapisku."],
    ["/materialy/4", "Nie udało się wczytać materiału kontekstowego."],
    ["/teksty-sekundarne/4", "Nie udało się wczytać tekstu sekundarnego."],
    ["/szukaj?q=dezerter", "Nie udało się wczytać wyników."],
  ])("ARC-63: %s draws the hypocycloid by its error, not while it loads", async (url, error) => {
    failApi();

    const { container } = renderRoute(url);

    expect(container.querySelector(CURVE)).toBeNull();
    expect(await screen.findByText(new RegExp(`^${error}`))).toBeVisible();
    expect(container.querySelector(CURVE)).toHaveAttribute("aria-hidden", "true");
    expect(await axeViolations(container)).toEqual([]);
  });
});
