import { useSyncExternalStore } from "react";

/** The `lg` breakpoint, where the reader shows its desktop layout (design/rules.md, Siatka). */
export const DESKTOP = "(min-width: 64rem)";

/**
 * Whether the viewport matches a media query, updated as it changes. For layouts that differ
 * in structure, not only in style: the reader's tag notes sit in the margin on desktop and
 * under their paragraph on mobile, and two copies of them would repeat every tag link.
 */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const list = window.matchMedia(query);
      list.addEventListener("change", onChange);
      return () => {
        list.removeEventListener("change", onChange);
      };
    },
    () => window.matchMedia(query).matches,
  );
}
