import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { EntityLayout } from "@/components/EntityLayout";
import { LoadStatus } from "@/components/LoadStatus";
import { ExternalMedia } from "@/components/MediaContent";
import { PageHeader } from "@/components/PageHeader";
import { DocumentReader } from "@/components/Reader";
import { RelatedFragments, RelatedTags, RelatedWorks } from "@/components/Related";
import { RichText } from "@/components/RichText";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type SecondaryTextData = components["schemas"]["SecondaryTextPage"];

class NotFound extends Error {}

async function fetchSecondaryText(id: number): Promise<SecondaryTextData> {
  const { data, response } = await api.GET("/api/secondary-texts/{id}/", {
    params: { path: { id } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The secondary text request failed with ${String(response.status)}.`);
  }
  return data;
}

/** "1947-10-01" as "1.10.1947". */
function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return [Number(day), Number(month), year].join(".");
}

/** "List · Leopold Buczkowski · 1.10.1947"; other kinds show the kind only (US-RA-10 AC1). */
function typeLine(text: SecondaryTextData): string {
  const kind = copy.secondaryText.kinds[text.kind];
  if (text.kind !== "letter") {
    return kind;
  }
  const date = text.letter_date === null ? "" : formatDate(text.letter_date);
  return [kind, text.sender, date].filter(Boolean).join(" · ");
}

/**
 * The secondary text page (US-RA-10) in the entity layout (R-05): the related works in a row
 * under the hero; the recording and the text in the reader at full width (ARC-57); the related
 * fragments in the main column; the tags of the text, its fragments and its work links. Empty blocks are not rendered
 * (R-02).
 */
export function SecondaryTextPage() {
  const id = Number(useParams().id);
  const page = useQuery({
    queryKey: ["secondary-text", id],
    queryFn: () => fetchSecondaryText(id),
    enabled: !Number.isNaN(id),
  });
  const secondaryText = page.data;

  if (page.error instanceof NotFound || Number.isNaN(id)) {
    return <NotFoundPage />;
  }
  if (secondaryText === undefined) {
    return (
      <main className="flex flex-1 flex-col">
        <LoadStatus
          pending={page.isPending}
          loading={copy.secondaryText.loading}
          error={copy.secondaryText.error}
          className="p-page-mobile md:p-page"
        />
      </main>
    );
  }

  const { works, fragments, tags } = secondaryText;

  return (
    <EntityLayout
      isDraft={secondaryText.is_draft}
      header={
        <PageHeader
          label={typeLine(secondaryText)}
          title={secondaryText.title}
          description={
            secondaryText.description === "" ? undefined : (
              <RichText html={secondaryText.description} />
            )
          }
          image={
            secondaryText.header_image === ""
              ? undefined
              : { src: secondaryText.header_image, alt: secondaryText.header_image_alt }
          }
        />
      }
      context={
        works.length > 0 ? (
          <RelatedWorks label={copy.secondaryText.works} works={works} aboveReader />
        ) : undefined
      }
      reader={
        <>
          {secondaryText.external_url !== "" && (
            <Card>
              <ExternalMedia link={secondaryText.external_url} />
            </Card>
          )}
          <Card>
            <DocumentReader id={secondaryText.document} />
          </Card>
        </>
      }
      main={
        fragments.total > 0 && (
          <RelatedFragments title={copy.secondaryText.fragments} fragments={fragments} />
        )
      }
      tags={
        tags.length > 0 ? <RelatedTags label={copy.secondaryText.tags} tags={tags} /> : undefined
      }
    />
  );
}
