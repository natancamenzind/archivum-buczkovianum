import type { ReactNode } from "react";

import { DraftBanner } from "@/components/DraftBanner";
import { cn } from "@/lib/utils";

interface EntityLayoutProps {
  /** The API's `is_draft`: staff are previewing a draft, which gets the draft banner (US-WR-13). */
  isDraft: boolean;
  /** The hero: a `PageHeader` with the entity's type line, title and description. */
  header: ReactNode;
  /** The context column on the left (R-03). Leave it out when it is empty (R-02). */
  context?: ReactNode;
  /**
   * The reader (R-11) and what goes with it, at the full width of the content (ARC-57). With a
   * reader the page has no context column: the context is a row under the hero.
   */
  reader?: ReactNode;
  main: ReactNode;
  /** The tag column on the right. Leave it out when it is empty (R-02). */
  tags?: ReactNode;
  /** The contextual materials block (R-08) below the columns. */
  materials?: ReactNode;
}

/**
 * The subpage layout shared by every entity page (R-05): hero, context column, main column and
 * tag column, then the contextual materials block. On mobile the order is main, context, tags,
 * materials (design/rules.md, Siatka). A page with a reader has the context in a row under the
 * hero, then the reader at full width, then the main and tag columns (ARC-57).
 */
export function EntityLayout({
  isDraft,
  header,
  context,
  reader,
  main,
  tags,
  materials,
}: EntityLayoutProps) {
  const hasReader = reader !== undefined;
  return (
    <main className="flex flex-col">
      {isDraft && <DraftBanner />}
      {header}
      {hasReader && context !== undefined && (
        <div className="flex flex-col gap-24 px-page-mobile pt-24 lg:flex-row lg:gap-32 lg:px-page lg:pt-32">
          {context}
        </div>
      )}
      {hasReader && (
        <div className="flex flex-col gap-24 px-page-mobile pt-24 lg:px-page lg:pt-32">
          {reader}
        </div>
      )}
      <div
        className={cn(
          "flex flex-col gap-24 px-page-mobile pt-24 pb-32 lg:grid lg:items-start lg:gap-32 lg:px-page lg:pt-32 lg:pb-48",
          hasReader
            ? "lg:grid-cols-[minmax(0,1fr)_var(--container-3xs)]"
            : "lg:grid-cols-[var(--container-3xs)_minmax(0,1fr)_var(--container-3xs)]",
        )}
      >
        <div
          className={cn(
            "flex flex-col gap-24 lg:row-start-1",
            hasReader ? "lg:col-start-1" : "lg:col-start-2",
          )}
        >
          {main}
        </div>
        {!hasReader && context !== undefined && (
          <div className="flex flex-col gap-32 lg:col-start-1 lg:row-start-1">{context}</div>
        )}
        {tags !== undefined && (
          <div
            className={cn(
              "flex flex-col gap-32 lg:row-start-1",
              hasReader ? "lg:col-start-2" : "lg:col-start-3",
            )}
          >
            {tags}
          </div>
        )}
      </div>
      {/* Hidden when the block renders nothing (R-02). */}
      {materials !== undefined && (
        <div className="px-page-mobile pb-32 empty:hidden lg:px-page lg:pb-48">{materials}</div>
      )}
    </main>
  );
}
