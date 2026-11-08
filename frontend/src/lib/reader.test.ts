import { describe, expect, it } from "vitest";

import { findMatches, layoutPages, matchAt, pageOf } from "./reader";

describe("pageOf", () => {
  it("is the last page starting at or before an offset, and 1 for a text without pages", () => {
    expect(pageOf([0, 10, 20], 15)).toBe(2);
    expect(pageOf([0, 10, 20], 20)).toBe(3);
    expect(pageOf([], 5)).toBe(1);
  });
});

describe("findMatches", () => {
  it("finds every word in any case, and nothing for a blank term", () => {
    expect(findMatches("Las, las i przelaski.", "las")).toEqual([
      { start: 0, end: 3 },
      { start: 5, end: 8 },
    ]);
    expect(findMatches("Las", "  ")).toEqual([]);
  });

  it("ARC-59: finds every form of a word from its start, covering the whole word", () => {
    const text = "Wertepy, wertepami i przewertepy.";

    expect(findMatches(text, "wertep").map((match) => text.slice(match.start, match.end))).toEqual([
      "Wertepy",
      "wertepami",
    ]);
  });

  it("ARC-59: finds each word of a phrase from its start, across a line break", () => {
    const text = "Druga strona\ntekstu.";

    expect(findMatches(text, "str  tek")).toEqual([{ start: 6, end: 19 }]);
  });
});

describe("matchAt", () => {
  const matches = [
    { start: 2, end: 5 },
    { start: 10, end: 14 },
    { start: 20, end: 22 },
  ];

  it("is the index of the match holding a range, or -1", () => {
    expect(matchAt(matches, 10, 12)).toBe(1);
    expect(matchAt(matches, 20, 22)).toBe(2);
    expect(matchAt(matches, 2, 3)).toBe(0);
    expect(matchAt(matches, 0, 2)).toBe(-1);
    expect(matchAt(matches, 6, 9)).toBe(-1);
    expect(matchAt(matches, 13, 16)).toBe(-1);
    expect(matchAt([], 0, 1)).toBe(-1);
  });
});

describe("layoutPages", () => {
  it("splits pages into paragraphs at blank lines, leaving the blank lines out", () => {
    const text = "Pierwszy.\n\nDrugi\nwiersz.\n \nTrzeci.Strona dwa.";
    const pages = layoutPages(text, [0, 34], [], []);

    const paragraphs = pages.map((page) =>
      page.paragraphs.map((paragraph) =>
        paragraph.segments.map((segment) => text.slice(segment.start, segment.end)).join(""),
      ),
    );
    expect(paragraphs).toEqual([["Pierwszy.", "Drugi\nwiersz.", "Trzeci."], ["Strona dwa."]]);
    expect(pages[0]?.paragraphs.map((paragraph) => paragraph.start)).toEqual([0, 11, 27]);
  });

  it("puts each fragment on the page it starts on, in text order, clamped to the text", () => {
    const fragments = [
      { id: 2, start: 12, end: 14 },
      { id: 1, start: 1, end: 3 },
      { id: 3, start: 40, end: 50 },
    ];
    const pages = layoutPages("Strona jeden.Strona dwa.", [0, 13], fragments, []);

    expect(pages.map((page) => page.starts.map((fragment) => fragment.id))).toEqual([[1, 2], [3]]);
  });

  it("cuts segments at matches", () => {
    const text = "Las i las.";
    const pages = layoutPages(text, [], [], findMatches(text, "las"));

    expect(
      pages[0]?.paragraphs[0]?.segments.map((segment) => text.slice(segment.start, segment.end)),
    ).toEqual(["Las", " i ", "las", "."]);
  });
});
