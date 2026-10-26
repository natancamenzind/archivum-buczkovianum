import { describe, expect, it } from "vitest";

import { formatCount, nouns, plural } from "./pl";

describe("plural", () => {
  it.each([
    [1, "fragment"],
    [2, "fragmenty"],
    [3, "fragmenty"],
    [4, "fragmenty"],
    [5, "fragmentów"],
    [11, "fragmentów"],
    [12, "fragmentów"],
    [13, "fragmentów"],
    [14, "fragmentów"],
    [21, "fragmentów"],
    [22, "fragmenty"],
    [23, "fragmenty"],
    [24, "fragmenty"],
    [25, "fragmentów"],
    [101, "fragmentów"],
    [102, "fragmenty"],
    [112, "fragmentów"],
    [114, "fragmentów"],
    [122, "fragmenty"],
  ])("uses the right form for %i", (count, expected) => {
    expect(plural(count, nouns.fragment)).toBe(expected);
  });

  it("uses the 'many' form for zero", () => {
    expect(plural(0, nouns.fragment)).toBe("fragmentów");
  });

  it("uses the 'many' form for fractions", () => {
    expect(plural(1.5, nouns.fragment)).toBe("fragmentów");
  });

  it("uses the form of the absolute value for negative counts", () => {
    expect(plural(-1, nouns.fragment)).toBe("fragment");
    expect(plural(-3, nouns.fragment)).toBe("fragmenty");
  });

  it("matches the occurrence forms from design/rules.md", () => {
    expect(plural(1, nouns.occurrence)).toBe("wystąpienie");
    expect(plural(3, nouns.occurrence)).toBe("wystąpienia");
    expect(plural(7, nouns.occurrence)).toBe("wystąpień");
  });
});

describe("formatCount", () => {
  it("joins the count and the noun", () => {
    expect(formatCount(24, nouns.fragment)).toBe("24 fragmenty");
    expect(formatCount(62, nouns.fragment)).toBe("62 fragmenty");
    expect(formatCount(12, nouns.tag)).toBe("12 tagów");
    expect(formatCount(1, nouns.note)).toBe("1 zapisek");
  });
});
