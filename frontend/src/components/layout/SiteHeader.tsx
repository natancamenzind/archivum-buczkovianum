import { type SubmitEvent, useRef } from "react";
import { Link, useNavigate } from "react-router";

import { BookIcon, SearchIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { searchUrl } from "@/lib/search";

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

const LINK_CLASSES = `transition-colors duration-150 ease-out motion-reduce:transition-none hover:text-accent-foreground focus-visible:text-accent-foreground ${FOCUS_CLASSES}`;

/**
 * "Nagłówek serwisu" in design/components/: service name and subtitle, "O archiwum" and the
 * search field (R-07). On mobile the field becomes an icon linking to the search page.
 */
export function SiteHeader() {
  const input = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  function search(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    void navigate(searchUrl(input.current?.value ?? ""));
    // The search page shows the query in its own field.
    event.currentTarget.reset();
  }

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
      <div className="flex items-center gap-16 md:gap-32">
        <Link to="/about" className={`text-cousine-nawigacja text-foreground ${LINK_CLASSES}`}>
          {copy.layout.about}
        </Link>
        <form
          role="search"
          aria-label={copy.search.label}
          onSubmit={search}
          className="hidden items-center gap-8 md:flex"
        >
          <SearchIcon className="size-16 shrink-0 text-icon" />
          {/* The design shows the field as its placeholder, in the navigation's colour. */}
          <input
            ref={input}
            type="search"
            aria-label={copy.search.label}
            placeholder={copy.search.label}
            className={`max-w-xs bg-transparent text-cousine-nawigacja text-foreground field-sizing-content placeholder:text-foreground [&::-webkit-search-cancel-button]:appearance-none ${FOCUS_CLASSES}`}
          />
        </form>
        <Link
          to="/search"
          aria-label={copy.search.label}
          className={`p-16 text-foreground md:hidden ${LINK_CLASSES}`}
        >
          <SearchIcon className="size-16" />
        </Link>
      </div>
    </header>
  );
}
