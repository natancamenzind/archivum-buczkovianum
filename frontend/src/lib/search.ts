import type { operations } from "@/api/schema";

type SearchQuery = NonNullable<operations["search_retrieve"]["parameters"]["query"]>;
export type Tab = NonNullable<SearchQuery["tab"]>;
export type Sort = NonNullable<SearchQuery["sort"]>;

/** The tabs in their order (US-RA-16 AC1). */
export const TABS: readonly Tab[] = ["all", "works", "fragments", "notes", "tags"];

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

export const NO_SEARCH: SearchState = {
  query: "",
  tab: "all",
  works: [],
  decade: null,
  hasScan: false,
  hasText: false,
  sort: "relevance",
};

function isTab(value: string | null): value is Tab {
  return TABS.some((tab) => tab === value);
}

function id(value: string | null): number | null {
  const number = Number(value);
  return value !== null && Number.isInteger(number) && number > 0 ? number : null;
}

/** The state in `params`; values that are not valid are left out. */
export function readSearch(params: URLSearchParams): SearchState {
  const tab = params.get("tab");
  return {
    query: (params.get("q") ?? "").trim(),
    tab: isTab(tab) ? tab : "all",
    works: params.getAll("work").flatMap((value) => id(value) ?? []),
    decade: id(params.get("decade")),
    hasScan: params.get("has_scan") === "1",
    hasText: params.get("has_text") === "1",
    sort: params.get("sort") === "title" ? "title" : "relevance",
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

/** `state` without its filters. */
export function withoutFilters(state: SearchState): SearchState {
  return { ...state, works: [], decade: null, hasScan: false, hasText: false };
}

/**
 * The search page's URL for `query` in `state`'s tab, filters and sort (architecture §8), e.g.
 * `/search?q=…&tab=works`. Defaults are left out, so a blank query alone is `/search`.
 */
export function searchUrl(query: string, state: SearchState = NO_SEARCH): string {
  const params = new URLSearchParams();
  const q = query.trim();
  if (q !== "") {
    params.set("q", q);
  }
  if (state.tab !== "all") {
    params.set("tab", state.tab);
  }
  for (const work of state.works) {
    params.append("work", String(work));
  }
  if (state.decade !== null) {
    params.set("decade", String(state.decade));
  }
  if (state.hasScan) {
    params.set("has_scan", "1");
  }
  if (state.hasText) {
    params.set("has_text", "1");
  }
  if (state.sort === "title") {
    params.set("sort", "title");
  }
  const search = params.toString();
  return search === "" ? "/search" : `/search?${search}`;
}
