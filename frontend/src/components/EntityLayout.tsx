import type { ReactNode } from "react";

interface EntityLayoutProps {
  /** The hero: a `PageHeader` with the entity's type line, title and description. */
  header: ReactNode;
  /** The context column on the left (R-03). Leave it out when it is empty (R-02). */
  context?: ReactNode;
  main: ReactNode;
  /** The tag column on the right. Leave it out when it is empty (R-02). */
  tags?: ReactNode;
  /** The contextual materials block (R-08) below the columns. */
  materials?: ReactNode;
}

/**
 * The subpage layout shared by every entity page (R-05): hero, context column, main column and
 * tag column, then the contextual materials block. On mobile the order is main, context, tags,
 * materials (design/rules.md, Siatka).
 */
export function EntityLayout({ header, context, main, tags, materials }: EntityLayoutProps) {
  return (
    <main className="flex flex-col">
      {header}
      <div className="flex flex-col gap-24 px-page-mobile pt-24 pb-32 lg:grid lg:grid-cols-[var(--container-3xs)_minmax(0,1fr)_var(--container-3xs)] lg:items-start lg:gap-32 lg:px-page lg:pt-32 lg:pb-48">
        <div className="flex flex-col gap-24 lg:col-start-2 lg:row-start-1">{main}</div>
        {context !== undefined && (
          <div className="flex flex-col gap-32 lg:col-start-1 lg:row-start-1">{context}</div>
        )}
        {tags !== undefined && (
          <div className="flex flex-col gap-32 lg:col-start-3 lg:row-start-1">{tags}</div>
        )}
      </div>
      {/* Hidden when the block renders nothing (R-02). */}
      {materials !== undefined && (
        <div className="px-page-mobile pb-32 empty:hidden lg:px-page lg:pb-48">{materials}</div>
      )}
    </main>
  );
}
