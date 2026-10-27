import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { ContextualMaterials } from "@/components/ContextualMaterials";
import { EntityLayout } from "@/components/EntityLayout";
import { FragmentCard, NoteCard } from "@/components/FragmentCard";
import { PageHeader } from "@/components/PageHeader";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type TagData = components["schemas"]["TagPage"];

class NotFound extends Error {}

async function fetchTag(slug: string): Promise<TagData> {
  const { data, response } = await api.GET("/api/tags/{slug}/", {
    params: { path: { slug } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The tag request failed with ${String(response.status)}.`);
  }
  return data;
}

/** The works the tag refers to, by first edition, with their tagged fragments (US-RA-07 AC2). */
function Works({ works, level }: { works: TagData["works"]; level: 2 | 3 }) {
  return (
    <div className="flex flex-col gap-8">
      <ColumnHeader label={copy.tag.works} count={works.length} level={level} />
      <ul>
        {works.map((work) => (
          <li key={work.slug}>
            <SideListItem
              meta={work.year?.toString()}
              title={work.title}
              description={
                work.fragment_count > 0 ? copy.tag.workFragments(work.fragment_count) : undefined
              }
              to={`/works/${work.slug}`}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * The tag page (US-RA-07) in the entity layout (R-05): the works the tag refers to in the
 * context column; every fragment and note with the tag in the main column; the related tags;
 * the contextual materials with the tag. Empty blocks are not rendered (R-02).
 */
export function TagPage() {
  const slug = useParams().slug ?? "";
  const page = useQuery({ queryKey: ["tag", slug], queryFn: () => fetchTag(slug) });
  const tag = page.data;

  if (page.error instanceof NotFound) {
    return <NotFoundPage />;
  }
  if (tag === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.tag.loading : copy.tag.error}
        </p>
      </main>
    );
  }

  const columnLevel = tag.fragments.length > 0 || tag.notes.length > 0 ? 3 : 2;

  return (
    <EntityLayout
      header={
        <PageHeader
          label={copy.tag.label(tag.occurrences, tag.works.length)}
          title={tag.title}
          description={tag.description === "" ? undefined : <RichText html={tag.description} />}
        />
      }
      context={tag.works.length > 0 ? <Works works={tag.works} level={columnLevel} /> : undefined}
      main={
        <>
          {tag.fragments.length > 0 && (
            <Card>
              <SectionHeader
                title={copy.tag.fragments}
                count={String(tag.fragments.length)}
                description={copy.tag.fragmentsDescription}
              />
              <ul className="flex flex-col gap-24">
                {tag.fragments.map((fragment) => (
                  <li key={fragment.id}>
                    <FragmentCard fragment={fragment} />
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {tag.notes.length > 0 && (
            <Card>
              <SectionHeader title={copy.tag.notes} count={String(tag.notes.length)} />
              <ul className="flex flex-col gap-24">
                {tag.notes.map((note) => (
                  <li key={note.url}>
                    <NoteCard note={note} />
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      }
      tags={
        tag.related.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.tag.related} count={tag.related.length} level={columnLevel} />
            <TagList tags={tag.related} />
          </div>
        ) : undefined
      }
      materials={
        <ContextualMaterials
          materials={tag.materials}
          description={copy.tag.materialsDescription}
        />
      }
    />
  );
}
