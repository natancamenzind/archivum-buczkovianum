import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Hypocycloid } from "@/components/Hypocycloid";

/** The points of a path made of one move and straight lines. */
function points(d: string): [number, number][] {
  return [...d.matchAll(/[ML] (-?[\d.]+) (-?[\d.]+)/g)].map((m) => [Number(m[1]), Number(m[2])]);
}

describe("Hypocycloid", () => {
  it("ARC-32: the line is a closed curve with ten cusps on the fixed circle", () => {
    const { container } = render(<Hypocycloid tone="inverse" placement="hero" />);

    for (const line of container.querySelectorAll<SVGPathElement>("[data-slot=hypocycloid-line]")) {
      const pts = points(line.getAttribute("d") ?? "");
      const fixed = Number(line.previousElementSibling?.getAttribute("r"));
      const radii = pts.map(([x, y]) => Math.hypot(x, y));
      expect(pts.at(0)).toEqual(pts.at(-1));
      // A cusp is where the line comes out furthest; the closing point repeats the first.
      const ring = radii.slice(0, -1);
      const at = (i: number) => ring.at(i % ring.length) ?? NaN;
      const cusps = ring.filter((rad, i) => rad > at(i - 1) && rad >= at(i + 1));
      expect(cusps).toHaveLength(10);
      for (const cusp of cusps) expect(cusp).toBeCloseTo(fixed, 1);
    }
  });
});
