/** Radii of the fixed and the rolling circle, 10 : 3 (ARC-32): the curve has ten cusps. */
const R = 10;
const r = 3;
/** The rolling circle turns around the fixed one three times before the curve closes. */
const TURNS = r;
const SAMPLES = 1200;

/**
 * Where the curve's centre lies in its box (Figma, ARC-32 section): `right` px in from the right
 * edge, and `y` px below the line `top` down the box.
 */
interface Spot {
  radius: number;
  right: number;
  top: "0%" | "50%";
  y: number;
}

const CORNER: Spot = { radius: 150, right: 40, top: "0%", y: 40 };
const PLACEMENTS = {
  /** Variant B: large, cut off by the hero's edges, clear of the description. */
  hero: { desktop: { radius: 320, right: 284, top: "50%", y: 40 }, mobile: CORNER },
  notFound: { desktop: { radius: 260, right: 404, top: "50%", y: 0 }, mobile: CORNER },
} satisfies Record<string, { desktop: Spot; mobile: Spot }>;

const TONES = {
  /** On the dark hero, the colour of the ornament above the label. */
  inverse: "stroke-inverse-border fill-inverse-border",
  /** On the page background. */
  page: "stroke-accent-border fill-accent-border",
};

/** The pen goes once round the curve in this long, again and again. */
const DURATION = "40s";
/**
 * How much of the curve shows at once (ARC-52): when the pen starts the ninth of the ten arcs,
 * the first arc starts to fade at the pen's pace, so eight arcs stay drawn.
 */
const TRAIL = 0.8;
/** Every how many samples the drawing animation gets a key time. */
const KEY_EVERY = 2;
/** The rolling circle's centre goes round this far; its pen arm turns back R / r as far. */
const ORBIT = 360 * TURNS;
const SPIN = (-ORBIT * R) / r;

/**
 * How many curves draw one round of the line, twelve to an arc (ARC-55). Safari breaks the dash
 * of a path made of hundreds of straight lines into scattered pieces, so the line is drawn with
 * cubic Béziers instead, which it dashes in one piece; a cusp falls on every twelfth curve's end.
 */
const CURVES = 120;

/** The hypocycloid at R = 10 and its direction, at angle `t`. */
const K = (R - r) / r;
const at = (t: number): [number, number] => [
  (R - r) * Math.cos(t) + r * Math.cos(K * t),
  (R - r) * Math.sin(t) - r * Math.sin(K * t),
];
const heading = (t: number): [number, number] => [
  -(R - r) * (Math.sin(t) + Math.sin(K * t)),
  (R - r) * (Math.cos(t) - Math.cos(K * t)),
];

/** The hypocycloid at R = 10, sampled at steady steps of the angle. */
const UNIT_POINTS = Array.from({ length: SAMPLES + 1 }, (_, i) =>
  at((2 * Math.PI * TURNS * i) / SAMPLES),
);

/**
 * One round of the line as cubic Béziers, each [control 1, control 2, end]: every curve meets
 * the hypocycloid at both ends and leaves and reaches them in its direction.
 */
const UNIT_CURVES = Array.from({ length: CURVES }, (_, i): [number, number][] => {
  const step = (2 * Math.PI * TURNS) / CURVES;
  const [t0, t1] = [i * step, (i + 1) * step];
  const [[x0, y0], [x1, y1]] = [at(t0), at(t1)];
  const [[dx0, dy0], [dx1, dy1]] = [heading(t0), heading(t1)];
  return [
    [x0 + (dx0 * step) / 3, y0 + (dy0 * step) / 3],
    [x1 - (dx1 * step) / 3, y1 - (dy1 * step) / 3],
    [x1, y1],
  ];
});

/**
 * Where the pen is along the line over one round. The pen moves at a steady angle, not a steady
 * speed (it slows into each cusp), so its place follows the angle through key times, not a
 * straight line. The fractions do not depend on the radius.
 *
 * The path goes round the curve twice and shows one dash, TRAIL long, ending at the pen. The first
 * round grows the dash from the path's start; each round after it runs along the second lap, so the
 * dash's tail wraps back over the first. The gap is long enough that no other dash shows.
 */
const DRAWING = (() => {
  let sum = 0;
  const lengths = UNIT_POINTS.map(([x, y], i) => {
    const [px, py] = UNIT_POINTS[i - 1] ?? [x, y];
    return (sum += Math.hypot(x - px, y - py));
  });
  const keys = lengths.filter((_, i) => i % KEY_EVERY === 0);
  const offsets = (lap: number) =>
    keys.map((length) => (TRAIL - lap - length / sum).toFixed(5)).join(";");
  return {
    keyTimes: keys.map((_, i) => ((i * KEY_EVERY) / SAMPLES).toFixed(4)).join(";"),
    first: offsets(0),
    next: offsets(1),
    dashArray: `${String(TRAIL)} ${String(2 + TRAIL)}`,
  };
})();

/**
 * The line as a path around (0, 0), its cusps on a circle of `radius`, twice round; built once per
 * radius.
 */
const paths = new Map<number, string>();
function linePath(radius: number): string {
  const point = ([x, y]: [number, number]) =>
    `${((x * radius) / R).toFixed(2)} ${((y * radius) / R).toFixed(2)}`;
  const d =
    paths.get(radius) ??
    [
      `M ${point(at(0))}`,
      ...[...UNIT_CURVES, ...UNIT_CURVES].map((curve) => `C ${curve.map(point).join(" ")}`),
    ].join(" ");
  paths.set(radius, d);
  return d;
}

/**
 * The curve with its fixed circle, the rolling circle and its pen. The roller is two nested turns:
 * its centre goes round the fixed circle three times, and the pen arm turns back 10/3 as fast in
 * that frame, so the pen stays on the line. Each round ends where it began, so the roller simply
 * repeats. The line and the roller run on the same SVG clock, so they stay in step. With reduced
 * motion the whole curve shows at once, without the roller.
 */
function Figure({ spot, className }: { spot: Spot; className: string }) {
  const rolling = (r * spot.radius) / R;
  const centre = ((R - r) * spot.radius) / R;
  return (
    <svg x="100%" y={spot.top} overflow="visible" className={className}>
      <g
        data-slot="hypocycloid-figure"
        transform={`translate(${String(-spot.right)} ${String(spot.y)})`}
      >
        <circle r={spot.radius} fill="none" strokeOpacity={0.24} />
        <path
          data-slot="hypocycloid-line"
          className="motion-reduce:[stroke-dasharray:none]"
          d={linePath(spot.radius)}
          fill="none"
          pathLength={2}
          strokeDasharray={DRAWING.dashArray}
          strokeDashoffset={TRAIL}
        >
          <animate
            attributeName="stroke-dashoffset"
            values={DRAWING.first}
            keyTimes={DRAWING.keyTimes}
            dur={DURATION}
            fill="freeze"
          />
          <animate
            attributeName="stroke-dashoffset"
            values={DRAWING.next}
            keyTimes={DRAWING.keyTimes}
            begin={DURATION}
            dur={DURATION}
            repeatCount="indefinite"
          />
        </path>
        <g className="motion-reduce:hidden" strokeOpacity={0.48}>
          <g>
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0"
              to={String(ORBIT)}
              dur={DURATION}
              repeatCount="indefinite"
            />
            <g>
              <animateTransform
                attributeName="transform"
                type="rotate"
                from={`0 ${String(centre)} 0`}
                to={`${String(SPIN)} ${String(centre)} 0`}
                dur={DURATION}
                repeatCount="indefinite"
              />
              <circle data-slot="hypocycloid-centre" cx={centre} r={rolling} fill="none" />
              <line x1={centre} x2={centre + rolling} />
              <circle data-slot="hypocycloid-pen" cx={centre + rolling} r={2.5} stroke="none" />
            </g>
          </g>
        </g>
      </g>
    </svg>
  );
}

/**
 * ARC-32: a hypocycloid, R : r = 10 : 3, that draws itself slowly round and round, eight of its
 * ten arcs showing behind the pen once the first round is nearly done (ARC-52). It fills
 * its `relative overflow-hidden` parent, behind the content, and is decoration only.
 */
export function Hypocycloid({
  tone,
  placement,
}: {
  tone: keyof typeof TONES;
  placement: keyof typeof PLACEMENTS;
}) {
  const { desktop, mobile } = PLACEMENTS[placement];
  return (
    <svg
      aria-hidden="true"
      data-slot="hypocycloid"
      className={`pointer-events-none absolute inset-0 size-full overflow-visible ${TONES[tone]}`}
      strokeWidth={1}
      strokeLinecap="round"
    >
      <Figure spot={mobile} className="md:hidden" />
      <Figure spot={desktop} className="hidden md:block" />
    </svg>
  );
}
