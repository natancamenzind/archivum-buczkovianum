import type { operations } from "@/api/schema";

type SearchQuery = NonNullable<operations["search_retrieve"]["parameters"]["query"]>;
export type Tab = NonNullable<SearchQuery["tab"]>;
export type Sort = NonNullable<SearchQuery["sort"]>;

/** The tabs in their order (US-RA-16 AC1). */
export const TABS: readonly Tab[] = ["all", "works", "fragments", "notes", "tags"];

/** The sort orders in their order. */
export const SORTS: readonly Sort[] = ["relevance", "title"];

/** The search page's state, as its URL keeps it (US-RA-16 AC4). */
export interface SearchState {
  query: string;
  tab: Tab;
  /** The selected works' IDs. */
  works: number[];
  /** The selected decade, e.g. 1940; null for "Wszystkie lata". */
  decade: number | null;
  hasScan: boolean;
  hasText: boolean;
  sort: Sort;
}

function isTab(value: string | null): value is Tab {
  return TABS.some((tab) => tab === value);
}

export function isSort(value: string | null): value is Sort {
  return SORTS.some((sort) => sort === value);
}

// The largest work id and decade the API accepts: PostgreSQL integer and smallint.
const MAX_ID = 2 ** 31 - 1;
const MAX_DECADE = 32767;

function id(value: string | null, max = MAX_ID): number | null {
  const number = Number(value);
  return value !== null && Number.isInteger(number) && number > 0 && number <= max ? number : null;
}

function decadeOf(value: string | null): number | null {
  const year = id(value, MAX_DECADE);
  return year !== null && year % 10 === 0 ? year : null;
}

/** The state in `params`; values that are not valid are left out. */
export function readSearch(params: URLSearchParams): SearchState {
  const tab = params.get("tab");
  const sort = params.get("sort");
  return {
    query: (params.get("q") ?? "").trim(),
    tab: isTab(tab) ? tab : "all",
    works: params.getAll("work").flatMap((value) => id(value) ?? []),
    decade: decadeOf(params.get("decade")),
    hasScan: params.get("has_scan") === "1",
    hasText: params.get("has_text") === "1",
    sort: isSort(sort) ? sort : "relevance",
  };
}

/** How many filter values are selected: the "n" of "Filtry (n)" (US-RA-16 AC3). */
export function filterCount(state: SearchState): number {
  return (
    state.works.length +
    Number(state.decade !== null) +
    Number(state.hasScan) +
    Number(state.hasText)
  );
}

/** Whether `params` choose a tab or a filter, so even a blank query lists results. */
export function isBrowsing(params: URLSearchParams): boolean {
  return params.has("tab") || filterCount(readSearch(params)) > 0;
}

/** `state` without its filters. */
export function withoutFilters(state: SearchState): SearchState {
  return { ...state, works: [], decade: null, hasScan: false, hasText: false };
}

/**
 * The search page's URL for a fresh search for `query` (architecture §8), e.g. `/search?q=…`. A
 * blank query is `/search`, the search entry.
 */
export function searchUrl(query: string): string {
  const q = query.trim();
  return q === "" ? "/search" : `/search?${new URLSearchParams({ q }).toString()}`;
}

/**
 * The search page's URL for `state`'s query, tab, filters and sort (architecture §8), e.g.
 * `/search?q=…&tab=works`. Defaults are left out, but a blank query names its tab, even "all",
 * so it still lists everything in it (US-RA-16 AC5).
 */
export function browseUrl(state: SearchState): string {
  const params = new URLSearchParams();
  const q = state.query.trim();
  const { tab, works, decade, hasScan, hasText, sort } = state;
  if (q !== "") {
    params.set("q", q);
  }
  if (tab !== "all" || q === "") {
    params.set("tab", tab);
  }
  for (const work of works) {
    params.append("work", String(work));
  }
  if (decade !== null) {
    params.set("decade", String(decade));
  }
  if (hasScan) {
    params.set("has_scan", "1");
  }
  if (hasText) {
    params.set("has_text", "1");
  }
  if (sort !== "relevance") {
    params.set("sort", sort);
  }
  return `/search?${params.toString()}`;
}
