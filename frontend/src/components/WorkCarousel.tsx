import { useEffect, useRef, useState } from "react";

import { ChevronLeftIcon, ChevronRightIcon } from "@/components/icons";
import { type Work, WorkCard } from "@/components/WorkCard";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

// Each arrow hangs past the row into the section card's padding (ARC-51). Touch screens
// have no hover to show the arrows, and swipe the row instead.
const ARROW = cn(
  "absolute top-1/2 z-10 flex size-48 -translate-y-1/2 items-center justify-center rounded-sm border border-accent-border bg-card text-accent-icon",
  "opacity-0 group-hover/carousel:opacity-100 group-focus-within/carousel:opacity-100 pointer-coarse:hidden",
  "transition-[opacity,background-color] duration-150 ease-out hover:bg-accent motion-reduce:transition-none",
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
);

/**
 * "Karuzela utworów" in design/screens/strona-glowna.md (ARC-20): one row of work cards that
 * scrolls sideways, with 1.5 cards in view on a phone and 4.5 on a desktop, so the cut-off card
 * shows there are more. While the pointer is over the row, or focus is in it, an arrow on each
 * side at half the cards' height scrolls by the whole cards in view; each shows only while the row
 * can scroll its way (ARC-51). The list's padding, taken back
 * by negative margins, keeps the hover lift and the focus ring inside the scroll area; at the
 * bottom it reaches the section card's edge, so the hover shadow is not cut short.
 */
export function WorkCarousel({ works }: { works: Work[] }) {
  const listRef = useRef<HTMLUListElement>(null);
  const [edges, setEdges] = useState({ start: true, end: true });

  useEffect(() => {
    const list = listRef.current;
    if (list === null) {
      return;
    }
    const update = () => {
      setEdges({
        start: list.scrollLeft <= 0,
        end: list.scrollLeft + list.clientWidth >= list.scrollWidth - 1,
      });
    };
    update();
    list.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      list.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [works]);

  const scroll = (direction: 1 | -1) => {
    const list = listRef.current;
    const card = list?.firstElementChild;
    if (list == null || card == null) {
      return;
    }
    const gap = parseFloat(getComputedStyle(list).columnGap) || 0;
    const step = card.getBoundingClientRect().width + gap;
    const cards = Math.max(1, Math.floor(list.clientWidth / step));
    list.scrollBy({ left: direction * cards * step });
  };

  return (
    // The wrapper takes the list's margins, so it spans exactly the cards and the arrows centre on them.
    <div className="group/carousel relative">
      <ul
        ref={listRef}
        data-slot="work-carousel"
        className={cn(
          "flex snap-x snap-mandatory scroll-smooth gap-(--gap) overflow-x-auto motion-reduce:scroll-auto",
          "-mx-4 -mt-8 -mb-card-mobile scroll-px-4 px-4 pt-8 pb-card-mobile md:-mb-card md:pb-card",
          "[--gap:var(--spacing-16)] [--visible:1.5] sm:[--visible:2.5] md:[--gap:var(--spacing-24)] lg:[--visible:3.5] xl:[--visible:4.5]",
        )}
      >
        {works.map((work) => (
          // Each card takes its share of the row, so the next one always shows by half.
          <li
            key={work.slug}
            className="shrink-0 snap-start basis-[calc((100%-(var(--visible)-0.5)*var(--gap))/var(--visible))]"
          >
            <WorkCard work={work} />
          </li>
        ))}
      </ul>
      {!edges.start && (
        <button
          type="button"
          className={cn(ARROW, "-left-16 md:-left-24")}
          aria-label={copy.workCarousel.previous}
          onClick={() => {
            scroll(-1);
          }}
        >
          <ChevronLeftIcon className="size-16" />
        </button>
      )}
      {!edges.end && (
        <button
          type="button"
          className={cn(ARROW, "-right-16 md:-right-24")}
          aria-label={copy.workCarousel.next}
          onClick={() => {
            scroll(1);
          }}
        >
          <ChevronRightIcon className="size-16" />
        </button>
      )}
    </div>
  );
}
