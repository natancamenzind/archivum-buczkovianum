import { Link } from "react-router";

import { ArrowRightIcon } from "@/components/icons";

interface ListRowProps {
  /** "Nr": the 1-based position, shown with two digits ("01"). */
  number: number;
  title: string;
  to: string;
}

/**
 * "Wiersz listy" in design/components/: a numbered row over a subtle rule that links to a page.
 * The number is decorative, since the row sits in an ordered list; the title names the link.
 */
export function ListRow({ number, title, to }: ListRowProps) {
  return (
    <Link
      to={to}
      className="flex items-center justify-between gap-12 border-b border-border py-12 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <span className="flex items-center gap-12">
        <span aria-hidden="true" className="text-cousine-metadane-male text-muted-foreground">
          {String(number).padStart(2, "0")}
        </span>
        <span className="text-lora-tekst-maly text-foreground">{title}</span>
      </span>
      <ArrowRightIcon className="size-16 shrink-0 text-accent-icon" />
    </Link>
  );
}
