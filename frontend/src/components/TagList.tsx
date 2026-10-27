import { Link } from "react-router";

import type { components } from "@/api/schema";

type Tag = components["schemas"]["TagChip"];

/**
 * "Tag" pills from design/components/, each linking to its tag page. On hover and keyboard
 * focus a pill takes the warm background and the accent border.
 */
export function TagList({ tags }: { tags: Tag[] }) {
  return (
    <ul className="flex flex-wrap gap-8">
      {tags.map((tag) => (
        <li key={tag.slug}>
          <Link
            to={`/tags/${tag.slug}`}
            className="block rounded-full border border-border bg-card px-12 py-4 text-cousine-metadane text-foreground transition-colors duration-150 ease-out hover:border-accent-border hover:bg-accent hover:text-accent-foreground focus-visible:border-accent-border focus-visible:bg-accent focus-visible:text-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none"
          >
            {tag.title}
          </Link>
        </li>
      ))}
    </ul>
  );
}
