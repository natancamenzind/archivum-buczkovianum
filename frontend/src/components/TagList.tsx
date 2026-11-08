import { Link } from "react-router";

import type { components } from "@/api/schema";
import { cn } from "@/lib/utils";

type Tag = components["schemas"]["TagChip"];

/**
 * "Tag" pills from design/components/, each linking to its tag page. On hover and keyboard
 * focus a pill takes the warm background and the accent border; `active` gives every pill that
 * look, as the reader does for the note of a highlighted fragment (ARC-57).
 */
export function TagList({ tags, active = false }: { tags: Tag[]; active?: boolean }) {
  return (
    <ul className="flex flex-wrap gap-8">
      {tags.map((tag) => (
        <li key={tag.slug}>
          <Link
            to={`/tagi/${tag.slug}`}
            className={cn(
              "block rounded-full border border-border bg-card px-12 py-4 text-cousine-metadane text-foreground transition-colors duration-150 ease-out hover:border-accent-border hover:bg-accent hover:text-accent-foreground focus-visible:border-accent-border focus-visible:bg-accent focus-visible:text-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none",
              active && "border-accent-border bg-accent text-accent-foreground",
            )}
          >
            {tag.title}
          </Link>
        </li>
      ))}
    </ul>
  );
}
