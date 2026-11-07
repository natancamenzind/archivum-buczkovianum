import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Hypocycloid } from "@/components/Hypocycloid";

/** The points of a path made of one move and straight lines. */
function points(d: string): [number, number][] {
  return [...d.matchAll(/[ML] (-?[\d.]+) (-?[\d.]+)/g)].map((m) => [Number(m[1]), Number(m[2])]);
}

/** The value an animation with `values` and `keyTimes` has at `time`, a fraction of its duration. */
function valueAt(animation: Element | null | undefined, time: number): number {
  const values = (animation?.getAttribute("values") ?? "").split(";").map(Number);
  const times = (animation?.getAttribute("keyTimes") ?? "").split(";").map(Number);
  const i = times.findIndex((t) => t >= time);
  const [t0, t1] = [times[i - 1] ?? NaN, times[i] ?? NaN];
  const [v0, v1] = [values[i - 1] ?? NaN, values[i] ?? NaN];
  return v0 + ((v1 - v0) * (time - t0)) / (t1 - t0);
}

/** The point `length` px along the path through `pts`. */
function pointAlong(pts: [number, number][], length: number): [number, number] {
  let left = length;
  for (let i = 1; i < pts.length; i++) {
    const [[x0, y0], [x1, y1]] = [pts[i - 1] ?? [NaN, NaN], pts[i] ?? [NaN, NaN]];
    const step = Math.hypot(x1 - x0, y1 - y0);
    if (left <= step) return [x0 + ((x1 - x0) * left) / step, y0 + ((y1 - y0) * left) / step];
    left -= step;
  }
  return pts.at(-1) ?? [NaN, NaN];
}

const rotate = ([x, y]: [number, number], degrees: number): [number, number] => {
  const a = (degrees * Math.PI) / 180;
  return [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];
};

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

  it("ARC-32: while it draws, the line ends at the rolling circle's pen", () => {
    const { container } = render(<Hypocycloid tone="page" placement="notFound" />);

    const figures = container.querySelectorAll("[data-slot=hypocycloid-figure]");
    expect(figures).toHaveLength(2);
    for (const figure of figures) {
      const line = figure.querySelector("[data-slot=hypocycloid-line]");
      const pts = points(line?.getAttribute("d") ?? "");
      const total = pts.slice(1).reduce((sum, [x, y], i) => {
        const [px, py] = pts[i] ?? [NaN, NaN];
        return sum + Math.hypot(x - px, y - py);
      }, 0);
      const draw = line?.querySelector("animate[attributeName=stroke-dashoffset]");
      const [orbit, spin] = [...figure.querySelectorAll("animateTransform")];
      const centre = Number(
        figure.querySelector("[data-slot=hypocycloid-centre]")?.getAttribute("cx"),
      );
      const arm =
        Number(figure.querySelector("[data-slot=hypocycloid-pen]")?.getAttribute("cx")) - centre;
      const turn = (el: Element | undefined) => Number.parseFloat(el?.getAttribute("to") ?? "");

      for (const time of [0.07, 0.13, 0.5, 0.77, 0.95]) {
        const drawn = pointAlong(pts, (1 - valueAt(draw, time)) * total);
        const orbitAngle = turn(orbit) * time;
        const [cx, cy] = rotate([centre, 0], orbitAngle);
        const [ax, ay] = rotate([arm, 0], orbitAngle + turn(spin) * time);
        expect(Math.hypot(drawn[0] - (cx + ax), drawn[1] - (cy + ay))).toBeLessThan(2);
      }
    }
  });
});
