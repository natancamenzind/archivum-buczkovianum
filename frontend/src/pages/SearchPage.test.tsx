import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";

function searchForm(): HTMLElement {
  return screen.getByRole("search", { name: "Wyszukiwanie" });
}

function searchBox(): HTMLInputElement {
  return within(searchForm()).getByRole<HTMLInputElement>("combobox", {
    name: "Szukaj w archiwum",
  });
}

describe("SearchPage", () => {
  it("US-RA-14 AC1: the search page shows the submitted query in its field", async () => {
    const { container } = renderRoute("/search?q=dezerter+w+stodole");

    expect(screen.getByRole("heading", { level: 1, name: "Wyszukiwanie" })).toBeInTheDocument();
    expect(searchBox()).toHaveValue("dezerter w stodole");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-14 AC1: submitting the page's field searches for the new query", () => {
    renderRoute("/search?q=dezerter");

    fireEvent.change(searchBox(), { target: { value: "  potok " } });
    fireEvent.click(within(searchForm()).getByRole("button", { name: "Szukaj" }));

    expect(searchBox()).toHaveValue("potok");
  });

  it("US-RA-14 AC1: submitting keeps the focus in the field", () => {
    renderRoute("/search?q=dezerter");

    searchBox().focus();
    fireEvent.change(searchBox(), { target: { value: "potok" } });
    fireEvent.submit(searchForm());

    expect(searchBox()).toHaveValue("potok");
    expect(searchBox()).toHaveFocus();
  });

  it("US-RA-14 AC2: a quoted phrase survives the trip through the URL", () => {
    renderRoute("/search");
    const phrase = "„dezerter w stodole” & ł#?+";

    fireEvent.change(searchBox(), { target: { value: phrase } });
    fireEvent.submit(searchForm());

    // The field shows the query decoded from the new URL.
    expect(searchBox()).toHaveValue(phrase);
  });

  it("US-RA-14 AC1: the empty field shows the placeholder and no clear button", async () => {
    const { container } = renderRoute("/search");

    expect(searchBox()).toHaveValue("");
    expect(searchBox()).toHaveAttribute("placeholder", "Tytuł, opis, transkrypcja lub tag");
    expect(within(searchForm()).queryByRole("button", { name: "Wyczyść" })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-14 AC1: 'Wyczyść' empties the field and keeps the focus in it", () => {
    renderRoute("/search?q=dezerter");

    fireEvent.click(within(searchForm()).getByRole("button", { name: "Wyczyść" }));

    expect(searchBox()).toHaveValue("");
    expect(searchBox()).toHaveFocus();
    expect(within(searchForm()).queryByRole("button", { name: "Wyczyść" })).toBeNull();
  });

  it("US-RA-14 AC1: a blank query opens the search page without one", () => {
    renderRoute("/search?q=dezerter");

    fireEvent.change(searchBox(), { target: { value: "   " } });
    fireEvent.submit(searchForm());

    expect(searchBox()).toHaveValue("");
  });

  it("US-RA-14 AC2: under the field, what is searched and the exact-phrase hint", async () => {
    const { container } = renderRoute("/search");

    expect(
      screen.getByText("Przeszukiwane: tytuły, opisy, transkrypcje i tagi"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Dokładna fraza: użyj cudzysłowu, np. „dezerter w stodole”"),
    ).toBeInTheDocument();
    expect(searchBox()).toHaveAccessibleDescription(
      "Przeszukiwane: tytuły, opisy, transkrypcje i tagi Dokładna fraza: użyj cudzysłowu, np. „dezerter w stodole”",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it("R-12: the field and its buttons show a focus outline", () => {
    renderRoute("/search?q=dezerter");

    expect(searchForm()).toHaveClass("has-[input:focus-visible]:outline-2");
    for (const name of ["Wyczyść", "Szukaj"]) {
      expect(within(searchForm()).getByRole("button", { name })).toHaveClass(
        "focus-visible:outline-2",
        "focus-visible:outline-ring",
      );
    }
  });
});
