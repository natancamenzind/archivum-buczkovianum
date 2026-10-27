import { useSearchParams } from "react-router";

import { SearchField } from "@/components/SearchField";
import { copy } from "@/copy/pl";

const TITLE_ID = "search-title";
const SCOPE_ID = "search-scope";
const HINT_ID = "search-hint";

/**
 * The search page (US-RA-14): the field with the query from `?q=`, what is searched and the
 * exact-phrase hint. The design has no visible title here, so the heading is for screen readers.
 */
export function SearchPage() {
  const [params] = useSearchParams();

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
    </main>
  );
}
