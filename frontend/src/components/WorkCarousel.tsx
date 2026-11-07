import { useEffect, useRef, useState } from "react";

import { ChevronLeftIcon, ChevronRightIcon } from "@/components/icons";
import { type Work, WorkCard } from "@/components/WorkCard";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

const ARROW = cn(
  "flex size-48 items-center justify-center rounded-sm border border-accent-border bg-card text-accent-icon",
  "transition-colors duration-150 ease-out enabled:hover:bg-accent motion-reduce:transition-none",
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
  "disabled:border-border disabled:text-muted-foreground",
);

/**
 * "Karuzela utworów" in design/screens/strona-glowna.md (ARC-20): one row of work cards that
 * scrolls sideways, with 1.5 cards in view on a phone and 4.5 on a desktop, so the cut-off card
 * shows there are more. The arrows below scroll by the whole cards in view; each is disabled at
 * its end of the row, and both are hidden when every card fits. The list's padding, taken back
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
    <div className="flex flex-col gap-16">
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
      {!(edges.start && edges.end) && (
        // Relative, so the arrows paint over the list's bottom padding, kept for the hover shadow.
        <div className="relative flex justify-end gap-8">
          <button
            type="button"
            className={ARROW}
            aria-label={copy.workCarousel.previous}
            disabled={edges.start}
            onClick={() => {
              scroll(-1);
            }}
          >
            <ChevronLeftIcon className="size-16" />
          </button>
          <button
            type="button"
            className={ARROW}
            aria-label={copy.workCarousel.next}
            disabled={edges.end}
            onClick={() => {
              scroll(1);
            }}
          >
            <ChevronRightIcon className="size-16" />
          </button>
        </div>
      )}
    </div>
  );
}
