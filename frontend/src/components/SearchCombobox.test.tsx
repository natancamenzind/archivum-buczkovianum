import { act, fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

const SUGGESTIONS = [
  { type: "work", title: "Czarny potok", url: "/works/czarny-potok" },
  { type: "tag", title: "Czarny las", url: "/tags/czarny-las" },
];

let queries: string[];

function headerField(): HTMLElement {
  return within(screen.getByRole("banner")).getByRole("combobox", { name: "Szukaj w archiwum" });
}

function pageField(): HTMLElement {
  return within(screen.getByRole("search", { name: "Wyszukiwanie" })).getByRole("combobox", {
    name: "Szukaj w archiwum",
  });
}

const WORK = "Czarny potok Utwór";
const TAG = "Czarny las Tag";

/** Types `value` into `field` and waits for the list; returns the suggestions' names. */
async function suggestionsFor(field: HTMLElement, value: string): Promise<string[]> {
  field.focus();
  fireEvent.change(field, { target: { value } });
  const list = await screen.findByRole("listbox", { name: "Podpowiedzi" });
  return within(list)
    .getAllByRole("option")
    .map((option) => option.textContent);
}

function option(name: string): HTMLElement {
  return screen.getByRole("option", { name });
}

function activeNavItem(): string | null {
  const nav = screen.getByRole("navigation", { name: "Menu główne" });
  return nav.querySelector('[aria-current="page"]')?.textContent ?? null;
}

describe("SearchCombobox", () => {
  beforeEach(() => {
    queries = [];
    server.use(
      http.get("*/api/about/", () => HttpResponse.json({ intro: "", project: "", team: [] })),
      http.get("*/api/search/autocomplete/", ({ request }) => {
        const q = new URL(request.url).searchParams.get("q") ?? "";
        queries.push(q);
        return HttpResponse.json(q.startsWith("czarny") ? SUGGESTIONS : []);
      }),
    );
  });

  it("US-RA-17 AC1: typing in the header field suggests works and tags", async () => {
    const { container } = renderRoute("/about");

    expect(await suggestionsFor(headerField(), "czarny p")).toEqual([WORK, TAG]);
    expect(queries.at(-1)).toBe("czarny p");
    expect(headerField()).toHaveAttribute("aria-expanded", "true");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-17 AC1: typing in the search page's field suggests works and tags", async () => {
    const { container } = renderRoute("/search");

    expect(await suggestionsFor(pageField(), "czarny")).toEqual([WORK, TAG]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-17 AC1: one letter asks for no suggestions", async () => {
    renderRoute("/about");

    fireEvent.change(headerField(), { target: { value: "c" } });
    await act(() => new Promise((resolve) => setTimeout(resolve, 400)));

    expect(queries).toEqual([]);
    expect(headerField()).toHaveAttribute("aria-expanded", "false");
  });

  it("US-RA-17 AC1: without matches the list stays closed", async () => {
    renderRoute("/about");
    await suggestionsFor(headerField(), "czarny");

    fireEvent.change(headerField(), { target: { value: "wertepy" } });

    expect(await screen.findByRole("combobox", { expanded: false })).toBe(headerField());
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("US-RA-17 AC1: the field asks only once the typing pauses", async () => {
    renderRoute("/about");
    const field = headerField();

    for (const value of ["cz", "cza", "czar", "czarn"]) {
      fireEvent.change(field, { target: { value } });
    }
    await suggestionsFor(field, "czarny");

    expect(queries).toEqual(["czarny"]);
  });

  it("US-RA-17 AC1: the search page's query asks for nothing until the reader types", async () => {
    renderRoute("/search?q=czarny");

    pageField().focus();
    await act(() => new Promise((resolve) => setTimeout(resolve, 400)));

    expect(queries).toEqual([]);
    fireEvent.keyDown(pageField(), { key: "ArrowDown" });
    expect(await screen.findByRole("listbox", { name: "Podpowiedzi" })).toBeInTheDocument();
    expect(queries).toEqual(["czarny"]);
  });

  it("US-RA-17 AC2: clicking a suggestion opens its page", async () => {
    const { router } = renderRoute("/about");

    await suggestionsFor(headerField(), "czarny");
    fireEvent.click(option(WORK));

    expect(router.state.location.pathname).toBe("/works/czarny-potok");
    expect(activeNavItem()).toBe("Utwory");
    expect(headerField()).toHaveValue("");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("US-RA-17 AC2: choosing a suggestion with the keyboard opens its page", async () => {
    const { container, router } = renderRoute("/about");
    const field = headerField();

    await suggestionsFor(field, "czarny");
    fireEvent.keyDown(field, { key: "ArrowDown" });
    fireEvent.keyDown(field, { key: "ArrowDown" });

    expect(field).toHaveAttribute("aria-activedescendant", option(TAG).id);
    expect(option(TAG)).toHaveAttribute("aria-selected", "true");
    expect(option(WORK)).toHaveAttribute("aria-selected", "false");
    expect(await axeViolations(container)).toEqual([]);
    fireEvent.keyDown(field, { key: "Enter" });
    expect(router.state.location.pathname).toBe("/tags/czarny-las");
  });

  it("US-RA-17 AC2: pointing at a suggestion makes it the active one until the pointer leaves", async () => {
    renderRoute("/about");

    await suggestionsFor(headerField(), "czarny");
    fireEvent.mouseMove(option(TAG));
    expect(headerField()).toHaveAttribute("aria-activedescendant", option(TAG).id);

    fireEvent.mouseLeave(screen.getByRole("listbox"));
    expect(headerField()).not.toHaveAttribute("aria-activedescendant");
    expect(fireEvent.keyDown(headerField(), { key: "Enter" })).toBe(true);
  });

  it("US-RA-17 AC1: on the search page, the edited query is asked for, not the old one", async () => {
    renderRoute("/search?q=czarny");

    expect(await suggestionsFor(pageField(), "czarny p")).toEqual([WORK, TAG]);

    expect(queries).toEqual(["czarny p"]);
  });

  it("US-RA-17 AC1: arrows in a one-letter field move the caret as usual", async () => {
    renderRoute("/about");

    fireEvent.change(headerField(), { target: { value: "c" } });

    expect(fireEvent.keyDown(headerField(), { key: "ArrowDown" })).toBe(true);
    await act(() => new Promise((resolve) => setTimeout(resolve, 400)));
    expect(queries).toEqual([]);
  });

  it("US-RA-17 AC2: Enter while composing a letter chooses nothing", async () => {
    const { router } = renderRoute("/about");
    const field = headerField();

    await suggestionsFor(field, "czarny");
    fireEvent.keyDown(field, { key: "ArrowDown" });
    fireEvent.keyDown(field, { key: "Enter", isComposing: true });

    expect(router.state.location.pathname).toBe("/about");
  });

  it("US-RA-17 AC2: a suggestion on the search page opens its page", async () => {
    const { router } = renderRoute("/search");

    await suggestionsFor(pageField(), "czarny");
    fireEvent.click(option(TAG));

    expect(router.state.location.pathname).toBe("/tags/czarny-las");
    expect(screen.queryByRole("search", { name: "Wyszukiwanie" })).toBeNull();
  });

  it("US-RA-17 AC2: the arrows wrap around the list", async () => {
    renderRoute("/about");
    const field = headerField();

    await suggestionsFor(field, "czarny");
    fireEvent.keyDown(field, { key: "ArrowUp" });
    expect(field).toHaveAttribute("aria-activedescendant", option(TAG).id);
    fireEvent.keyDown(field, { key: "ArrowDown" });
    expect(field).toHaveAttribute("aria-activedescendant", option(WORK).id);
  });

  it("US-RA-14 AC1: Enter without a chosen suggestion still searches", async () => {
    renderRoute("/about");

    await suggestionsFor(headerField(), "czarny");
    // The key is not prevented, so the browser submits the form.
    expect(fireEvent.keyDown(headerField(), { key: "Enter" })).toBe(true);
    fireEvent.submit(within(screen.getByRole("banner")).getByRole("search"));

    expect(pageField()).toHaveValue("czarny");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("US-RA-17 AC1: Escape closes the list and keeps the text", async () => {
    renderRoute("/about");
    const field = headerField();

    await suggestionsFor(field, "czarny");
    fireEvent.keyDown(field, { key: "Escape" });

    expect(screen.queryByRole("listbox")).toBeNull();
    expect(field).toHaveValue("czarny");
    expect(field).not.toHaveAttribute("aria-activedescendant");
    fireEvent.keyDown(field, { key: "ArrowDown" });
    expect(screen.getByRole("listbox", { name: "Podpowiedzi" })).toBeInTheDocument();
  });

  it("US-RA-17 AC1: leaving the field closes the list", async () => {
    renderRoute("/about");
    const field = headerField();

    await suggestionsFor(field, "czarny");
    fireEvent.blur(field);

    expect(screen.queryByRole("listbox")).toBeNull();
  });
});
