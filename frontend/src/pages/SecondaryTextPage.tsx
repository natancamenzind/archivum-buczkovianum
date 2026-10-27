import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { EntityLayout } from "@/components/EntityLayout";
import { FragmentCard } from "@/components/FragmentCard";
import { PageHeader } from "@/components/PageHeader";
import { Reader } from "@/components/Reader";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy, previewCount } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type SecondaryTextData = components["schemas"]["SecondaryTextPage"];
type Document = components["schemas"]["Document"];

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

async function fetchDocument(id: number): Promise<Document> {
  const { data, response } = await api.GET("/api/documents/{id}/", {
    params: { path: { id } },
  });
  if (data === undefined) {
    throw new Error(`The document request failed with ${String(response.status)}.`);
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
 * The secondary text page (US-RA-10) in the entity layout (R-05): the related works in the
 * context column; the text in the reader and the related fragments in the main column; the tags
 * of the text, its fragments and its work links. Empty blocks are not rendered (R-02).
 */
export function SecondaryTextPage() {
  const id = Number(useParams().id);
  const page = useQuery({
    queryKey: ["secondary-text", id],
    queryFn: () => fetchSecondaryText(id),
    enabled: !Number.isNaN(id),
  });
  const secondaryText = page.data;
  const text = useQuery({
    queryKey: ["document", secondaryText?.document],
    queryFn: () => fetchDocument(secondaryText?.document ?? 0),
    enabled: secondaryText !== undefined,
  });

  if (page.error instanceof NotFound || Number.isNaN(id)) {
    return <NotFoundPage />;
  }
  if (secondaryText === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.secondaryText.loading : copy.secondaryText.error}
        </p>
      </main>
    );
  }

  const { works, fragments, tags } = secondaryText;

  return (
    <EntityLayout
      header={
        <PageHeader
          label={typeLine(secondaryText)}
          title={secondaryText.title}
          description={
            secondaryText.description === "" ? undefined : (
              <RichText html={secondaryText.description} />
            )
          }
        />
      }
      context={
        works.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.secondaryText.works} count={works.length} />
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
          <Card>
            <SectionHeader title={copy.secondaryText.text} />
            {text.data === undefined ? (
              <p className="text-cousine-metadane text-muted-foreground" role="status">
                {text.isPending ? copy.reader.loading : copy.reader.error}
              </p>
            ) : (
              <Reader document={text.data} />
            )}
          </Card>
          {/* A preview without an "all" link (US-RA-10 AC3). */}
          {fragments.total > 0 && (
            <Card>
              <SectionHeader
                title={copy.secondaryText.fragments}
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
            <ColumnHeader label={copy.secondaryText.tags} count={tags.length} />
            <TagList tags={tags} />
          </div>
        ) : undefined
      }
    />
  );
}
