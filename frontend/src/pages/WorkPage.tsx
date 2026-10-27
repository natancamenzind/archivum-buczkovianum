import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { ArrowLink } from "@/components/ArrowLink";
import { ColumnHeader } from "@/components/ColumnHeader";
import { ContextualMaterials } from "@/components/ContextualMaterials";
import { EntityLayout } from "@/components/EntityLayout";
import { FragmentCard, NoteCard } from "@/components/FragmentCard";
import { ListRow } from "@/components/ListRow";
import { PageHeader } from "@/components/PageHeader";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy, previewCount } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type WorkData = components["schemas"]["WorkPage"];

class NotFound extends Error {}

async function fetchWork(slug: string): Promise<WorkData> {
  const { data, response } = await api.GET("/api/works/{slug}/", {
    params: { path: { slug } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The work request failed with ${String(response.status)}.`);
  }
  return data;
}

/** The editions by year (US-RA-04 AC2); the earliest is the first edition. */
function Editions({ editions, level }: { editions: WorkData["editions"]; level: 2 | 3 }) {
  return (
    <div className="flex flex-col gap-8">
      <ColumnHeader label={copy.work.editions} count={editions.length} level={level} />
      <ul>
        {editions.map((edition, index) => (
          // Editions have no ID in the API, and the list never reorders.
          <li key={index}>
            <SideListItem
              meta={String(edition.year)}
              title={edition.publisher}
              description={[edition.place, index === 0 && copy.work.firstEdition]
                .filter(Boolean)
                .join(" · ")}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

/** The main typescript's fragments as cards (R-09, R-10). "All" opens them on its page (D20). */
function Fragments({ work }: { work: WorkData }) {
  const { items, total } = work.fragments;
  return (
    <Card>
      <SectionHeader
        title={copy.work.fragments}
        count={previewCount(items.length, total)}
        description={copy.work.fragmentsDescription}
      />
      <ul className="flex flex-col gap-24">
        {items.map((fragment) => (
          <li key={fragment.id}>
            <FragmentCard fragment={fragment} />
          </li>
        ))}
      </ul>
      {items.length < total && work.main_typescript !== null && (
        <ArrowLink
          label={copy.typescript.allFragments(total)}
          to={`/typescripts/${String(work.main_typescript)}?fragments=all`}
        />
      )}
    </Card>
  );
}

/**
 * The work page (US-RA-04) in the entity layout (R-05): the editions in the context column; the
 * main typescript's fragments, the typescripts and the notes in the main column; the tags that
 * refer to the work; its contextual materials. Empty blocks are not rendered (R-02).
 */
export function WorkPage() {
  const slug = useParams().slug ?? "";
  const page = useQuery({ queryKey: ["work", slug], queryFn: () => fetchWork(slug) });
  const work = page.data;

  if (page.error instanceof NotFound) {
    return <NotFoundPage />;
  }
  if (work === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.work.loading : copy.work.error}
        </p>
      </main>
    );
  }

  const label = [copy.work.type, copy.author, work.year?.toString()].filter(Boolean).join(" · ");
  const columnLevel =
    work.fragments.total > 0 || work.typescripts.length > 0 || work.notes.length > 0 ? 3 : 2;

  return (
    <EntityLayout
      header={
        <PageHeader
          label={label}
          title={work.title}
          description={work.description === "" ? undefined : <RichText html={work.description} />}
        />
      }
      context={
        work.editions.length > 0 ? (
          <Editions editions={work.editions} level={columnLevel} />
        ) : undefined
      }
      main={
        <>
          {work.fragments.total > 0 && <Fragments work={work} />}
          {work.typescripts.length > 0 && (
            <Card>
              <SectionHeader
                title={copy.work.typescripts}
                count={String(work.typescripts.length)}
              />
              <ol>
                {work.typescripts.map((typescript, index) => (
                  <li key={typescript.id}>
                    <ListRow
                      number={index + 1}
                      title={[typescript.title, typescript.shelfmark].filter(Boolean).join(", ")}
                      to={`/typescripts/${String(typescript.id)}`}
                    />
                  </li>
                ))}
              </ol>
            </Card>
          )}
          {work.notes.length > 0 && (
            <Card>
              <SectionHeader
                title={copy.work.notes}
                count={String(work.notes.length)}
                description={copy.work.notesDescription}
              />
              <ul className="flex flex-col gap-24">
                {work.notes.map((note) => (
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
        work.tags.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.tags.title} count={work.tags.length} level={columnLevel} />
            <TagList tags={work.tags} />
          </div>
        ) : undefined
      }
      materials={<ContextualMaterials materials={work.materials} />}
    />
  );
}
