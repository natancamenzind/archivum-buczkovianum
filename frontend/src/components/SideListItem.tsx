import { Link } from "react-router";

import { cn } from "@/lib/utils";

interface SideListItemProps {
  /** "Rok": the line above the title, e.g. the year or a shelfmark. Rendered only when given. */
  meta?: string;
  title: string;
  /** "Opis": the line under the title. Rendered only when given. */
  description?: string;
  /** The item's page. Without one, as for an edition, the item is not a link. */
  to?: string;
  /** "Aktywny": the object the page shows. */
  current?: boolean;
}

/**
 * "Element listy bocznej" in design/components/: an item of an entity page's context column
 * (R-03), linking to its page if it has one. The current item has the accent rule and year.
 */
export function SideListItem({ meta, title, description, to, current = false }: SideListItemProps) {
  const className = cn(
    "flex flex-col gap-4 border-l border-border py-8 pl-12",
    current && "border-l-2 border-accent-border",
  );
  const content = (
    <>
      {meta !== undefined && (
        <span
          className={cn(
            "text-cousine-metadane-male",
            current ? "text-accent-foreground" : "text-muted-foreground",
          )}
        >
          {meta}
        </span>
      )}
      <span className="text-lora-tekst text-foreground">{title}</span>
      {description !== undefined && (
        <span className="text-cousine-metadane-male text-muted-foreground">{description}</span>
      )}
    </>
  );

  if (to === undefined) {
    return <div className={className}>{content}</div>;
  }
  return (
    <Link
      to={to}
      aria-current={current ? "page" : undefined}
      className={cn(
        className,
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
      )}
    >
      {content}
    </Link>
  );
}
