import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { type TagCount, TagCloud } from "@/components/TagCloud";
import { axeViolations } from "@/test/render";

function tag(title: string, occurrences: number): TagCount {
  return { slug: title.toLowerCase(), title, occurrences };
}

// The design's sample cloud (design/screens/lista-tagi.md).
const TAGS: TagCount[] = [
  tag("Wojna", 31),
  tag("Wieś", 24),
  tag("Pamięć", 18),
  tag("Podole", 15),
  tag("Ucieczka", 11),
  tag("Epidemia", 7),
  tag("Las", 6),
  tag("Dezerter", 4),
  tag("Pisanie", 3),
  tag("Szkoła", 3),
  tag("Stodoła", 2),
  tag("Zima", 2),
];

function renderCloud(tags: TagCount[] = TAGS) {
  return render(
    <MemoryRouter>
      <TagCloud tags={tags} />
    </MemoryRouter>,
  );
}

function cloudTitles(): string[] {
  return screen.getAllByRole("link").map((link) => link.firstChild?.textContent ?? "");
}

describe("TagCloud", () => {
  it("US-RA-01 AC4: every tag links to its page and names its occurrence count", async () => {
    const { container } = renderCloud([tag("Dezerter", 4), tag("Zima", 1)]);

    expect(screen.getByRole("link", { name: "Dezerter 4 wystąpienia" })).toHaveAttribute(
      "href",
      "/tags/dezerter",
    );
    expect(screen.getByRole("link", { name: "Zima 1 wystąpienie" })).toHaveAttribute(
      "href",
      "/tags/zima",
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it.each([
    [1, 1],
    [3, 1],
    [4, 2],
    [7, 2],
    [8, 3],
    [15, 3],
    [16, 4],
    [25, 4],
    [26, 5],
    [140, 5],
  ])("US-RA-01 AC4: %i occurrences give size %i", async (occurrences, size) => {
    const { container } = renderCloud([tag("Dezerter", occurrences)]);

    expect(screen.getByRole("link")).toHaveClass(`text-chmura-tagow-${String(size)}`);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: the two largest sizes use the accent colour", async () => {
    const { container } = renderCloud([tag("Pamięć", 16), tag("Podole", 15)]);

    expect(screen.getByRole("link", { name: /Pamięć/ })).toHaveClass("text-accent-foreground");
    expect(screen.getByRole("link", { name: /Podole/ })).toHaveClass("text-foreground");
    expect(screen.getByRole("link", { name: /Podole/ })).not.toHaveClass("text-accent-foreground");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: the same data always gives the same cloud, whatever its order", async () => {
    const first = renderCloud();
    const titles = cloudTitles();
    first.unmount();

    const { container } = renderCloud([...TAGS].reverse());

    expect(cloudTitles()).toEqual(titles);
    expect(titles).toHaveLength(TAGS.length);
    expect(new Set(titles)).toEqual(new Set(TAGS.map((item) => item.title)));
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: the largest tags are in the middle row, the smaller in the rows around it", async () => {
    const { container } = renderCloud();

    const rows = screen.getAllByRole("list").map((row) =>
      within(row)
        .getAllByRole("link")
        .map((link) => link.firstChild?.textContent),
    );
    expect(rows).toHaveLength(3);
    const [top, middle, bottom] = rows;
    expect(middle).toHaveLength(4);
    expect(middle).toEqual(expect.arrayContaining(["Wojna", "Wieś", "Pamięć", "Podole"]));
    expect(middle?.slice(1, 3)).toContain("Wojna");
    expect([...(top ?? []), ...(bottom ?? [])]).toHaveLength(8);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: a cloud of one tag has one row", async () => {
    const { container } = renderCloud([tag("Wojna", 31)]);

    expect(screen.getAllByRole("list")).toHaveLength(1);
    expect(await axeViolations(container)).toEqual([]);
  });

  it("US-RA-01 AC4: baselines do not line up: neighbours have different vertical offsets", async () => {
    const { container } = renderCloud();

    for (const row of screen.getAllByRole("list")) {
      const offsets = within(row)
        .getAllByRole("listitem")
        .map((item) => item.className);
      for (let index = 1; index < offsets.length; index += 1) {
        expect(offsets[index]).not.toEqual(offsets[index - 1]);
      }
    }
    expect(await axeViolations(container)).toEqual([]);
  });
});
