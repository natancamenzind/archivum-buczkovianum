import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/PageHeader";
import { SectionHeader } from "@/components/SectionHeader";
import { Card } from "@/components/ui/card";
import { type Work, WorkCard } from "@/components/WorkCard";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";

async function fetchWorks(): Promise<Work[]> {
  const { data, response } = await api.GET("/api/works/");
  if (data === undefined) {
    throw new Error(`The works request failed with ${String(response.status)}.`);
  }
  return data;
}

/**
 * The works list (US-RA-18): a card for every published work, in the API's order (by first
 * edition). The grid has one column on mobile (US-RA-20) and gives every row the same height,
 * so all the cards are as tall as the tallest one. Without works the section is hidden (R-02).
 */
export function WorksPage() {
  const works = useQuery({ queryKey: ["works"], queryFn: fetchWorks });
  const list = works.data;

  return (
    <main className="flex flex-col">
      <PageHeader
        label={copy.siteName}
        title={copy.works.title}
        description={copy.works.description}
      />
      <div className="flex flex-col gap-32 px-page-mobile py-24 md:px-page md:pt-48 md:pb-64">
        {/* Only before the first data: a failed background refetch keeps the list it has. */}
        {list === undefined ? (
          <p className="text-cousine-metadane text-muted-foreground" role="status">
            {works.isPending ? copy.works.loading : copy.works.error}
          </p>
        ) : (
          list.length > 0 && (
            <Card>
              <SectionHeader
                title={copy.works.all}
                count={String(list.length)}
                description={copy.works.allDescription}
              />
              <ul className="grid auto-rows-fr grid-cols-1 gap-24 sm:grid-cols-2 lg:grid-cols-4">
                {list.map((work) => (
                  <li key={work.slug}>
                    <WorkCard work={work} />
                  </li>
                ))}
              </ul>
            </Card>
          )
        )}
      </div>
    </main>
  );
}
