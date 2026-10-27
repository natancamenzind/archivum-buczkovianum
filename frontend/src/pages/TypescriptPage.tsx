import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useParams, useSearchParams } from "react-router";

import type { components } from "@/api/schema";
import { ArrowLink } from "@/components/ArrowLink";
import { ColumnHeader } from "@/components/ColumnHeader";
import { ContextualMaterials } from "@/components/ContextualMaterials";
import { EntityLayout } from "@/components/EntityLayout";
import { ListRow } from "@/components/ListRow";
import { PageHeader } from "@/components/PageHeader";
import { Reader } from "@/components/Reader";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy, formatCount, fragmentLabel, nouns, previewCount } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type TypescriptData = components["schemas"]["TypescriptPage"];
type Document = components["schemas"]["Document"];
type FragmentRow = components["schemas"]["FragmentRow"];

/** `?fragments=all` expands the fragment list in place (plan D20). */
const ALL_FRAGMENTS = "all";

class NotFound extends Error {}

async function fetchTypescript(id: number): Promise<TypescriptData> {
  const { data, response } = await api.GET("/api/typescripts/{id}/", {
    params: { path: { id } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The typescript request failed with ${String(response.status)}.`);
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

/** "Fragment 01 · rozdział I · ML, sygn. 1618.0009", leaving out what is missing (R-02). */
function fragmentTitle(fragment: FragmentRow): string {
  return [fragmentLabel(fragment.number), fragment.location, fragment.shelfmark]
    .filter(Boolean)
    .join(" · ");
}

function Context({ typescript }: { typescript: TypescriptData }) {
  const { work, work_typescripts: typescripts } = typescript;
  return (
    <>
      {work !== null && (
        <div className="flex flex-col gap-8">
          <ColumnHeader label={copy.typescript.work} count={1} />
          <SideListItem
            meta={work.year === null ? undefined : String(work.year)}
            title={work.title}
            // No count when it is 0 (plan D23).
            description={
              work.fragment_count > 0 ? formatCount(work.fragment_count, nouns.fragment) : undefined
            }
            to={`/works/${work.slug}`}
          />
        </div>
      )}
      <div className="flex flex-col gap-8">
        <ColumnHeader label={copy.typescript.workTypescripts} count={typescripts.length} />
        <ul>
          {typescripts.map((item) => (
            <li key={item.id}>
              <SideListItem
                meta={item.shelfmark === "" ? undefined : item.shelfmark}
                title={item.title}
                to={`/typescripts/${String(item.id)}`}
                current={item.id === typescript.id}
              />
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

function Fragments({ typescript, document }: { typescript: TypescriptData; document?: Document }) {
  const [params] = useSearchParams();
  const { items, total } = typescript.fragments;
  const expanded = params.get("fragments") === ALL_FRAGMENTS;
  // The whole list comes with the reader's text, in page order.
  const all = expanded ? document?.fragments : undefined;
  const shown = all ?? items;
  const list = useRef<HTMLUListElement>(null);
  const expanding = useRef(false);

  // Expanded from the link, which then disappears, the list takes the keyboard focus.
  useEffect(() => {
    if (all !== undefined && expanding.current) {
      expanding.current = false;
      list.current?.querySelector("a")?.focus();
    }
  }, [all]);

  return (
    <Card>
      <SectionHeader
        title={copy.typescript.fragments}
        count={previewCount(shown.length, total)}
        description={copy.typescript.fragmentsDescription}
      />
      <ul ref={list}>
        {shown.map((fragment) => (
          <li key={fragment.id}>
            <ListRow
              number={fragment.number}
              title={fragmentTitle(fragment)}
              to={`/typescripts/${String(typescript.id)}?${expanded ? `fragments=${ALL_FRAGMENTS}&` : ""}fragment=${String(fragment.id)}`}
            />
          </li>
        ))}
      </ul>
      {!expanded && shown.length < total && (
        <ArrowLink
          label={copy.typescript.allFragments(total)}
          to={`?fragments=${ALL_FRAGMENTS}`}
          onClick={() => {
            expanding.current = true;
          }}
        />
      )}
    </Card>
  );
}

/**
 * The typescript page (US-RA-08) in the entity layout (R-05): the work and its typescripts in
 * the context column; the reader and the fragment preview in the main column; the tags of the
 * typescript and its fragments; the contextual materials of its work. Empty blocks are not
 * rendered (R-02).
 */
export function TypescriptPage() {
  const id = Number(useParams().id);
  const page = useQuery({
    queryKey: ["typescript", id],
    queryFn: () => fetchTypescript(id),
    enabled: !Number.isNaN(id),
  });
  const typescript = page.data;
  const text = useQuery({
    queryKey: ["document", typescript?.document],
    queryFn: () => fetchDocument(typescript?.document ?? 0),
    enabled: typescript !== undefined,
  });

  if (page.error instanceof NotFound || Number.isNaN(id)) {
    return <NotFoundPage />;
  }
  if (typescript === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.typescript.loading : copy.typescript.error}
        </p>
      </main>
    );
  }

  const year = typescript.work?.year?.toString();
  const label = [copy.typescript.type, typescript.shelfmark, year].filter(Boolean).join(" · ");

  return (
    <EntityLayout
      header={
        <PageHeader
          label={label}
          title={typescript.title}
          description={
            typescript.description === "" ? undefined : <RichText html={typescript.description} />
          }
        />
      }
      context={<Context typescript={typescript} />}
      main={
        <>
          <Card>
            <SectionHeader
              title={copy.typescript.scan}
              count={formatCount(typescript.page_count, nouns.page)}
            />
            {text.data === undefined ? (
              <p className="text-cousine-metadane text-muted-foreground" role="status">
                {text.isPending ? copy.reader.loading : copy.reader.error}
              </p>
            ) : (
              <Reader document={text.data} />
            )}
          </Card>
          {typescript.fragments.total > 0 && (
            <Fragments typescript={typescript} document={text.data} />
          )}
        </>
      }
      tags={
        typescript.tags.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ColumnHeader label={copy.tags.title} count={typescript.tags.length} />
            <TagList tags={typescript.tags} />
          </div>
        ) : undefined
      }
      materials={<ContextualMaterials materials={typescript.materials} />}
    />
  );
}
