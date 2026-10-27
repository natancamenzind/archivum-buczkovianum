import { type SubmitEvent, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { CloseIcon, SearchIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { searchUrl } from "@/lib/search";

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

interface SearchFieldProps {
  /** The query in the URL, shown again after every navigation. */
  query: string;
  /** The ID of the heading that names the search landmark. */
  labelledBy: string;
  /** The IDs of the texts that describe the field. */
  describedBy: string;
}

/**
 * "Pole wyszukiwania" in design/components/: the search page's field, with "Wyczyść" while it
 * holds text. Submitting opens the search page for the trimmed query.
 */
export function SearchField({ query, labelledBy, describedBy }: SearchFieldProps) {
  const [value, setValue] = useState(query);
  const location = useLocation();
  const [shownLocation, setShownLocation] = useState(location.key);
  const input = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Every search, even for the same query, shows the URL's query again. Updated during render
  // rather than by remounting, so a submit keeps the focus where it was.
  if (location.key !== shownLocation) {
    setShownLocation(location.key);
    setValue(query);
  }

  function search(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    void navigate(searchUrl(value));
  }

  return (
    <form
      role="search"
      aria-labelledby={labelledBy}
      onSubmit={search}
      className="flex items-center gap-12 rounded-sm border border-accent-border bg-card py-8 pr-8 pl-16 has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-ring"
    >
      <SearchIcon className="size-16 shrink-0 text-icon" />
      <input
        ref={input}
        type="search"
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
        }}
        aria-label={copy.search.label}
        aria-describedby={describedBy}
        placeholder={copy.search.placeholder}
        className="min-w-0 flex-1 bg-transparent text-lora-tytul-elementu text-foreground outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:appearance-none"
      />
      {value !== "" && (
        <button
          type="button"
          aria-label={copy.search.clear}
          onClick={() => {
            setValue("");
            input.current?.focus();
          }}
          className={`rounded-sm p-12 text-icon transition-colors duration-150 ease-out hover:text-accent-foreground motion-reduce:transition-none ${FOCUS_CLASSES}`}
        >
          <CloseIcon className="size-16" />
        </button>
      )}
      <button
        type="submit"
        className={`rounded-sm bg-primary px-24 py-12 text-cousine-etykieta text-primary-foreground transition-colors duration-150 ease-out hover:bg-primary-hover focus-visible:bg-primary-hover motion-reduce:transition-none ${FOCUS_CLASSES}`}
      >
        {copy.search.submit}
      </button>
    </form>
  );
}
