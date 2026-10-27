import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { ArrowRightIcon } from "@/components/icons";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeader } from "@/components/SectionHeader";
import { type TagCount, TagCloud } from "@/components/TagCloud";
import { Card } from "@/components/ui/card";
import { copy, formatCount, nouns } from "@/copy/pl";
import { api } from "@/lib/api";

const alphabetical = new Intl.Collator("pl");

async function fetchTags(): Promise<TagCount[]> {
  const { data, response } = await api.GET("/api/tags/");
  if (data === undefined) {
    throw new Error(`The tags request failed with ${String(response.status)}.`);
  }
  return data;
}

/** "Wiersz tagu" in design/components/: the name, the occurrence count and an arrow. */
function TagRow({ tag }: { tag: TagCount }) {
  return (
    <Link
      to={`/tags/${tag.slug}`}
      className="flex items-center justify-between gap-12 border-b border-border py-12 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <span className="text-lora-tekst text-foreground">{tag.title}</span>{" "}
      <span className="flex items-center gap-12">
        <span className="text-cousine-metadane-male text-muted-foreground">
          {formatCount(tag.occurrences, nouns.occurrence)}
        </span>
        <ArrowRightIcon className="size-16 shrink-0 text-accent-icon" />
      </span>
    </Link>
  );
}

/**
 * The tags list (US-RA-20): the tag cloud, then every tag alphabetically in Polish, in two
 * columns on desktop and one on mobile. The API sends only tags in use (D26), and without any
 * both sections are hidden (R-02).
 */
export function TagsPage() {
  const tags = useQuery({ queryKey: ["tags"], queryFn: fetchTags });
  const list = tags.data;

  return (
    <main className="flex flex-col">
      <PageHeader
        label={copy.siteName}
        title={copy.tags.title}
        description={copy.tags.description}
      />
      <div className="flex flex-col gap-32 px-page-mobile py-24 md:px-page md:pt-48 md:pb-64">
        {/* Only before the first data: a failed background refetch keeps the list it has. */}
        {list === undefined ? (
          <p className="text-cousine-metadane text-muted-foreground" role="status">
            {tags.isPending ? copy.tags.loading : copy.tags.error}
          </p>
        ) : (
          list.length > 0 && (
            <>
              <Card>
                <SectionHeader
                  title={copy.tagCloud.title}
                  count={String(list.length)}
                  description={copy.tagCloud.description}
                />
                <TagCloud tags={list} />
              </Card>
              <Card>
                <SectionHeader
                  title={copy.tags.all}
                  count={String(list.length)}
                  description={copy.tags.allDescription}
                />
                <ul className="md:columns-2 md:gap-x-48">
                  {[...list]
                    .sort((a, b) => alphabetical.compare(a.title, b.title))
                    .map((tag) => (
                      <li key={tag.slug} className="break-inside-avoid">
                        <TagRow tag={tag} />
                      </li>
                    ))}
                </ul>
              </Card>
            </>
          )
        )}
      </div>
    </main>
  );
}
