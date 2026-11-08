import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { FragmentCard } from "@/components/FragmentCard";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { previewCount } from "@/copy/pl";
import { cn } from "@/lib/utils";

type WorkSummary = components["schemas"]["WorkSummary"];
type FragmentPreview = components["schemas"]["FragmentCardPreview"];
type Tag = components["schemas"]["TagChip"];

/**
 * An item page's related works for the context column, with their first-edition year. Above a
 * reader (ARC-57) the column is a block in a row under the hero, headed at level 2.
 */
export function RelatedWorks({
  label,
  works,
  aboveReader = false,
}: {
  label: string;
  works: WorkSummary[];
  aboveReader?: boolean;
}) {
  return (
    <div className={cn("flex flex-col gap-8", aboveReader && "lg:w-3xs")}>
      <ColumnHeader label={label} count={works.length} level={aboveReader ? 2 : 3} />
      <ul>
        {works.map((work) => (
          <li key={work.slug}>
            <SideListItem
              meta={work.year === null ? undefined : String(work.year)}
              title={work.title}
              to={`/utwory/${work.slug}`}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

/** An item page's related fragments: a preview without an "all" link (US-RA-10 AC3). */
export function RelatedFragments({
  title,
  fragments,
}: {
  title: string;
  fragments: FragmentPreview;
}) {
  return (
    <Card>
      <SectionHeader title={title} count={previewCount(fragments.items.length, fragments.total)} />
      <ul className="flex flex-col gap-24">
        {fragments.items.map((fragment) => (
          <li key={fragment.id}>
            <FragmentCard fragment={fragment} />
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** An item page's tags for the tag column. */
export function RelatedTags({ label, tags }: { label: string; tags: Tag[] }) {
  return (
    <div className="flex flex-col gap-8">
      <ColumnHeader label={label} count={tags.length} />
      <TagList tags={tags} />
    </div>
  );
}
