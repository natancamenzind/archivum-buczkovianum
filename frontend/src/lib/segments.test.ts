import { describe, expect, it } from "vitest";

import { segments } from "./segments";

describe("segments", () => {
  it("splits the text at every fragment boundary, overlaps included", () => {
    expect(
      segments(10, [
        { id: 1, start: 2, end: 6 },
        { id: 2, start: 4, end: 8 },
      ]),
    ).toEqual([
      { start: 0, end: 2, ids: [] },
      { start: 2, end: 4, ids: [1] },
      { start: 4, end: 6, ids: [1, 2] },
      { start: 6, end: 8, ids: [2] },
      { start: 8, end: 10, ids: [] },
    ]);
  });

  it("also splits at the cuts, so no segment crosses a page", () => {
    expect(segments(10, [{ id: 1, start: 2, end: 8 }], [0, 5])).toEqual([
      { start: 0, end: 2, ids: [] },
      { start: 2, end: 5, ids: [1] },
      { start: 5, end: 8, ids: [1] },
      { start: 8, end: 10, ids: [] },
    ]);
  });

  it("#9: clamps a fragment left past the end of a changed text", () => {
    expect(
      segments(6, [
        { id: 1, start: 4, end: 20 },
        { id: 2, start: 9, end: 12 },
      ]),
    ).toEqual([
      { start: 0, end: 4, ids: [] },
      { start: 4, end: 6, ids: [1] },
    ]);
  });

  it("gives an empty text no segments", () => {
    expect(segments(0, [{ id: 1, start: 0, end: 3 }])).toEqual([]);
  });
});
