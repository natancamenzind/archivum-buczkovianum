import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { FragmentCard } from "@/components/FragmentCard";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { previewCount } from "@/copy/pl";

type WorkSummary = components["schemas"]["WorkSummary"];
type FragmentPreview = components["schemas"]["FragmentCardPreview"];
type Tag = components["schemas"]["TagChip"];

/** An item page's related works for the context column, with their first-edition year. */
export function RelatedWorks({ label, works }: { label: string; works: WorkSummary[] }) {
  return (
    <div className="flex flex-col gap-8">
      <ColumnHeader label={label} count={works.length} />
      <ul>
        {works.map((work) => (
          <li key={work.slug}>
            <SideListItem
              meta={work.year === null ? undefined : String(work.year)}
              title={work.title}
              to={`/works/${work.slug}`}
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
