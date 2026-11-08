import { type KeyboardEvent, useId, useState } from "react";

import { ChevronLeftIcon, ChevronRightIcon, CloseIcon, SearchIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

export type View = "both" | "text" | "scan";

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
const ICON_BUTTON_CLASSES = cn(
  "flex size-32 shrink-0 items-center justify-center rounded-sm text-foreground hover:bg-card disabled:text-muted-foreground disabled:hover:bg-transparent",
  FOCUS_CLASSES,
);

interface PageFieldProps {
  /** The page in view (from 1). */
  page: number;
  count: number;
  onPage: (page: number) => void;
}

/**
 * "Pole strony": "Strona [9] z 137" with arrows (ARC-57). The number follows the page in view;
 * typing one and pressing Enter goes there, and a number out of range says which are valid.
 */
export function PageField({ page, count, onPage }: PageFieldProps) {
  const [draft, setDraft] = useState<string | null>(null);
  const [invalid, setInvalid] = useState(false);
  const errorId = useId();

  function commit() {
    if (draft === null) {
      return;
    }
    const number = Number(draft);
    if (!Number.isInteger(number) || number < 1 || number > count) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setDraft(null);
    onPage(number);
  }

  function keyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      commit();
    } else if (event.key === "Escape") {
      setDraft(null);
      setInvalid(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-8">
        <span className="text-cousine-metadane-male text-muted-foreground uppercase">
          {copy.reader.pageField}
        </span>
        <button
          type="button"
          aria-label={copy.reader.previousPage}
          disabled={page <= 1}
          onClick={() => {
            onPage(page - 1);
          }}
          className={ICON_BUTTON_CLASSES}
        >
          <ChevronLeftIcon className="size-16" />
        </button>
        <input
          type="text"
          inputMode="numeric"
          aria-label={copy.reader.pageNumber}
          aria-invalid={invalid}
          aria-describedby={invalid ? errorId : undefined}
          value={draft ?? String(page)}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          onKeyDown={keyDown}
          onBlur={() => {
            if (!invalid) {
              setDraft(null);
            }
          }}
          className={cn(
            "w-64 rounded-sm border border-border bg-card px-8 py-4 text-center text-cousine-metadane text-foreground aria-invalid:border-accent-border",
            FOCUS_CLASSES,
          )}
        />
        <span className="text-cousine-metadane-male text-muted-foreground">
          {copy.reader.pageOf(count)}
        </span>
        <button
          type="button"
          aria-label={copy.reader.nextPage}
          disabled={page >= count}
          onClick={() => {
            onPage(page + 1);
          }}
          className={ICON_BUTTON_CLASSES}
        >
          <ChevronRightIcon className="size-16" />
        </button>
      </div>
      {invalid && (
        <p id={errorId} role="alert" className="text-cousine-metadane-male text-accent-foreground">
          {copy.reader.pageRange(count)}
        </p>
      )}
    </div>
  );
}

const VIEWS: View[] = ["both", "text", "scan"];

/**
 * "Widok czytnika" on desktop: "Skan i transkrypcja", "Transkrypcja", "Skan" (ARC-57). A radio
 * group: the arrow keys move between the views, Tab leaves the group.
 */
export function ViewSwitch({ view, onView }: { view: View; onView: (view: View) => void }) {
  function keyDown(event: KeyboardEvent) {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key];
    if (step === undefined) {
      return;
    }
    event.preventDefault();
    const next = VIEWS[(VIEWS.indexOf(view) + step + VIEWS.length) % VIEWS.length] ?? view;
    onView(next);
    event.currentTarget.querySelector<HTMLElement>(`[data-view="${next}"]`)?.focus();
  }

  return (
    <div
      role="radiogroup"
      aria-label={copy.reader.views}
      onKeyDown={keyDown}
      className="flex items-center gap-4 rounded-sm border border-border bg-muted p-4"
    >
      {VIEWS.map((option) => (
        <button
          key={option}
          type="button"
          role="radio"
          data-view={option}
          aria-checked={view === option}
          tabIndex={view === option ? 0 : -1}
          onClick={() => {
            onView(option);
          }}
          className={cn(
            "rounded-sm border border-transparent px-12 py-4 text-cousine-metadane text-muted-foreground hover:text-foreground aria-checked:border-accent-border aria-checked:bg-card aria-checked:text-accent-foreground",
            FOCUS_CLASSES,
          )}
        >
          {copy.reader[option]}
        </button>
      ))}
    </div>
  );
}

/** The mobile "Skan" / "Transkrypcja" toggle (R-11 AC1). */
export function ViewToggle({ view, onView }: { view: View; onView: (view: View) => void }) {
  return (
    <div role="group" aria-label={copy.reader.views} className="flex gap-8">
      {(["scan", "text"] as const).map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={option === "scan" ? view === "scan" : view !== "scan"}
          onClick={() => {
            onView(option);
          }}
          className={cn(
            "rounded-full border border-border px-12 py-4 text-cousine-metadane text-foreground aria-pressed:border-accent-border aria-pressed:bg-accent aria-pressed:text-accent-foreground",
            FOCUS_CLASSES,
          )}
        >
          {copy.reader[option]}
        </button>
      ))}
    </div>
  );
}

interface SearchProps {
  label: string;
  query: string;
  /** The current match (from 0) and the number of matches. */
  current: number;
  count: number;
  onQuery: (query: string) => void;
  onStep: (step: 1 | -1) => void;
}

/**
 * "Szukaj w maszynopisie" (ARC-57): a counter of matches ("1 z 6"); Enter, Shift+Enter and the
 * arrows move between them; Esc clears the field.
 */
export function DocumentSearch({ label, query, current, count, onQuery, onStep }: SearchProps) {
  function keyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (count > 0) {
        onStep(event.key === "ArrowUp" || (event.key === "Enter" && event.shiftKey) ? -1 : 1);
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      onQuery("");
    }
  }

  return (
    <div
      role="search"
      className="flex min-h-[calc(var(--space-32)+var(--space-8))] w-full items-center gap-8 rounded-sm border border-border bg-card pr-4 pl-12 has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-ring lg:max-w-sm"
    >
      <SearchIcon className="size-16 shrink-0 text-icon" />
      <input
        type="search"
        aria-label={label}
        placeholder={label}
        value={query}
        onChange={(event) => {
          onQuery(event.target.value);
        }}
        onKeyDown={keyDown}
        className="min-w-0 flex-1 bg-transparent text-lora-tekst-maly text-foreground outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:appearance-none"
      />
      {query.trim() !== "" && (
        <>
          <span
            aria-live="polite"
            className="shrink-0 text-cousine-metadane-male text-muted-foreground"
          >
            {count === 0 ? copy.reader.noMatches : copy.reader.matches(current + 1, count)}
          </span>
          <button
            type="button"
            aria-label={copy.reader.previousMatch}
            disabled={count === 0}
            onClick={() => {
              onStep(-1);
            }}
            className={ICON_BUTTON_CLASSES}
          >
            <ChevronLeftIcon className="size-16 rotate-90" />
          </button>
          <button
            type="button"
            aria-label={copy.reader.nextMatch}
            disabled={count === 0}
            onClick={() => {
              onStep(1);
            }}
            className={ICON_BUTTON_CLASSES}
          >
            <ChevronRightIcon className="size-16 rotate-90" />
          </button>
          <button
            type="button"
            aria-label={copy.reader.clearSearch}
            onClick={() => {
              onQuery("");
            }}
            className={ICON_BUTTON_CLASSES}
          >
            <CloseIcon className="size-16" />
          </button>
        </>
      )}
    </div>
  );
}
