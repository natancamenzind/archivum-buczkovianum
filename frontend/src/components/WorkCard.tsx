import { Link } from "react-router";

import type { components } from "@/api/schema";
import { ArrowUpRightIcon, ImageIcon } from "@/components/icons";
import { Card } from "@/components/ui/card";
import { copy, formatCount, nouns } from "@/copy/pl";
import { cn } from "@/lib/utils";

type Work = components["schemas"]["WorkCard"];

/** The cover, or the placeholder board when the work has none (plan D25). */
function Cover({ work }: { work: Work }) {
  return (
    <div className="flex aspect-4/3 items-center justify-center overflow-hidden rounded-sm bg-media">
      {work.cover_image === "" ? (
        // Hidden from screen readers, so "[Okładka]" does not open every card link's name.
        <div
          data-slot="cover-placeholder"
          aria-hidden="true"
          className="flex flex-col items-center gap-8"
        >
          <ImageIcon className="size-16 text-icon" />
          <p className="text-cousine-metadane-male text-muted-foreground">
            {copy.workCard.coverPlaceholder}
          </p>
        </div>
      ) : (
        <img
          src={work.cover_image}
          alt={work.cover_image_alt}
          className="size-full object-contain"
        />
      )}
    </div>
  );
}

/**
 * "Karta utworu" in design/components/ (US-RA-01 AC3), on the works list and the home page.
 * The whole card links to the work page (R-01). It fills its grid cell, and the grid gives every
 * card the same height, so the footer sits at the bottom whatever the title's length. Hover and
 * keyboard focus lift the card and turn the title to the accent (design/rules.md).
 */
export function WorkCard({ work }: { work: Work }) {
  // Genre and year, leaving out whichever is missing (R-02).
  const meta = [work.genre, work.year === null ? "" : String(work.year)]
    .filter((part) => part !== "")
    .join(" · ");

  return (
    <Link
      to={`/works/${work.slug}`}
      className="group block h-full rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <Card
        className={cn(
          "h-full gap-12 p-16 md:p-16",
          "transition-[translate,box-shadow,border-color] duration-180 ease-out motion-reduce:transition-none",
          "group-hover:-translate-y-4 group-hover:border-accent-border-subtle group-hover:shadow-raised",
          "group-focus-visible:-translate-y-4 group-focus-visible:border-accent-border-subtle group-focus-visible:shadow-raised",
          "motion-reduce:group-hover:translate-y-0 motion-reduce:group-focus-visible:translate-y-0",
        )}
      >
        <Cover work={work} />
        {meta !== "" && <p className="text-cousine-etykieta text-accent-foreground">{meta}</p>}
        <h3 className="text-lora-tytul-elementu text-foreground transition-colors duration-180 ease-out group-hover:text-accent-foreground group-focus-visible:text-accent-foreground motion-reduce:transition-none">
          {work.title}
        </h3>
        <p className="text-lora-tekst-maly text-muted-foreground">{copy.author}</p>
        <div
          data-slot="work-card-footer"
          className="mt-auto flex items-center justify-between border-t border-border pt-12 transition-colors duration-180 ease-out group-hover:border-accent-border-subtle group-focus-visible:border-accent-border-subtle motion-reduce:transition-none"
        >
          {/* Without visible fragments the count is hidden and only the arrow stays (D23). */}
          {work.fragment_count > 0 && (
            <p className="text-cousine-metadane-male text-muted-foreground">
              {formatCount(work.fragment_count, nouns.fragment)}
            </p>
          )}
          <ArrowUpRightIcon className="ml-auto size-16 text-accent-icon" />
        </div>
      </Card>
    </Link>
  );
}
