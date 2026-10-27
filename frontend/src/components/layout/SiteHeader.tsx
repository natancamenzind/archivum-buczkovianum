import { Link } from "react-router";

import { BookIcon } from "@/components/icons";
import { copy } from "@/copy/pl";

const LINK_CLASSES =
  "transition-colors duration-150 ease-out motion-reduce:transition-none hover:text-accent-foreground focus-visible:text-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

/** "Nagłówek serwisu" in design/components/: service name and subtitle, "O archiwum" (R-07). */
export function SiteHeader() {
  return (
    <header className="flex h-64 items-center justify-between border-t-3 border-b border-t-primary border-b-border bg-background px-page-mobile md:h-auto md:px-page md:py-32">
      <Link to="/" className={`flex items-center gap-12 ${LINK_CLASSES}`}>
        <BookIcon className="size-24 text-accent-icon" />
        <span className="text-lora-tekst text-foreground md:text-lora-tytul-elementu">
          {copy.siteName}
        </span>{" "}
        {/* Figma's mobile header drops the subtitle, so below `md` the link's accessible name is
            only "Archivum Buczkovianum". From `md` up, the space keeps the two parts apart:
            "Archivum Buczkovianum Archiwum literackie". */}
        <span className="hidden text-cousine-metadane-male text-muted-foreground md:inline">
          {copy.layout.headerSubtitle}
        </span>
      </Link>
      <div className="flex items-center gap-32">
        <Link to="/about" className={`text-cousine-nawigacja text-foreground ${LINK_CLASSES}`}>
          {copy.layout.about}
        </Link>
        {/* The search field (an icon on mobile) comes here in step 29, US-RA-14. */}
      </div>
    </header>
  );
}
