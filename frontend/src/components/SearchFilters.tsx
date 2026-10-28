import type { ReactNode } from "react";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { CheckIcon, ChevronDownIcon, CloseIcon } from "@/components/icons";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { copy } from "@/copy/pl";
import { filterCount, type SearchState, withoutFilters } from "@/lib/search";
import { cn } from "@/lib/utils";

type Facets = components["schemas"]["SearchFacets"];

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
const BUTTON_CLASSES = `flex grow items-center justify-center rounded-sm px-24 py-12 text-cousine-etykieta transition-colors duration-150 ease-out motion-reduce:transition-none ${FOCUS_CLASSES}`;

interface FiltersProps {
  facets: Facets;
  state: SearchState;
  onChange: (state: SearchState) => void;
}

/** "Pole wyboru" in design/components/: a checkbox with its label and count. */
function Checkbox({
  label,
  count,
  checked,
  onChange,
}: {
  label: string;
  count: number;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-8">
      <span className="relative flex shrink-0">
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => {
            onChange(event.target.checked);
          }}
          className={`peer size-16 cursor-pointer appearance-none rounded-sm border border-accent-border bg-card checked:bg-primary ${FOCUS_CLASSES}`}
        />
        <CheckIcon className="pointer-events-none absolute inset-0 m-auto size-12 text-inverse-icon opacity-0 peer-checked:opacity-100" />
      </span>
      <span className="text-cousine-metadane text-foreground">{label}</span>{" "}
      <span className="text-cousine-metadane-male text-muted-foreground">{count}</span>
    </label>
  );
}

function FilterGroup({
  label,
  count,
  children,
}: {
  label: string;
  count?: number;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-8">
      <ColumnHeader label={label} count={count} />
      {children}
    </div>
  );
}

/**
 * The search filters (US-RA-16 AC2), each value with its count: works, availability and the
 * decade of the first edition. Every change goes straight to the URL.
 */
export function SearchFilters({ facets, state, onChange }: FiltersProps) {
  const { searchFilters } = copy;
  return (
    <div className="flex flex-col gap-32">
      {facets.works.length > 0 && (
        <FilterGroup label={searchFilters.work} count={facets.works.length}>
          {facets.works.map((work) => (
            <Checkbox
              key={work.id}
              label={work.title}
              count={work.count}
              checked={state.works.includes(work.id)}
              onChange={(checked) => {
                onChange({
                  ...state,
                  works: checked
                    ? [...state.works, work.id]
                    : state.works.filter((id) => id !== work.id),
                });
              }}
            />
          ))}
        </FilterGroup>
      )}
      <FilterGroup label={searchFilters.availability}>
        <Checkbox
          label={searchFilters.hasScan}
          count={facets.has_scan}
          checked={state.hasScan}
          onChange={(hasScan) => {
            onChange({ ...state, hasScan });
          }}
        />
        <Checkbox
          label={searchFilters.hasText}
          count={facets.has_text}
          checked={state.hasText}
          onChange={(hasText) => {
            onChange({ ...state, hasText });
          }}
        />
      </FilterGroup>
      {facets.decades.length > 0 && (
        <FilterGroup label={searchFilters.period}>
          <select
            aria-label={searchFilters.period}
            value={state.decade ?? ""}
            onChange={(event) => {
              const decade = event.target.value;
              onChange({ ...state, decade: decade === "" ? null : Number(decade) });
            }}
            className={`w-full rounded-sm border border-accent-border bg-card px-12 py-8 text-cousine-metadane text-foreground ${FOCUS_CLASSES}`}
          >
            <option value="">{searchFilters.allYears}</option>
            {facets.decades.map(({ decade, count }) => (
              <option key={decade} value={decade}>
                {searchFilters.decade(decade, count)}
              </option>
            ))}
          </select>
        </FilterGroup>
      )}
    </div>
  );
}

/**
 * The mobile filter panel (US-RA-16 AC3, design/rules.md): "Filtry (n)" opens the filters full
 * screen, over the header, with the actions pinned to the bottom. "Wyczyść" clears the filters
 * and keeps the panel open; "Pokaż wyniki (n)" closes it.
 */
export function FilterPanel({
  facets,
  state,
  onChange,
  total,
  open,
  onOpenChange,
}: Omit<FiltersProps, "facets"> & {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Undefined until the first results arrive. */
  facets: Facets | undefined;
  /** The filtered result count; undefined while it loads. */
  total: number | undefined;
}) {
  const { searchFilters } = copy;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger
        disabled={facets === undefined}
        className={`flex grow items-center justify-between rounded-sm border border-accent-border bg-card px-12 py-8 text-cousine-metadane text-foreground disabled:opacity-40 md:hidden ${FOCUS_CLASSES}`}
      >
        {searchFilters.open(filterCount(state))}
        <ChevronDownIcon className="size-16 text-icon" />
      </DialogTrigger>
      {facets !== undefined && (
        <DialogContent aria-describedby={undefined}>
          <div className="flex items-center justify-between border-b border-border px-page-mobile py-12">
            <DialogTitle>{searchFilters.title}</DialogTitle>
            <DialogClose
              aria-label={searchFilters.close}
              className={`flex rounded-sm p-12 text-icon ${FOCUS_CLASSES}`}
            >
              <CloseIcon className="size-16" />
            </DialogClose>
          </div>
          <div
            aria-busy={total === undefined}
            className={cn(
              "flex-1 overflow-y-auto px-page-mobile pt-24 pb-48",
              total === undefined && "opacity-40",
            )}
          >
            <SearchFilters facets={facets} state={state} onChange={onChange} />
          </div>
          <div className="flex gap-12 border-t border-border bg-background px-page-mobile py-16">
            <button
              type="button"
              onClick={() => {
                onChange(withoutFilters(state));
              }}
              className={cn(
                BUTTON_CLASSES,
                "border border-accent-border bg-card text-accent-foreground hover:bg-accent",
              )}
            >
              {searchFilters.clear}
            </button>
            <DialogClose
              className={cn(
                BUTTON_CLASSES,
                "bg-primary text-primary-foreground hover:bg-primary-hover",
              )}
            >
              {searchFilters.show(total === undefined ? searchFilters.pending : String(total))}
            </DialogClose>
          </div>
        </DialogContent>
      )}
    </Dialog>
  );
}
