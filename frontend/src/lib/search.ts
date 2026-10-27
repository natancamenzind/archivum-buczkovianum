/** The search page's URL for `query` (architecture §8): `/search?q=…`, or `/search` when blank. */
export function searchUrl(query: string): string {
  const q = query.trim();
  return q === "" ? "/search" : `/search?${new URLSearchParams({ q }).toString()}`;
}
