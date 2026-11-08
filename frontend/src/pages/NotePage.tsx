import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { EntityLayout } from "@/components/EntityLayout";
import { LoadStatus } from "@/components/LoadStatus";
import { MediaContent } from "@/components/MediaContent";
import { PageHeader } from "@/components/PageHeader";
import { RelatedFragments, RelatedTags, RelatedWorks } from "@/components/Related";
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
 * of the note and its fragments. A text is read in the reader at full width, with the works in a
 * row under the hero (ARC-57). Empty blocks are not rendered (R-02).
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
      <main className="flex flex-1 flex-col">
        <LoadStatus
          pending={page.isPending}
          loading={copy.note.loading}
          error={copy.note.error}
          className="p-page-mobile md:p-page"
        />
      </main>
    );
  }

  const { works, fragments, tags } = note;
  const hasReader = note.content.document !== null;

  return (
    <EntityLayout
      isDraft={note.is_draft}
      header={
        <PageHeader
          label={[copy.note.label, note.shelfmark].filter(Boolean).join(" · ")}
          title={note.title}
          image={
            note.header_image === ""
              ? undefined
              : { src: note.header_image, alt: note.header_image_alt }
          }
        />
      }
      context={
        works.length > 0 ? (
          <RelatedWorks label={copy.note.works} works={works} aboveReader={hasReader} />
        ) : undefined
      }
      // A text is read in the reader, at full width (ARC-57); other content stays in the column.
      reader={hasReader ? <MediaContent content={note.content} /> : undefined}
      main={
        <>
          {!hasReader && <MediaContent content={note.content} />}
          {fragments.total > 0 && (
            <RelatedFragments title={copy.note.fragments} fragments={fragments} />
          )}
        </>
      }
      tags={tags.length > 0 ? <RelatedTags label={copy.note.tags} tags={tags} /> : undefined}
    />
  );
}
