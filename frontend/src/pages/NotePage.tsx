import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { EntityLayout } from "@/components/EntityLayout";
import { MediaContent } from "@/components/MediaContent";
import { PageHeader } from "@/components/PageHeader";
import { RelatedFragments, RelatedTags, RelatedWorks } from "@/components/Related";
import { RichText } from "@/components/RichText";
import { copy } from "@/copy/pl";
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
      isDraft={note.is_draft}
      header={
        <PageHeader
          label={[copy.note.label, note.shelfmark].filter(Boolean).join(" · ")}
          title={note.title}
          description={note.description === "" ? undefined : <RichText html={note.description} />}
        />
      }
      context={
        works.length > 0 ? <RelatedWorks label={copy.note.works} works={works} /> : undefined
      }
      main={
        <>
          <MediaContent content={note.content} />
          {fragments.total > 0 && (
            <RelatedFragments title={copy.note.fragments} fragments={fragments} />
          )}
        </>
      }
      tags={tags.length > 0 ? <RelatedTags label={copy.note.tags} tags={tags} /> : undefined}
    />
  );
}
