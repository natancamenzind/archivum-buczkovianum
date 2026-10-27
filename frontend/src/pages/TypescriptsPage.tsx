import { useQuery } from "@tanstack/react-query";

import type { components } from "@/api/schema";
import { ListRow } from "@/components/ListRow";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeader } from "@/components/SectionHeader";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";

type TypescriptGroup = components["schemas"]["TypescriptGroup"];

async function fetchTypescripts(): Promise<TypescriptGroup[]> {
  const { data, response } = await api.GET("/api/typescripts/");
  if (data === undefined) {
    throw new Error(`The typescripts request failed with ${String(response.status)}.`);
  }
  return data;
}

function Group({ group }: { group: TypescriptGroup }) {
  // Genre and year, leaving out whichever is missing (R-02).
  const meta = [group.genre, group.year].filter(Boolean).join(" · ");

  return (
    <Card className="h-full">
      <SectionHeader
        title={group.title}
        count={String(group.typescripts.length)}
        description={meta === "" ? undefined : meta}
      />
      <ol>
        {group.typescripts.map((typescript, index) => (
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
  );
}

/**
 * The typescripts list (US-RA-19): a card per work, in the API's order (by first edition),
 * listing the work's typescripts. Two cards per row on desktop, one column on mobile (US-RA-20).
 * Without typescripts no card is shown (R-02).
 */
export function TypescriptsPage() {
  const typescripts = useQuery({ queryKey: ["typescripts"], queryFn: fetchTypescripts });
  const groups = typescripts.data;

  return (
    <main className="flex flex-col">
      <PageHeader
        label={copy.siteName}
        title={copy.typescripts.title}
        description={copy.typescripts.description}
      />
      <div className="px-page-mobile py-24 md:px-page md:pt-48 md:pb-64">
        {/* Only before the first data: a failed background refetch keeps the list it has. */}
        {groups === undefined ? (
          <p className="text-cousine-metadane text-muted-foreground" role="status">
            {typescripts.isPending ? copy.typescripts.loading : copy.typescripts.error}
          </p>
        ) : (
          groups.length > 0 && (
            <ul className="grid grid-cols-1 gap-24 md:grid-cols-2">
              {groups.map((group) => (
                <li key={group.slug}>
                  <Group group={group} />
                </li>
              ))}
            </ul>
          )
        )}
      </div>
    </main>
  );
}
