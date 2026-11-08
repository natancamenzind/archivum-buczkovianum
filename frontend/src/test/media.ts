let width = 1440;

/**
 * jsdom has no `matchMedia`. This one answers `min-width` and `max-width` queries in rem (16 px)
 * or px against a viewport width a test sets with `setViewport()`: desktop by default.
 */
function matches(query: string): boolean {
  return query.split(" and ").every((part) => {
    const found = /\((min|max)-width:\s*([\d.]+)(rem|px)\)/.exec(part);
    if (found === null) {
      return false;
    }
    const [, bound, value, unit] = found;
    const limit = Number(value) * (unit === "rem" ? 16 : 1);
    return bound === "min" ? width >= limit : width <= limit;
  });
}

export function setViewport(viewport: "desktop" | "mobile"): void {
  width = viewport === "desktop" ? 1440 : 390;
}

export function installMatchMedia(): void {
  // The viewport never changes during a test, so the list never fires "change".
  window.matchMedia = (query: string) =>
    Object.assign(new EventTarget(), {
      media: query,
      matches: matches(query),
      onchange: null,
    }) as MediaQueryList;
}
