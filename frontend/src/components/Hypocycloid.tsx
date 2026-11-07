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

/** One drawing of the line takes this long; the roller then fades out. */
const DURATION = "40s";
/** Every how many samples the drawing animation gets a key time. */
const KEY_EVERY = 2;

/**
 * The hypocycloid as a path around (0, 0), its cusps on a circle of `radius`, and how much of it
 * is drawn over time. The pen moves at a steady angle, not a steady speed (it slows into each
 * cusp), so the drawn length follows the angle through key times, not a straight line.
 */
function line(radius: number): { d: string; keyTimes: string; values: string } {
  const scale = radius / R;
  const end = 2 * Math.PI * TURNS;
  const k = (R - r) / r;
  const points = Array.from({ length: SAMPLES + 1 }, (_, i) => {
    const t = (end * i) / SAMPLES;
    return [
      ((R - r) * Math.cos(t) + r * Math.cos(k * t)) * scale,
      ((R - r) * Math.sin(t) - r * Math.sin(k * t)) * scale,
    ] as const;
  });
  const lengths = [0];
  points.slice(1).forEach(([x, y], i) => {
    const [px, py] = points[i] ?? [x, y];
    lengths.push((lengths.at(-1) ?? 0) + Math.hypot(x - px, y - py));
  });
  const total = lengths.at(-1) ?? 1;
  const keys = lengths.filter((_, i) => i % KEY_EVERY === 0);
  return {
    d: points
      .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`)
      .join(" "),
    keyTimes: keys.map((_, i) => ((i * KEY_EVERY) / SAMPLES).toFixed(4)).join(";"),
    values: keys.map((length) => (1 - length / total).toFixed(5)).join(";"),
  };
}

/**
 * The curve with its fixed circle and, while it draws, the rolling circle and its pen. The roller
 * is two nested turns: its centre goes round the fixed circle three times, and the pen arm turns
 * back 10/3 as fast in that frame, so the pen stays on the line. The line and the roller run on
 * the same SVG clock, so they stay in step; index.css handles reduced motion.
 */
function Figure({ spot, className }: { spot: Spot; className: string }) {
  const scale = spot.radius / R;
  const centre = (R - r) * scale;
  const { d, keyTimes, values } = line(spot.radius);
  return (
    <svg x="100%" y={spot.top} overflow="visible" className={className}>
      <g
        data-slot="hypocycloid-figure"
        transform={`translate(${String(-spot.right)} ${String(spot.y)})`}
      >
        <circle r={spot.radius} fill="none" strokeOpacity={0.24} />
        <path
          data-slot="hypocycloid-line"
          className="hypocycloid-line"
          d={d}
          fill="none"
          pathLength={1}
          strokeDasharray={1}
        >
          <animate
            attributeName="stroke-dashoffset"
            values={values}
            keyTimes={keyTimes}
            dur={DURATION}
            fill="freeze"
          />
        </path>
        <g className="hypocycloid-roller" strokeOpacity={0.48}>
          <animate
            attributeName="opacity"
            from="1"
            to="0"
            begin={DURATION}
            dur="0.6s"
            fill="freeze"
          />
          <g>
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0"
              to="1080"
              dur={DURATION}
              fill="freeze"
            />
            <g>
              <animateTransform
                attributeName="transform"
                type="rotate"
                from={`0 ${String(centre)} 0`}
                to={`-3600 ${String(centre)} 0`}
                dur={DURATION}
                fill="freeze"
              />
              <circle data-slot="hypocycloid-centre" cx={centre} r={r * scale} fill="none" />
              <line x1={centre} x2={centre + r * scale} />
              <circle data-slot="hypocycloid-pen" cx={centre + r * scale} r={2.5} stroke="none" />
            </g>
          </g>
        </g>
      </g>
    </svg>
  );
}

/**
 * ARC-32: a hypocycloid, R : r = 10 : 3, that draws itself slowly once and then stays. It fills
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
