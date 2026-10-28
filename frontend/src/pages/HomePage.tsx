import { useQuery } from "@tanstack/react-query";

import type { components } from "@/api/schema";
import { ArrowLink } from "@/components/ArrowLink";
import { FragmentCard } from "@/components/FragmentCard";
import { RichText } from "@/components/RichText";
import { SectionHeader } from "@/components/SectionHeader";
import { TagCloud } from "@/components/TagCloud";
import { Card } from "@/components/ui/card";
import { WorkCard } from "@/components/WorkCard";
import { copy, formatCount, nouns, previewCount } from "@/copy/pl";
import { api } from "@/lib/api";
import { browseUrl, NEW_SEARCH } from "@/lib/search";

type Home = components["schemas"]["HomePage"];
type FeaturedFragment = components["schemas"]["FeaturedFragment"];

async function fetchHome(): Promise<Home> {
  const { data, response } = await api.GET("/api/home/");
  if (data === undefined) {
    throw new Error(`The home request failed with ${String(response.status)}.`);
  }
  return data;
}

/**
 * "Nagłówek strony głównej" in design/screens/strona-glowna.md: the title, introduction and
 * counts over the portrait, darkened towards the text. The title shows before the data does.
 */
function Hero({ home }: { home: Home | undefined }) {
  const statistics = home?.statistics;
  const intro = home?.intro ?? "";

  return (
    // A div, not <header>: the site header is the page's only banner landmark (R-07).
    <div data-slot="home-hero" className="relative overflow-hidden bg-inverse">
      {home !== undefined && home.portrait !== "" && (
        <img
          src={home.portrait}
          alt={home.portrait_alt}
          className="absolute inset-0 size-full object-cover"
        />
      )}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-linear-to-r from-inverse/94 via-inverse/72 to-inverse/20"
      />
      <div className="relative px-page-mobile pt-64 pb-24 md:px-page md:py-64">
        <div className="flex flex-col gap-16 md:max-w-2xl">
          {/* The design's ornament is 40 px wide; 48 is the nearest spacing token. */}
          <div aria-hidden="true" className="h-px w-48 bg-inverse-border" />
          <h1 className="text-lora-tytul-strony-mobile text-inverse-foreground md:text-lora-display">
            {copy.siteName}
          </h1>
          {intro.trim() !== "" && (
            <RichText
              html={intro}
              className="text-lora-glosa text-inverse-foreground md:text-lora-wstep"
            />
          )}
          {statistics !== undefined && (
            <p className="text-cousine-etykieta text-inverse-muted-foreground">
              {[
                formatCount(statistics.works, nouns.work),
                formatCount(statistics.fragments, nouns.fragment),
                formatCount(statistics.tags, nouns.tag),
              ].join(" · ")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * "Wybrany fragment" (US-RA-02): the fragment card, counted among all visible fragments, and a
 * link to the Fragmenty search filtered to its work.
 */
function Featured({ featured, total }: { featured: FeaturedFragment; total: number }) {
  const { fragment, work } = featured;
  return (
    <Card>
      <SectionHeader
        title={copy.home.featured}
        count={previewCount(1, total)}
        description={copy.home.featuredDescription}
      />
      <FragmentCard fragment={fragment} />
      {work !== null && (
        <ArrowLink
          label={copy.home.workFragments(work.title, work.count)}
          to={browseUrl({ ...NEW_SEARCH, tab: "fragments", works: [work.id] })}
        />
      )}
    </Card>
  );
}

/**
 * The home page (US-RA-01): the hero, the work cards in the API's order (by first edition), the
 * featured fragment and the tag cloud. Sections without content are hidden (R-02).
 */
export function HomePage() {
  const home = useQuery({ queryKey: ["home"], queryFn: fetchHome });
  const data = home.data;

  return (
    <main className="flex flex-col">
      <Hero home={data} />
      <div className="flex flex-col gap-32 px-page-mobile py-24 md:px-page md:pt-48 md:pb-64">
        {/* Only before the first data: a failed background refetch keeps the page it has. */}
        {data === undefined ? (
          <p className="text-cousine-metadane text-muted-foreground" role="status">
            {home.isPending ? copy.home.loading : copy.home.error}
          </p>
        ) : (
          <>
            {data.works.length > 0 && (
              <Card>
                <SectionHeader
                  title={copy.home.works}
                  count={String(data.works.length)}
                  description={copy.home.worksDescription}
                />
                <ul className="grid auto-rows-fr grid-cols-1 gap-24 sm:grid-cols-2 lg:grid-cols-4">
                  {data.works.map((work) => (
                    <li key={work.slug}>
                      <WorkCard work={work} />
                    </li>
                  ))}
                </ul>
              </Card>
            )}
            {data.featured !== null && (
              <Featured featured={data.featured} total={data.statistics.fragments} />
            )}
            {data.tags.length > 0 && (
              <Card>
                <SectionHeader
                  title={copy.tagCloud.title}
                  count={String(data.tags.length)}
                  description={copy.tagCloud.description}
                />
                <TagCloud tags={data.tags} />
              </Card>
            )}
          </>
        )}
      </div>
    </main>
  );
}
