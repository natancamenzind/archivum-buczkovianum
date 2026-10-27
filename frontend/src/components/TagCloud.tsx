import { Link } from "react-router";

import type { components } from "@/api/schema";
import { formatCount, nouns } from "@/copy/pl";
import { cn } from "@/lib/utils";

export type TagCount = components["schemas"]["TagCount"];

/** The lowest occurrence count of sizes 2 to 5 (US-RA-01 AC4): 1–3, 4–7, 8–15, 16–25, 26+. */
const SIZE_STARTS = [4, 8, 16, 26];

const SIZE_CLASSES = [
  "text-chmura-tagow-1 text-foreground",
  "text-chmura-tagow-2 text-foreground",
  "text-chmura-tagow-3 text-foreground",
  "text-chmura-tagow-4 text-accent-foreground",
  "text-chmura-tagow-5 text-accent-foreground",
];

/** Vertical offsets of 0–24 px (design/rules.md), as top and bottom padding that always add up
 * to 24 px, so a row's height does not depend on its offsets. */
const OFFSET_CLASSES = ["pt-16 pb-8", "pt-0 pb-24", "pt-12 pb-12", "pt-24 pb-0", "pt-8 pb-16"];

/** The index into SIZE_CLASSES. */
function size(occurrences: number): number {
  return SIZE_STARTS.filter((start) => occurrences >= start).length;
}

/** Sorts the items by keys from a Park–Miller generator with a fixed seed. */
function shuffled<T>(items: T[]): T[] {
  let state = 1947;
  return items
    .map((item) => {
      state = (state * 48271) % 2147483647;
      return { item, key: state };
    })
    .sort((a, b) => a.key - b.key)
    .map(({ item }) => item);
}

/** Largest first in, largest in the middle out, the others alternately after and before it. */
function centred(tags: TagCount[]): TagCount[] {
  const result: TagCount[] = [];
  tags.forEach((tag, index) => {
    if (index % 2 === 0) {
      result.push(tag);
    } else {
      result.unshift(tag);
    }
  });
  return result;
}

/**
 * The cloud's rows (design/rules.md): the largest third of the tags in the middle row, the rest
 * alternately in the rows above and below it, each row centred on its largest tags. Tags of one
 * size are shuffled, starting from the tags sorted by slug, so the same tags give the same cloud
 * whatever order they come in. Empty rows are left out.
 */
function rows(tags: TagCount[]): TagCount[][] {
  const bySlug = [...tags].sort((a, b) => (a.slug < b.slug ? -1 : 1));
  const largestFirst = shuffled(bySlug).sort((a, b) => size(b.occurrences) - size(a.occurrences));
  const middleSize = Math.ceil(largestFirst.length / 3);
  const rest = largestFirst.slice(middleSize);
  return [
    rest.filter((_, index) => index % 2 === 0),
    largestFirst.slice(0, middleSize),
    rest.filter((_, index) => index % 2 === 1),
  ]
    .filter((row) => row.length > 0)
    .map(centred);
}

/**
 * "Chmura tagów" (US-RA-01 AC4, design/rules.md): every tag it gets, sized by its occurrence
 * count in five steps, the two largest in the accent colour. The layout is deterministic, and a
 * row wraps when it does not fit. Each tag links to its page; its count, shown only by size, is
 * spelled out for screen readers.
 */
export function TagCloud({ tags }: { tags: TagCount[] }) {
  return (
    <div className="flex flex-col gap-4 rounded-md bg-muted p-16 md:p-32">
      {rows(tags).map((row, rowIndex) => (
        <ul
          key={row[0]?.slug}
          className="flex flex-wrap items-start justify-center gap-x-16 md:gap-x-32"
        >
          {row.map((tag, index) => (
            <li
              key={tag.slug}
              className={OFFSET_CLASSES[(index + 2 * rowIndex) % OFFSET_CLASSES.length]}
            >
              <Link
                to={`/tags/${tag.slug}`}
                className={cn(
                  SIZE_CLASSES[size(tag.occurrences)],
                  "transition-colors hover:text-accent-foreground-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none",
                )}
              >
                {tag.title}{" "}
                <span className="sr-only">{formatCount(tag.occurrences, nouns.occurrence)}</span>
              </Link>
            </li>
          ))}
        </ul>
      ))}
    </div>
  );
}
