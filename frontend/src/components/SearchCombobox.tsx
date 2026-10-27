import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { type ComponentProps, type KeyboardEvent, useEffect, useId, useState } from "react";
import { useNavigate } from "react-router";

import type { components } from "@/api/schema";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Suggestion = components["schemas"]["Suggestion"];

// One letter matches too much to be worth suggesting.
const MIN_LENGTH = 2;
const DEBOUNCE_MS = 150;

async function fetchSuggestions(q: string): Promise<Suggestion[]> {
  const { data, response } = await api.GET("/api/search/autocomplete/", {
    params: { query: { q } },
  });
  if (data === undefined) {
    throw new Error(`The autocomplete request failed with ${String(response.status)}.`);
  }
  return data;
}

/** `value`, once it has not changed for a moment, so not every keystroke asks the API. */
function useSettled(value: string): string {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => {
      setSettled(value);
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
    };
  }, [value]);
  return settled;
}

interface SearchComboboxProps extends Omit<
  ComponentProps<"input">,
  "value" | "onChange" | "onKeyDown" | "onBlur" | "type" | "role"
> {
  value: string;
  onValueChange: (value: string) => void;
  /** Placement of the suggestion list, against the nearest positioned ancestor. */
  listClassName: string;
}

/**
 * A search field's input with suggestions of works and tags under it (US-RA-17). Choosing one,
 * by click or with the arrows and Enter, opens its page; Enter with none chosen submits the form.
 */
export function SearchCombobox({
  value,
  onValueChange,
  listClassName,
  ...inputProps
}: SearchComboboxProps) {
  const navigate = useNavigate();
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const q = useSettled(value.trim());
  const query = useQuery({
    queryKey: ["autocomplete", q],
    queryFn: () => fetchSuggestions(q),
    // Only once the reader has typed and paused; not for the query a field opens with.
    enabled: open && q.length >= MIN_LENGTH && q === value.trim(),
    // The list keeps the last suggestions while the text settles, instead of flickering.
    placeholderData: keepPreviousData,
  });
  const suggestions = value.trim().length >= MIN_LENGTH ? (query.data ?? []) : [];
  const expanded = open && suggestions.length > 0;
  const activeIndex = expanded && active < suggestions.length ? active : -1;

  function close() {
    setOpen(false);
    setActive(-1);
  }

  function choose(suggestion: Suggestion) {
    close();
    onValueChange("");
    void navigate(suggestion.url);
  }

  function move(step: 1 | -1) {
    const count = suggestions.length;
    setOpen(true);
    setActive(
      activeIndex === -1 ? (step === 1 ? 0 : count - 1) : (activeIndex + step + count) % count,
    );
  }

  function keyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing) {
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (suggestions.length > 0) {
        move(event.key === "ArrowDown" ? 1 : -1);
      } else {
        setOpen(true);
      }
    } else if (event.key === "Enter") {
      const chosen = activeIndex === -1 ? undefined : suggestions[activeIndex];
      if (chosen) {
        event.preventDefault();
        choose(chosen);
      } else {
        close();
      }
    } else if (event.key === "Escape" && expanded) {
      // Without this, Escape also empties a search input.
      event.preventDefault();
      close();
    }
  }

  return (
    <>
      <input
        {...inputProps}
        type="search"
        role="combobox"
        autoComplete="off"
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls={expanded ? listId : undefined}
        aria-activedescendant={activeIndex === -1 ? undefined : `${listId}-${String(activeIndex)}`}
        value={value}
        onChange={(event) => {
          onValueChange(event.target.value);
          setOpen(true);
          setActive(-1);
        }}
        onKeyDown={keyDown}
        onBlur={close}
      />
      {expanded && (
        <ul
          id={listId}
          role="listbox"
          aria-label={copy.search.suggestions}
          className={cn(
            "absolute top-full z-10 flex flex-col rounded-sm border border-accent-border bg-popover py-4 shadow-raised",
            listClassName,
          )}
        >
          {suggestions.map((suggestion, index) => (
            <li
              key={suggestion.url}
              id={`${listId}-${String(index)}`}
              role="option"
              aria-selected={index === activeIndex}
              // Keeps the focus in the field, so its blur does not close the list before the click.
              onMouseDown={(event) => {
                event.preventDefault();
              }}
              onMouseEnter={() => {
                setActive(index);
              }}
              onClick={() => {
                choose(suggestion);
              }}
              className="flex cursor-pointer items-baseline justify-between gap-16 px-16 py-8 aria-selected:bg-accent"
            >
              <span className="text-lora-tekst text-foreground">{suggestion.title}</span>{" "}
              <span className="text-cousine-metadane-male text-muted-foreground">
                {copy.search.suggestionTypes[suggestion.type]}
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
