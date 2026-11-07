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

/** The hypocycloid as a path around (0, 0), its cusps on a circle of `radius`. */
function linePath(radius: number): string {
  const scale = radius / R;
  const end = 2 * Math.PI * TURNS;
  const k = (R - r) / r;
  const points = Array.from({ length: SAMPLES + 1 }, (_, i) => {
    const t = (end * i) / SAMPLES;
    const x = ((R - r) * Math.cos(t) + r * Math.cos(k * t)) * scale;
    const y = ((R - r) * Math.sin(t) - r * Math.sin(k * t)) * scale;
    return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  });
  return points.join(" ");
}

/**
 * The curve with its fixed circle and, while it draws, the rolling circle and its pen. The roller
 * is two nested turns: its centre goes round the fixed circle three times, and the pen arm turns
 * back 10/3 as fast in that frame, so the pen stays on the line (animation in index.css).
 */
function Figure({ spot, className }: { spot: Spot; className: string }) {
  const scale = spot.radius / R;
  return (
    <svg x="100%" y={spot.top} overflow="visible" className={className}>
      <g transform={`translate(${String(-spot.right)} ${String(spot.y)})`}>
        <circle r={spot.radius} fill="none" strokeOpacity={0.24} />
        <path
          data-slot="hypocycloid-line"
          className="hypocycloid-line"
          d={linePath(spot.radius)}
          fill="none"
          pathLength={1}
        />
        <g className="hypocycloid-roller" strokeOpacity={0.48}>
          <g className="hypocycloid-orbit">
            <g transform={`translate(${String((R - r) * scale)} 0)`}>
              <g className="hypocycloid-spin">
                <circle r={r * scale} fill="none" />
                <line x2={r * scale} />
                <circle cx={r * scale} r={2.5} stroke="none" />
              </g>
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
