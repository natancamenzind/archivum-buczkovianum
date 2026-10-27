import { type SubmitEvent, useRef, useState } from "react";
import { useNavigate } from "react-router";

import { CloseIcon, SearchIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { searchUrl } from "@/lib/search";

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

interface SearchFieldProps {
  /** The query the field starts with. */
  query: string;
  /** The ID of the heading that names the search landmark. */
  labelledBy: string;
}

/**
 * "Pole wyszukiwania" in design/components/: the search page's field, with "Wyczyść" while it
 * holds text. Submitting opens the search page for the trimmed query.
 */
export function SearchField({ query, labelledBy }: SearchFieldProps) {
  const [value, setValue] = useState(query);
  const input = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

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
