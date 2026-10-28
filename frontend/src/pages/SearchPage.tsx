import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { type ReactNode, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { FragmentCard } from "@/components/FragmentCard";
import { SearchField } from "@/components/SearchField";
import { FilterPanel, SearchFilters } from "@/components/SearchFilters";
import { type ItemGroup, ItemResult, TagResult, WorkResult } from "@/components/SearchResult";
import { SearchTabs } from "@/components/SearchTabs";
import { SectionHeader } from "@/components/SectionHeader";
import { TagList } from "@/components/TagList";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { filterCount, readSearch, type SearchState, searchUrl } from "@/lib/search";
import { cn } from "@/lib/utils";

type Results = components["schemas"]["SearchPage"];

const TITLE_ID = "search-title";
const SCOPE_ID = "search-scope";
const HINT_ID = "search-hint";
const SORT_ID = "search-sort";
const FILTERS_ID = "search-filters";
const RESULTS_PADDING = "px-page-mobile pt-24 pb-32 md:px-page md:pt-32 md:pb-48";
const ITEM_GROUPS: ItemGroup[] = ["notes", "typescripts", "secondary_texts", "materials"];
// The loading skeleton shows only after this long, so fast answers do not flash (design/rules.md).
const SKELETON_DELAY_MS = 300;

async function fetchResults(state: SearchState): Promise<Results> {
  const { data, response } = await api.GET("/api/search/", {
    params: {
      query: {
        q: state.query,
        tab: state.tab,
        work: state.works,
        decade: state.decade === null ? [] : [state.decade],
        has_scan: state.hasScan,
        has_text: state.hasText,
        sort: state.sort,
      },
    },
  });
  if (data === undefined) {
    throw new Error(`The search request failed with ${String(response.status)}.`);
  }
  return data;
}

interface GroupProps {
  title: string;
  count: number;
  /** Cards stand apart; result rows touch, separated by their rules. */
  cards?: boolean;
  children: ReactNode;
}

/** A group of results (US-RA-15 AC3): a panel with the group's name and count. */
function Group({ title, count, cards = false, children }: GroupProps) {
  if (count === 0) {
    return null;
  }
  return (
    <Card>
      <SectionHeader title={title} count={String(count)} />
      <ul className={cn("flex flex-col", cards && "gap-24")}>{children}</ul>
    </Card>
  );
}

/** "Wynik wyszukiwania / Szkielet": four results' worth of pulsing bars (design/rules.md). */
function Skeleton() {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => {
      setShown(true);
    }, SKELETON_DELAY_MS);
    return () => {
      clearTimeout(timer);
    };
  }, []);
  if (!shown) {
    return null;
  }
  return (
    <Card aria-hidden="true" className="gap-0">
      {[0, 1, 2, 3].map((index) => (
        <div
          key={index}
          className="flex flex-col gap-12 border-b border-border py-16 last:border-b-0 motion-safe:animate-pulse"
        >
          {["h-8 w-1/5", "h-16 w-2/5", "h-8 w-3/4", "h-8 w-1/2", "h-8 w-1/6"].map((size) => (
            <div key={size} className={cn("rounded-sm bg-media", size)} />
          ))}
        </div>
      ))}
    </Card>
  );
}

/**
 * Nothing found (US-RA-15 AC8): a hint and the three most frequent tags. Without a query, the
 * hint points to the tab and filters instead.
 */
function NoResults({ query, tags }: { query: string; tags: Results["suggested_tags"] }) {
  return (
    <Card className="md:max-w-4xl">
      <h2 className="text-lora-tytul-sekcji text-foreground">
        {copy.searchResults.noResults(query)}
      </h2>
      <p className="text-lora-tekst text-muted-foreground">
        {query === "" ? copy.searchResults.noResultsFilteredHint : copy.searchResults.noResultsHint}
      </p>
      {tags.length > 0 && (
        <div className="flex flex-col gap-8">
          <ColumnHeader label={copy.searchResults.suggestedTags} />
          <p className="text-lora-tekst-maly text-muted-foreground">
            {copy.searchResults.suggestedTagsDescription}
          </p>
          <TagList tags={tags} />
        </div>
      )}
    </Card>
  );
}

/**
 * The results for `state` (US-RA-15, US-RA-16): the tabs, the filters beside the results (in a
 * panel on mobile), the title with the total and the sort order, then the groups in the order of
 * US-RA-15 AC3. While results load, a skeleton holds their place, the tab counts show "–" and
 * the previous filters stay, dimmed.
 */
function SearchResults({ state }: { state: SearchState }) {
  const navigate = useNavigate();
  const results = useQuery({
    queryKey: ["search", state],
    queryFn: () => fetchResults(state),
    placeholderData: keepPreviousData,
  });
  const loading = results.isPending || results.isPlaceholderData;
  const data = loading ? undefined : results.data;
  const facets = results.data?.facets;

  function change(next: SearchState) {
    void navigate(searchUrl(next.query, next));
  }

  if (data?.total === 0 && state.tab === "all" && filterCount(state) === 0) {
    return (
      <div className={RESULTS_PADDING}>
        <NoResults query={state.query} tags={data.suggested_tags} />
      </div>
    );
  }

  const tab = state.tab === "all" ? null : copy.searchFilters.tabs[state.tab];
  return (
    <>
      <SearchTabs state={state} counts={data?.facets.tabs} />
      <div className={cn("flex gap-48", RESULTS_PADDING)}>
        {facets !== undefined && (
          <aside
            aria-labelledby={FILTERS_ID}
            aria-busy={loading}
            className={cn("hidden shrink-0 md:flex md:w-3xs md:flex-col", loading && "opacity-40")}
          >
            <h2 id={FILTERS_ID} className="sr-only">
              {copy.searchFilters.title}
            </h2>
            <SearchFilters facets={facets} state={state} onChange={change} />
          </aside>
        )}
        <section
          aria-labelledby="search-results-title"
          className="flex min-w-0 grow flex-col gap-24"
        >
          <div className="flex flex-col gap-16 md:flex-row md:items-end md:justify-between">
            <div className="flex flex-col gap-4">
              <h2 id="search-results-title" className="text-lora-tytul-sekcji text-foreground">
                {copy.searchResults.title(state.query)}
              </h2>
              {data === undefined ? (
                <p
                  role="status"
                  className={cn(
                    "text-muted-foreground",
                    loading ? "text-lora-glosa" : "text-cousine-metadane-male",
                  )}
                >
                  {loading ? copy.searchResults.loading : copy.searchResults.error}
                </p>
              ) : (
                <p role="status" className="text-cousine-metadane-male text-muted-foreground">
                  {copy.searchResults.total(data.total, tab)}
                </p>
              )}
            </div>
            <div className={cn("flex items-center gap-8", data === undefined && "opacity-40")}>
              <FilterPanel facets={facets} state={state} onChange={change} total={data?.total} />
              <label htmlFor={SORT_ID} className="text-cousine-metadane text-muted-foreground">
                {copy.searchResults.sort}
              </label>
              {/* An empty query is always sorted by title (US-RA-16 AC5). */}
              <select
                id={SORT_ID}
                value={state.query === "" ? "title" : state.sort}
                disabled={data === undefined || state.query === ""}
                onChange={(event) => {
                  change({
                    ...state,
                    sort: event.target.value === "title" ? "title" : "relevance",
                  });
                }}
                className="grow rounded-sm border border-accent-border bg-card px-12 py-8 text-cousine-metadane text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring md:grow-0"
              >
                {(["relevance", "title"] as const).map((option) => (
                  <option key={option} value={option}>
                    {copy.searchResults.sorts[option]}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {loading && <Skeleton />}
          {data?.total === 0 && <NoResults query={state.query} tags={data.suggested_tags} />}
          {data !== undefined && (
            <>
              <Group title={copy.searchResults.groups.works} count={data.works.length}>
                {data.works.map((work) => (
                  <li key={work.url}>
                    <WorkResult work={work} />
                  </li>
                ))}
              </Group>
              <Group title={copy.searchResults.groups.tags} count={data.tags.length}>
                {data.tags.map((tag) => (
                  <li key={tag.url}>
                    <TagResult tag={tag} />
                  </li>
                ))}
              </Group>
              <Group
                title={copy.searchResults.groups.fragments}
                count={data.fragments.length}
                cards
              >
                {data.fragments.map((fragment) => (
                  <li key={fragment.id}>
                    <FragmentCard fragment={fragment} />
                  </li>
                ))}
              </Group>
              {ITEM_GROUPS.map((group) => (
                <Group
                  key={group}
                  title={copy.searchResults.groups[group]}
                  count={data[group].length}
                >
                  {data[group].map((item) => (
                    <li key={item.url}>
                      <ItemResult item={item} group={group} />
                    </li>
                  ))}
                </Group>
              ))}
            </>
          )}
        </section>
      </div>
    </>
  );
}

/**
 * The search page (US-RA-14, US-RA-15, US-RA-16): the field with the query from `?q=`, what is
 * searched and the exact-phrase hint, then the results for the query, tab and filters in the
 * URL. Without any of them, there is nothing to show yet. The design has no visible title here,
 * so the heading is for screen readers.
 */
export function SearchPage() {
  const [params] = useSearchParams();
  const state = readSearch(params);
  const searching = state.query !== "" || state.tab !== "all" || filterCount(state) > 0;

  return (
    <main className="flex flex-col">
      <h1 id={TITLE_ID} className="sr-only">
        {copy.search.title}
      </h1>
      <div className="flex flex-col gap-8 px-page-mobile pt-24 md:max-w-4xl md:box-content md:gap-12 md:px-page md:pt-48">
        <SearchField
          query={params.get("q") ?? ""}
          labelledBy={TITLE_ID}
          describedBy={`${SCOPE_ID} ${HINT_ID}`}
        />
        <div className="flex flex-col gap-4 text-cousine-metadane-male text-muted-foreground md:flex-row md:justify-between">
          <p id={SCOPE_ID}>{copy.search.scope}</p>
          <p id={HINT_ID}>{copy.search.hint}</p>
        </div>
      </div>
      {searching && <SearchResults state={state} />}
    </main>
  );
}
