import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/api/schema";
import { axeViolations, renderRoute } from "@/test/render";
import { server } from "@/test/server";

type AboutData = components["schemas"]["AboutPage"];

const ABOUT_URL = "*/api/about/";

const ABOUT: AboutData = {
  intro: "Archiwum literackie Leopolda Buczkowskiego.",
  project: "Cel archiwum i zakres zbiorów.\n\nInstytucje partnerskie i finansowanie.",
  team: [
    {
      group: "leadership",
      members: [{ name: "Anna Nowak", role: "Kierowniczka projektu", bio: "Badaczka prozy." }],
    },
    {
      group: "team",
      members: [
        { name: "Jan Kowalski", role: "Redaktor", bio: "Edytor tekstów." },
        { name: "Ewa Wiśniewska", role: "Redaktorka", bio: "Archiwistka." },
      ],
    },
    {
      group: "site",
      members: [{ name: "Piotr Zieliński", role: "Programista", bio: "Autor serwisu." }],
    },
  ],
};

function mockAbout(data: Partial<AboutData> = {}): void {
  server.use(http.get(ABOUT_URL, () => HttpResponse.json({ ...ABOUT, ...data })));
}

function section(name: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 2, name });
  const card = heading.closest<HTMLElement>("[data-slot=card]");
  if (card === null) {
    throw new Error(`"${name}" is not inside a card.`);
  }
  return card;
}

describe("AboutPage", () => {
  it("US-RA-13 AC1: 'O archiwum' in the header opens the page, and no navigation item is active", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    const header = screen.getByRole("banner");
    expect(within(header).getByRole("link", { name: "O archiwum" })).toHaveAttribute(
      "href",
      "/about",
    );
    expect(await screen.findByRole("heading", { level: 2, name: "Zespół" })).toBeVisible();
    const nav = screen.getByRole("navigation", { name: "Menu główne" });
    expect(nav.querySelector('[aria-current="page"]')).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-13 AC2: the hero shows the label, the title 'O archiwum' and the introduction", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    const title = screen.getByRole("heading", { level: 1, name: "O archiwum" });
    const hero = title.closest<HTMLElement>("[data-slot=page-header]");
    if (hero === null) {
      throw new Error("The title is not inside the hero.");
    }
    expect(within(hero).getByText("Archivum Buczkovianum")).toBeVisible();
    expect(
      await within(hero).findByText("Archiwum literackie Leopolda Buczkowskiego."),
    ).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-13 AC2: an empty introduction is not rendered (R-02)", async () => {
    mockAbout({ intro: "  " });

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    const hero = screen
      .getByRole("heading", { level: 1, name: "O archiwum" })
      .closest("[data-slot=page-header]");
    expect(hero?.querySelectorAll("p")).toHaveLength(1);
  });

  it("US-RA-13 AC3: 'O projekcie' shows the project text as paragraphs in a card", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "O projekcie" });
    const project = section("O projekcie");
    expect(within(project).getByText("Cel archiwum i zakres zbiorów.")).toBeVisible();
    expect(within(project).getByText("Instytucje partnerskie i finansowanie.")).toBeVisible();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-13 AC3: without project text, 'O projekcie' is hidden (R-02)", async () => {
    mockAbout({ project: "\n\n" });

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    expect(screen.queryByRole("heading", { name: "O projekcie" })).toBeNull();
  });

  it("US-RA-13 AC4: 'Zespół' lists the three groups in order", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    const groups = within(section("Zespół")).getAllByRole("heading", { level: 3 });
    expect(groups.map((group) => group.textContent)).toEqual([
      "Kierownictwo projektu",
      "Członkowie zespołu",
      "Opracowanie serwisu",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-13 AC4: each member shows name, role and biography, in the API's order", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    const members = within(section("Zespół")).getAllByRole("listitem");
    expect(members.map((member) => member.textContent)).toEqual([
      "Anna NowakKierowniczka projektuBadaczka prozy.",
      "Jan KowalskiRedaktorEdytor tekstów.",
      "Ewa WiśniewskaRedaktorkaArchiwistka.",
      "Piotr ZielińskiProgramistaAutor serwisu.",
    ]);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-13 AC4: an empty role or biography is not rendered (R-02)", async () => {
    mockAbout({
      team: [{ group: "team", members: [{ name: "Jan Kowalski", role: "", bio: "" }] }],
    });

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    const member = within(section("Zespół")).getByRole("listitem");
    expect(member.querySelectorAll("p")).toHaveLength(1);
  });

  it("US-RA-13 AC4: empty groups are hidden (R-02)", async () => {
    mockAbout({ team: ABOUT.team.filter(({ group }) => group !== "team") });

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    expect(screen.getByRole("heading", { level: 3, name: "Kierownictwo projektu" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Członkowie zespołu" })).toBeNull();
    expect(screen.getByRole("heading", { level: 3, name: "Opracowanie serwisu" })).toBeVisible();
  });

  it("US-RA-13 AC4: with every group empty, 'Zespół' is hidden (R-02)", async () => {
    mockAbout({ team: [] });

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "O projekcie" });
    expect(screen.queryByRole("heading", { name: "Zespół" })).toBeNull();
  });

  it("says it is loading, then shows the page", async () => {
    mockAbout();

    const { container } = renderRoute("/about");

    expect(screen.getByRole("status")).toHaveTextContent("Wczytuję stronę…");
    expect(await axeViolations(container)).toEqual([]);
    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("says so when the API fails, keeping the title", async () => {
    server.use(http.get(ABOUT_URL, () => HttpResponse.json({}, { status: 500 })));

    const { container } = renderRoute("/about");

    expect(
      await screen.findByText("Nie udało się wczytać strony. Spróbuj ponownie później."),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "O archiwum" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("follows the mobile grid: page margins, mobile title and card padding", async () => {
    mockAbout();

    renderRoute("/about");

    await screen.findByRole("heading", { level: 2, name: "Zespół" });
    const title = screen.getByRole("heading", { level: 1, name: "O archiwum" });
    expect(title).toHaveClass("text-lora-tytul-strony-mobile", "md:text-lora-tytul-strony");
    expect(title.closest("[data-slot=page-header]")).toHaveClass("px-page-mobile", "md:px-page");
    expect(section("Zespół")).toHaveClass("p-card-mobile", "md:p-card");
  });
});
