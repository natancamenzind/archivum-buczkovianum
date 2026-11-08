import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { BibliographyList } from "@/components/BibliographyList";
import { ColumnHeader } from "@/components/ColumnHeader";
import { DraftBanner } from "@/components/DraftBanner";
import { LoadStatus } from "@/components/LoadStatus";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeader } from "@/components/SectionHeader";
import { SideListItem } from "@/components/SideListItem";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type BibliographyData = components["schemas"]["BibliographyPage"];

class NotFound extends Error {}

async function fetchBibliography(slug: string): Promise<BibliographyData> {
  const { data, response } = await api.GET("/api/works/{slug}/bibliography/", {
    params: { path: { slug } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The bibliography request failed with ${String(response.status)}.`);
  }
  return data;
}

/**
 * A work's bibliography page (US-RA-21): the hero as on the About page, the card with every
 * entry, and the works with a bibliography by first edition, the current one highlighted. On
 * mobile the works are below the card.
 */
export function BibliographyPage() {
  const slug = useParams().slug ?? "";
  const page = useQuery({
    queryKey: ["bibliography", slug],
    queryFn: () => fetchBibliography(slug),
  });
  const bibliography = page.data;

  if (page.error instanceof NotFound) {
    return <NotFoundPage />;
  }
  if (bibliography === undefined) {
    return (
      <main className="flex flex-1 flex-col">
        <LoadStatus
          pending={page.isPending}
          loading={copy.bibliography.loading}
          error={copy.bibliography.error}
          className="p-page-mobile md:p-page"
        />
      </main>
    );
  }

  return (
    <main className="flex flex-col">
      {bibliography.is_draft && <DraftBanner />}
      <PageHeader
        label={[copy.bibliography.type, copy.author].join(" · ")}
        title={bibliography.title}
      />
      <div className="flex flex-col gap-24 px-page-mobile pt-24 pb-32 lg:flex-row lg:items-start lg:gap-32 lg:px-page lg:pt-48 lg:pb-64">
        <Card className="min-w-0 lg:flex-1">
          <SectionHeader
            title={copy.bibliography.title}
            count={String(bibliography.entries.length)}
          />
          <BibliographyList entries={bibliography.entries} />
        </Card>
        {bibliography.works.length > 0 && (
          <nav
            aria-label={copy.bibliography.works}
            className="flex flex-col gap-8 lg:w-3xs lg:shrink-0"
          >
            <ColumnHeader label={copy.bibliography.works} count={bibliography.works.length} />
            <ul>
              {bibliography.works.map((work) => (
                <li key={work.slug}>
                  <SideListItem
                    title={copy.bibliography.workBibliography(work.title)}
                    to={`/utwory/${work.slug}/bibliografia`}
                    current={work.slug === bibliography.slug}
                  />
                </li>
              ))}
            </ul>
          </nav>
        )}
      </div>
    </main>
  );
}
