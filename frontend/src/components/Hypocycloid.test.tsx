import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Hypocycloid } from "@/components/Hypocycloid";

/** The points a path made of one move and cubic Béziers goes through: where each part ends. */
function points(d: string): [number, number][] {
  return [...d.matchAll(/(?:M|C(?: -?[\d.]+ -?[\d.]+){2}) (-?[\d.]+) (-?[\d.]+)/g)].map((m) => [
    Number(m[1]),
    Number(m[2]),
  ]);
}

/** The value an animation with `values` and `keyTimes` has at `time`, a fraction of its duration. */
function valueAt(animation: Element | null | undefined, time: number): number {
  const values = (animation?.getAttribute("values") ?? "").split(";").map(Number);
  const times = (animation?.getAttribute("keyTimes") ?? "").split(";").map(Number);
  const i = times.findIndex((t) => t >= time);
  if (times[i] === time) return values[i] ?? NaN;
  const [t0, t1] = [times[i - 1] ?? NaN, times[i] ?? NaN];
  const [v0, v1] = [values[i - 1] ?? NaN, values[i] ?? NaN];
  return v0 + ((v1 - v0) * (time - t0)) / (t1 - t0);
}

/** The point `fraction` of the way along the path through `pts`. */
function pointAlong(pts: [number, number][], fraction: number): [number, number] {
  const segments = pts.slice(1).map(([x1, y1], i) => {
    const [x0, y0] = pts[i] ?? [NaN, NaN];
    return { x0, y0, x1, y1, step: Math.hypot(x1 - x0, y1 - y0) };
  });
  let left = fraction * segments.reduce((sum, { step }) => sum + step, 0);
  for (const { x0, y0, x1, y1, step } of segments) {
    if (left <= step) return [x0 + ((x1 - x0) * left) / step, y0 + ((y1 - y0) * left) / step];
    left -= step;
  }
  return pts.at(-1) ?? [NaN, NaN];
}

/** The figure's line and its two drawing animations: the first loop, then every loop after it. */
function drawing(figure: Element) {
  const line = figure.querySelector("[data-slot=hypocycloid-line]");
  const [first, next] = [
    ...(line?.querySelectorAll("animate[attributeName=stroke-dashoffset]") ?? []),
  ];
  const [dash = NaN, gap = NaN] = (line?.getAttribute("stroke-dasharray") ?? "")
    .split(" ")
    .map(Number);
  const loops = Number(line?.getAttribute("pathLength"));
  /** The drawn stretch of the line at `time`, in curves from the path's start, clipped to it. */
  const visible = (animation: Element | undefined, time: number) => {
    const start = -valueAt(animation, time);
    expect(start + dash + gap).toBeGreaterThanOrEqual(loops); // the next dash stays off the path
    return { from: Math.max(0, start), to: Math.min(loops, start + dash) };
  };
  return { line, first, next, loops, visible };
}

const rotate = ([x, y]: [number, number], degrees: number): [number, number] => {
  const a = (degrees * Math.PI) / 180;
  return [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];
};

describe("Hypocycloid", () => {
  it("ARC-32: the line is a closed curve with ten cusps on the fixed circle", () => {
    const { container } = render(<Hypocycloid tone="inverse" placement="hero" />);

    for (const line of container.querySelectorAll<SVGPathElement>("[data-slot=hypocycloid-line]")) {
      // The path goes round the curve twice, so a drawn stretch can run on past its start.
      const all = points(line.getAttribute("d") ?? "");
      const pts = all.slice(0, (all.length + 1) / 2);
      expect(all.slice((all.length - 1) / 2)).toEqual(pts);
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

  it("ARC-55: the line is drawn with curves, not straight lines, so Safari dashes it in one piece", () => {
    const { container } = render(<Hypocycloid tone="inverse" placement="hero" />);

    for (const line of container.querySelectorAll("[data-slot=hypocycloid-line]")) {
      const commands = (line.getAttribute("d") ?? "").match(/[A-Za-z]/g) ?? [];
      expect(commands[0]).toBe("M");
      expect(new Set(commands.slice(1))).toEqual(new Set(["C"]));
    }
  });

  it("ARC-32: while it draws, the line ends at the rolling circle's pen", () => {
    const { container } = render(<Hypocycloid tone="page" placement="notFound" />);

    const figures = container.querySelectorAll("[data-slot=hypocycloid-figure]");
    expect(figures).toHaveLength(2);
    for (const figure of figures) {
      const { line, first, next, loops, visible } = drawing(figure);
      const pts = points(line?.getAttribute("d") ?? "");
      const [orbit, spin] = [...figure.querySelectorAll("animateTransform")];
      const centre = Number(
        figure.querySelector("[data-slot=hypocycloid-centre]")?.getAttribute("cx"),
      );
      const arm =
        Number(figure.querySelector("[data-slot=hypocycloid-pen]")?.getAttribute("cx")) - centre;
      const turn = (el: Element | undefined) => Number.parseFloat(el?.getAttribute("to") ?? "");

      const draws = [first, next].flatMap((draw) =>
        [0.07, 0.13, 0.5, 0.77, 0.95].map((time) => ({ draw, time })),
      );
      for (const { draw, time } of draws) {
        const drawn = pointAlong(pts, visible(draw, time).to / loops);
        const orbitAngle = turn(orbit) * time;
        const [cx, cy] = rotate([centre, 0], orbitAngle);
        const [ax, ay] = rotate([arm, 0], orbitAngle + turn(spin) * time);
        expect(Math.hypot(drawn[0] - (cx + ax), drawn[1] - (cy + ay))).toBeLessThan(2);
      }
    }
  });

  it("ARC-52: from the ninth arc on, the first arcs fade as fast as new ones draw, forever", () => {
    const { container } = render(<Hypocycloid tone="inverse" placement="hero" />);

    for (const figure of container.querySelectorAll("[data-slot=hypocycloid-figure]")) {
      const { first, next, visible } = drawing(figure);
      const arcs = (stretch: { from: number; to: number }) => (stretch.to - stretch.from) * 10;

      // Up to the ninth of the ten arcs, the line only grows from its start.
      expect(visible(first, 0).to).toBeCloseTo(0, 3);
      for (const time of [0.1, 0.5, 0.79]) expect(visible(first, time).from).toBe(0);
      expect(visible(first, 0.8).to).toBeCloseTo(0.8, 3);
      // From then on, eight arcs always show: the tail keeps pace with the pen.
      for (const time of [0.85, 0.9, 1]) expect(arcs(visible(first, time))).toBeCloseTo(8, 3);
      for (const time of [0, 0.25, 0.5, 0.75, 1])
        expect(arcs(visible(next, time))).toBeCloseTo(8, 3);

      // The repeated loop takes over where the first one ends and ends one whole curve on.
      expect(next?.getAttribute("begin")).toBe(first?.getAttribute("dur"));
      expect(next?.getAttribute("dur")).toBe(first?.getAttribute("dur"));
      expect(next?.getAttribute("repeatCount")).toBe("indefinite");
      expect(visible(next, 0).from).toBeCloseTo(visible(first, 1).from, 5);
      expect(visible(next, 1).from - visible(next, 0).from).toBeCloseTo(1, 5);

      // The rolling circle never stops or fades out.
      for (const turn of figure.querySelectorAll("animateTransform")) {
        expect(turn.getAttribute("repeatCount")).toBe("indefinite");
      }
      expect(figure.querySelector("animate[attributeName=opacity]")).toBeNull();
    }
  });

  it("ARC-32: with reduced motion the finished curve shows at once, without the roller", () => {
    const { container } = render(<Hypocycloid tone="inverse" placement="hero" />);

    for (const figure of container.querySelectorAll("[data-slot=hypocycloid-figure]")) {
      expect(figure.querySelector("[data-slot=hypocycloid-line]")).toHaveClass(
        "motion-reduce:[stroke-dasharray:none]",
      );
      expect(
        figure.querySelector("[data-slot=hypocycloid-pen]")?.closest(".motion-reduce\\:hidden"),
      ).not.toBeNull();
    }
  });
});
