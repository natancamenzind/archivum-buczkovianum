import { Link } from "react-router";

import type { components } from "@/api/schema";
import { copy } from "@/copy/pl";
import { browseUrl, type SearchState, TABS } from "@/lib/search";
import { cn } from "@/lib/utils";

type TabCounts = components["schemas"]["TabCounts"];

/**
 * "Zakładka" in design/components/: the search tabs (US-RA-16 AC1), each with its count. A tab
 * is a link that keeps the query, filters and sort. While results load, counts show "–".
 */
export function SearchTabs({ state, counts }: { state: SearchState; counts?: TabCounts }) {
  return (
    <nav
      aria-label={copy.searchFilters.tabsLabel}
      className="overflow-x-auto border-b border-border px-page-mobile pt-16 md:px-page md:pt-24"
    >
      <ul className="flex gap-32">
        {TABS.map((tab) => {
          const active = tab === state.tab;
          return (
            <li key={tab} className="shrink-0">
              <Link
                to={browseUrl({ ...state, tab })}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-8 border-b-2 py-12 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                  active ? "border-accent-border" : "border-transparent",
                )}
              >
                <span
                  className={cn(
                    "text-cousine-nawigacja",
                    active ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {copy.searchFilters.tabs[tab]}
                </span>{" "}
                <span className="text-cousine-metadane-male text-muted-foreground">
                  {counts === undefined ? copy.searchFilters.pending : String(counts[tab])}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
