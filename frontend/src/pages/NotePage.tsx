import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { EntityLayout } from "@/components/EntityLayout";
import { FragmentCard } from "@/components/FragmentCard";
import { MediaContent } from "@/components/MediaContent";
import { PageHeader } from "@/components/PageHeader";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy, previewCount } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type NoteData = components["schemas"]["NotePage"];

class NotFound extends Error {}

async function fetchNote(id: number): Promise<NoteData> {
  const { data, response } = await api.GET("/api/notes/{id}/", {
    params: { path: { id } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The note request failed with ${String(response.status)}.`);
  }
  return data;
}

/**
 * The note page (US-RA-11) in the secondary text page's layout (R-05): the related works in the
 * context column; the content by its kind and the related fragments in the main column; the tags
 * of the note and its fragments. Empty blocks are not rendered (R-02).
 */
export function NotePage() {
  const id = Number(useParams().id);
  const page = useQuery({
    queryKey: ["note", id],
    queryFn: () => fetchNote(id),
    enabled: !Number.isNaN(id),
  });
  const note = page.data;

  if (page.error instanceof NotFound || Number.isNaN(id)) {
    return <NotFoundPage />;
  }
  if (note === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.note.loading : copy.note.error}
        </p>
      </main>
    );
  }

  const { works, fragments, tags } = note;

  return (
    <EntityLayout
      header={
        <PageHeader
          label={[copy.note.label, note.shelfmark].filter(Boolean).join(" · ")}
          title={note.title}
          description={note.description === "" ? undefined : <RichText html={note.description} />}
        />
      }
      context={
        works.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.note.works} count={works.length} />
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
        ) : undefined
      }
      main={
        <>
          <MediaContent content={note.content} />
          {/* A preview without an "all" link (US-RA-10 AC3). */}
          {fragments.total > 0 && (
            <Card>
              <SectionHeader
                title={copy.note.fragments}
                count={previewCount(fragments.items.length, fragments.total)}
              />
              <ul className="flex flex-col gap-24">
                {fragments.items.map((fragment) => (
                  <li key={fragment.id}>
                    <FragmentCard fragment={fragment} />
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      }
      tags={
        tags.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.note.tags} count={tags.length} />
            <TagList tags={tags} />
          </div>
        ) : undefined
      }
    />
  );
}
