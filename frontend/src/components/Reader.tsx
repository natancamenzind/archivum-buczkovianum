import { useQuery } from "@tanstack/react-query";
import { type KeyboardEvent, memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";

import type { components } from "@/api/schema";
import { ZoomIcon } from "@/components/icons";
import {
  DocumentSearch,
  PageField,
  type View,
  ViewSwitch,
  ViewToggle,
} from "@/components/ReaderBar";
import { FragmentNote, ReaderMargin } from "@/components/ReaderNotes";
import { ScanPage } from "@/components/ScanPage";
import { ScanZoom } from "@/components/ScanZoom";
import { copy, fragmentLabel } from "@/copy/pl";
import { fetchDocument } from "@/lib/api";
import { DESKTOP, useMediaQuery } from "@/lib/media";
import { type PDFDocumentProxy, usePdf } from "@/lib/pdf";
import {
  findMatches,
  layoutPages,
  type Match,
  matchAt,
  noteId,
  type Page,
  pageOf,
} from "@/lib/reader";
import type { Segment } from "@/lib/segments";
import { cn } from "@/lib/utils";

type Document = components["schemas"]["Document"];
type Fragment = components["schemas"]["DocumentFragment"];

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

/** `?widok=`: the view, by its name in the address (ARC-57). */
const VIEW_PARAM = "widok";
const VIEW_NAMES: Record<View, string> = {
  both: "skan-i-transkrypcja",
  text: "transkrypcja",
  scan: "skan",
};
/** `?strona=`: the page in view (ARC-57). */
const PAGE_PARAM = "strona";
/** The view the reader was last set to, for the next document it opens. */
const VIEW_KEY = "reader-view";

// The tag margin is 200 px wide: four --space-48 and one --space-8.
const MARGIN_WIDTH = "w-[calc(4*var(--space-48)+var(--space-8))]";
// A page scrolled to stops below the reader's sticky bar and, from `lg`, the site header.
const PAGE_SCROLL_MARGIN = "scroll-mt-64 lg:scroll-mt-[calc(3*var(--space-64))]";
// The site header is sticky from `lg`; the reader's bar sticks under it.
const BAR_TOP = "lg:top-[calc(var(--space-64)+var(--space-24))]";
// A single-view column is about as wide as a page of text.
const SINGLE_COLUMN = "w-full max-w-3xl";
// The page in view is the one crossing the middle of the window.
const MIDDLE_LINE = "-50% 0px -50% 0px";

function viewFromName(name: string | null): View | null {
  return (Object.keys(VIEW_NAMES) as View[]).find((view) => VIEW_NAMES[view] === name) ?? null;
}

function storedView(): View | null {
  try {
    return viewFromName(window.localStorage.getItem(VIEW_KEY));
  } catch {
    return null;
  }
}

function storeView(view: View) {
  try {
    window.localStorage.setItem(VIEW_KEY, VIEW_NAMES[view]);
  } catch {
    // Without storage the view is kept in the address only.
  }
}

/** What the reader scrolls to after the next render: a fragment, a match or a page. */
type Target =
  { fragment: number } | { match: number; page: number } | { page: number; focusZoom?: boolean };

/** Of the fragments covering a segment, the shortest: the innermost one. */
function innermost(segment: Segment, fragments: Map<number, Fragment>): Fragment | undefined {
  return segment.ids
    .flatMap((id) => fragments.get(id) ?? [])
    .reduce<Fragment | undefined>(
      (best, fragment) =>
        best === undefined || fragment.end - fragment.start < best.end - best.start
          ? fragment
          : best,
      undefined,
    );
}

interface ReaderPageProps {
  number: number;
  count: number;
  page: Page<Fragment>;
  text: string;
  /** The view shown: on mobile "text" or "scan" only. */
  view: View;
  hasScans: boolean;
  hasMargin: boolean;
  isDesktop: boolean;
  pdf?: PDFDocumentProxy;
  matches: Match[];
  /** The current match's index, or -1. */
  currentMatch: number;
  /** The highlighted and the selected fragment, when this page holds it; otherwise null. */
  active: number | null;
  selected: number | null;
  fragments: Map<number, Fragment>;
  onHover: (id: number | null) => void;
  onSelect: (id: number) => void;
  onZoom: (page: number) => void;
}

/**
 * One page of the reader: its scan, its text and the notes of the fragments starting on it.
 * Memoised, so hovering a fragment redraws only the page that holds it.
 */
const ReaderPage = memo(function ReaderPage({
  number,
  count,
  page,
  text,
  view,
  hasScans,
  hasMargin,
  isDesktop,
  pdf,
  matches,
  currentMatch,
  active,
  selected,
  fragments,
  onHover,
  onSelect,
  onZoom,
}: ReaderPageProps) {
  const notes = page.starts.filter((fragment) => fragment.tags.length > 0);
  const noted = new Set(notes.map((fragment) => fragment.id));
  const showScan = hasScans && view !== "text";
  const showText = view !== "scan";

  function selectByKey(event: KeyboardEvent, id: number) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(id);
    }
  }

  function renderSegment(segment: Segment) {
    const part = text.slice(segment.start, segment.end);
    const match = matchAt(matches, segment.start, segment.end);
    const content =
      match === -1 ? (
        part
      ) : (
        <mark
          key={segment.start}
          data-search-match
          data-match={match}
          aria-current={match === currentMatch ? "true" : undefined}
          className={
            match === currentMatch
              ? "bg-primary text-primary-foreground"
              : "bg-accent text-foreground"
          }
        >
          {part}
        </mark>
      );
    const fragment = innermost(segment, fragments);
    if (fragment === undefined) {
      return content;
    }
    const starts = segment.ids.filter((id) => fragments.get(id)?.start === segment.start);
    return (
      <mark
        key={segment.start}
        role="button"
        tabIndex={0}
        aria-pressed={selected !== null && segment.ids.includes(selected)}
        aria-label={`${fragmentLabel(fragment.number)}: ${part}`}
        aria-describedby={noted.has(fragment.id) ? noteId(fragment.id) : undefined}
        data-fragments={segment.ids.join(" ")}
        data-starts={starts.length > 0 ? starts.join(" ") : undefined}
        data-active={active !== null && segment.ids.includes(active) ? "" : undefined}
        onClick={() => {
          onSelect(fragment.id);
        }}
        onKeyDown={(event) => {
          selectByKey(event, fragment.id);
        }}
        onMouseEnter={() => {
          onHover(fragment.id);
        }}
        onMouseLeave={() => {
          onHover(null);
        }}
        onFocus={() => {
          onHover(fragment.id);
        }}
        onBlur={() => {
          onHover(null);
        }}
        className={cn(
          "cursor-pointer bg-transparent text-accent-foreground underline decoration-accent-border-subtle underline-offset-3 data-active:text-accent-foreground-hover data-active:decoration-accent-border data-active:decoration-2 aria-pressed:decoration-accent-border aria-pressed:decoration-2",
          FOCUS_CLASSES,
        )}
      >
        {content}
      </mark>
    );
  }

  /** On mobile a note stands under the paragraph its fragment starts in. */
  function notesUnder(index: number): Fragment[] {
    if (isDesktop) {
      return [];
    }
    const from = index === 0 ? -Infinity : (page.paragraphs[index]?.start ?? Infinity);
    const to = page.paragraphs[index + 1]?.start ?? Infinity;
    return notes.filter((fragment) => fragment.start >= from && fragment.start < to);
  }

  return (
    <div
      data-page={number}
      className={cn(
        "flex flex-col gap-24 lg:flex-row",
        view !== "both" && "lg:justify-center",
        PAGE_SCROLL_MARGIN,
      )}
    >
      {showScan && (
        <div
          className={cn(
            "flex flex-col gap-12 rounded-md bg-media p-16",
            view === "scan" ? SINGLE_COLUMN : "min-w-0 flex-1",
          )}
        >
          <div className="flex items-center justify-between gap-8">
            <p className="text-cousine-metadane-male text-muted-foreground">
              {copy.reader.page(number, count)}
            </p>
            <button
              type="button"
              data-zoom={number}
              aria-label={copy.reader.zoom(number)}
              onClick={() => {
                onZoom(number);
              }}
              className={cn(
                "flex size-32 items-center justify-center rounded-sm border border-border bg-card text-icon hover:border-accent-border",
                FOCUS_CLASSES,
              )}
            >
              <ZoomIcon className="size-16" />
            </button>
          </div>
          {/* The zoom button above is the keyboard's way in; a click on the scan is a shortcut. */}
          <div
            onClick={() => {
              onZoom(number);
            }}
            className="cursor-zoom-in"
          >
            <ScanPage pdf={pdf} number={number} label={copy.reader.page(number, count)} />
          </div>
        </div>
      )}
      {showText && (
        <div
          className={cn(
            "flex flex-col gap-12",
            view === "text" && hasScans ? SINGLE_COLUMN : "min-w-0 flex-1",
          )}
        >
          {hasScans && (
            <p className="text-cousine-metadane-male text-muted-foreground">
              {copy.reader.textPage(number, count)}
            </p>
          )}
          <div className="flex flex-col gap-24">
            {page.paragraphs.map((paragraph, index) => (
              <div key={paragraph.start} className="flex flex-col gap-12">
                {/* ARC-67: next to a scan the transcript is set smaller. */}
                <p
                  className={cn(
                    hasScans ? "text-lora-tekst-maly" : "text-lora-tekst",
                    "whitespace-pre-wrap text-foreground",
                  )}
                >
                  {paragraph.segments.map(renderSegment)}
                </p>
                {notesUnder(index).map((fragment) => (
                  <FragmentNote
                    key={fragment.id}
                    fragment={fragment}
                    active={active === fragment.id}
                    onHover={onHover}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
      {/* On mobile the "Skan" view lists the page's notes under its scan. */}
      {!isDesktop && !showText && notes.length > 0 && (
        <div className="flex flex-col gap-12">
          {notes.map((fragment) => (
            <FragmentNote
              key={fragment.id}
              fragment={fragment}
              active={active === fragment.id}
              onHover={onHover}
            />
          ))}
        </div>
      )}
      {isDesktop && hasMargin && (
        <ReaderMargin
          notes={notes}
          active={active}
          onHover={onHover}
          view={view}
          className={cn(MARGIN_WIDTH, "shrink-0")}
        />
      )}
    </div>
  );
});

/** "Wczytywanie strony N z M…": the next page's skeleton, which loads it once in view. */
function LoadingPage({
  number,
  count,
  hasScans,
  onVisible,
}: {
  number: number;
  count: number;
  hasScans: boolean;
  onVisible: () => void;
}) {
  const element = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        onVisible();
      }
    });
    if (element.current !== null) {
      observer.observe(element.current);
    }
    return () => {
      observer.disconnect();
    };
  }, [onVisible]);

  return (
    <div ref={element} data-loading-page={number} className="flex flex-col gap-12">
      <p role="status" className="text-cousine-metadane-male text-muted-foreground">
        {copy.reader.pageLoading(number, count)}
      </p>
      <div aria-hidden="true" className="flex gap-24">
        {hasScans && <div className="hidden h-64 flex-1 rounded-md bg-muted lg:block" />}
        <div className="flex flex-1 flex-col gap-12">
          {["w-full", "w-11/12", "w-full", "w-2/3"].map((width, index) => (
            <div key={index} className={cn("h-12 rounded-sm bg-muted", width)} />
          ))}
        </div>
      </div>
    </div>
  );
}

interface ReaderBodyProps {
  document: Document;
  pdf?: PDFDocumentProxy;
  scanFailed: boolean;
  /** The fragment the URL names (`?fragment=`), or null. */
  target: number | null;
  /** The search term the URL names (`?q=`), or "". */
  term: string;
  /** The search field's label; null for a reader without one. */
  searchLabel: string | null;
}

function ReaderBody({ document, pdf, scanFailed, target, term, searchLabel }: ReaderBodyProps) {
  const { text, page_offsets: offsets, fragments } = document;
  const [params, setParams] = useSearchParams();
  const isDesktop = useMediaQuery(DESKTOP);
  const byId = useMemo(
    () => new Map(fragments.map((fragment) => [fragment.id, fragment])),
    [fragments],
  );
  const pageCount = Math.max(offsets.length, 1);
  const hasScans = offsets.length > 0 && !scanFailed;
  const hasMargin = fragments.some((fragment) => fragment.tags.length > 0);

  const [query, setQuery] = useState(term);
  const [matchNumber, setMatchNumber] = useState(0);
  const matches = useMemo(() => findMatches(text, query), [text, query]);
  const pages = useMemo(
    () => layoutPages(text, offsets, fragments, matches),
    [text, offsets, fragments, matches],
  );

  // R-11 AC3: a fragment reference or a search term opens the reader at the fragment or the
  // first match, in a view that shows the text; otherwise `?strona=` names the page.
  const [opening] = useState<{ target: Target | null; page: number; atText: boolean }>(() => {
    const fragment = target === null ? undefined : byId.get(target);
    if (fragment !== undefined) {
      const page = pageOf(offsets, fragment.start);
      return { target: { fragment: fragment.id }, page, atText: true };
    }
    const match = matches[0];
    if (match !== undefined) {
      const page = pageOf(offsets, match.start);
      return { target: { match: 0, page }, page, atText: true };
    }
    const page = Number(params.get(PAGE_PARAM));
    if (Number.isInteger(page) && page > 1 && page <= pageCount) {
      return { target: { page }, page, atText: false };
    }
    return { target: null, page: 1, atText: target !== null || term !== "" };
  });
  const [scrollTarget, setScrollTarget] = useState(opening.target);
  // Pages are mounted from the first on, one more each time the reader nears the last.
  const [mounted, setMounted] = useState(opening.page);
  const [current, setCurrent] = useState(opening.page);

  const [view, setView] = useState<View>(() => {
    const chosen = viewFromName(params.get(VIEW_PARAM)) ?? storedView() ?? "both";
    return opening.atText && chosen === "scan" ? "both" : chosen;
  });
  const shown: View = !hasScans ? "text" : isDesktop ? view : view === "scan" ? "scan" : "text";

  const [selected, setSelected] = useState(target);
  const [hovered, setHovered] = useState<number | null>(null);
  const active = hovered ?? selected;
  const [zoomed, setZoomed] = useState<number | null>(null);
  const pagesElement = useRef<HTMLDivElement>(null);

  const setParam = useCallback(
    (name: string, value: string) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          next.set(name, value);
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const goTo = useCallback((next: Target, page: number) => {
    setMounted((count) => Math.max(count, page));
    setScrollTarget(next);
  }, []);

  const goToPage = useCallback(
    (page: number, focusZoom = false) => {
      setCurrent(page);
      setParam(PAGE_PARAM, String(page));
      goTo({ page, focusZoom }, page);
    },
    [goTo, setParam],
  );

  useEffect(() => {
    const root = pagesElement.current;
    if (scrollTarget === null || root === null) {
      return;
    }
    if ("fragment" in scrollTarget) {
      root
        .querySelector(`[data-fragments~="${String(scrollTarget.fragment)}"]`)
        ?.scrollIntoView({ block: "center" });
    } else if ("match" in scrollTarget) {
      // In the "Skan" view the match is not drawn: the reader goes to its page.
      const mark = root.querySelector(`[data-match="${String(scrollTarget.match)}"]`);
      (mark ?? root.querySelector(`[data-page="${String(scrollTarget.page)}"]`))?.scrollIntoView({
        block: mark === null ? "start" : "center",
      });
    } else {
      root
        .querySelector(`[data-page="${String(scrollTarget.page)}"]`)
        ?.scrollIntoView({ block: "start" });
      if (scrollTarget.focusZoom === true) {
        root.querySelector<HTMLElement>(`[data-zoom="${String(scrollTarget.page)}"]`)?.focus();
      }
    }
    // A scan that cannot be opened leaves the text alone, at full width: scroll to it again.
  }, [scrollTarget, scanFailed]);

  // The page crossing the middle of the window is the page in view, in the field and address.
  useEffect(() => {
    const root = pagesElement.current;
    if (root === null || pageCount < 2) {
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries.find((found) => found.isIntersecting);
        const page = Number((entry?.target as HTMLElement | undefined)?.dataset.page);
        if (page > 0) {
          setCurrent(page);
          setParam(PAGE_PARAM, String(page));
        }
      },
      { rootMargin: MIDDLE_LINE },
    );
    for (const element of root.querySelectorAll("[data-page]")) {
      observer.observe(element);
    }
    return () => {
      observer.disconnect();
    };
  }, [mounted, shown, pageCount, setParam]);

  const chooseView = useCallback(
    (next: View) => {
      setView(next);
      storeView(next);
      setParam(VIEW_PARAM, VIEW_NAMES[next]);
    },
    [setParam],
  );

  const search = useCallback(
    (next: string) => {
      setQuery(next);
      setMatchNumber(0);
      const match = findMatches(text, next)[0];
      if (match !== undefined) {
        const page = pageOf(offsets, match.start);
        goTo({ match: 0, page }, page);
      }
    },
    [text, offsets, goTo],
  );

  const step = useCallback(
    (by: 1 | -1) => {
      const number = (matchNumber + by + matches.length) % matches.length;
      const match = matches[number];
      if (match !== undefined) {
        setMatchNumber(number);
        const page = pageOf(offsets, match.start);
        goTo({ match: number, page }, page);
      }
    },
    [matchNumber, matches, offsets, goTo],
  );

  const select = useCallback((id: number) => {
    setSelected(id);
  }, []);

  const loadNext = useCallback(() => {
    setMounted((count) => Math.min(count + 1, pageCount));
  }, [pageCount]);

  const closeZoom = useCallback(() => {
    if (zoomed !== null) {
      goToPage(zoomed, true);
    }
    setZoomed(null);
  }, [zoomed, goToPage]);

  /** The fragments each page holds, so that a page is redrawn only for its own fragments. */
  const pageIds = useMemo(
    () =>
      pages.map(
        (page) =>
          new Set([
            ...page.starts.map((fragment) => fragment.id),
            ...page.paragraphs.flatMap((paragraph) =>
              paragraph.segments.flatMap((segment) => segment.ids),
            ),
          ]),
      ),
    [pages],
  );

  const hasBar = pageCount > 1 || (hasScans && isDesktop) || searchLabel !== null;

  return (
    <div className="flex flex-col gap-24">
      {hasBar && (
        <div
          className={cn(
            "sticky top-0 z-10 flex flex-col gap-8 rounded-sm border border-border bg-muted p-12 lg:flex-row lg:items-center lg:justify-between lg:gap-16 lg:px-16 lg:py-8",
            BAR_TOP,
          )}
        >
          {pageCount > 1 && <PageField page={current} count={pageCount} onPage={goToPage} />}
          {hasScans && isDesktop && <ViewSwitch view={view} onView={chooseView} />}
          {searchLabel !== null && (
            <DocumentSearch
              label={searchLabel}
              query={query}
              current={matchNumber}
              count={matches.length}
              onQuery={search}
              onStep={step}
            />
          )}
        </div>
      )}
      {hasScans && !isDesktop && <ViewToggle view={view} onView={chooseView} />}
      {scanFailed && (
        <p role="status" className="text-cousine-metadane text-muted-foreground">
          {copy.reader.scanError}
        </p>
      )}
      <div ref={pagesElement} className="flex flex-col gap-32">
        {pages.slice(0, mounted).map((page, index) => {
          const ids = pageIds[index];
          return (
            <ReaderPage
              key={index}
              number={index + 1}
              count={pageCount}
              page={page}
              text={text}
              view={shown}
              hasScans={hasScans}
              hasMargin={hasMargin}
              isDesktop={isDesktop}
              pdf={pdf}
              matches={matches}
              currentMatch={matches.length > 0 ? matchNumber : -1}
              active={active !== null && ids?.has(active) === true ? active : null}
              selected={selected !== null && ids?.has(selected) === true ? selected : null}
              fragments={byId}
              onHover={setHovered}
              onSelect={select}
              onZoom={setZoomed}
            />
          );
        })}
        {mounted < pageCount && (
          <LoadingPage
            key={mounted + 1}
            number={mounted + 1}
            count={pageCount}
            hasScans={hasScans}
            onVisible={loadNext}
          />
        )}
      </div>
      {hasScans && (
        <ScanZoom
          pdf={pdf}
          page={zoomed}
          count={pageCount}
          onPage={setZoomed}
          onClose={closeZoom}
        />
      )}
    </div>
  );
}

/**
 * The reader of every OCR document (R-11, ARC-57). Its bar holds the page field, the view
 * switch ("Skan i transkrypcja", "Transkrypcja", "Skan"; on mobile "Skan" / "Transkrypcja") and
 * the search in the document. Fragments are underlined; each one's tags stand in a note in the
 * right margin (on mobile under its paragraph), and hovering or focusing either one highlights
 * the other. Pages load one at a time as the reader scrolls, and each scan opens in a zoom.
 * `?fragment=<id>` scrolls to that fragment and selects it; `?q=<term>`, from a search result,
 * fills the search and scrolls to the first match; `?strona=` and `?widok=` keep the page and
 * the view. A plain text is shown as text only. The text is split as architecture §4.4 says.
 * A `searchLabel` of null leaves the search out (a secondary text, ARC-66); `?q=` still marks
 * and scrolls to the first match.
 */
export function Reader({
  document,
  searchLabel = copy.reader.search,
}: {
  document: Document;
  searchLabel?: string | null;
}) {
  const [params] = useSearchParams();
  const target = Number(params.get("fragment")) || null;
  const term = params.get("q") ?? "";
  const pdf = usePdf(document.scan);

  return (
    // A new fragment reference or search term starts over: show the text and scroll to it.
    <ReaderBody
      key={`${String(target)} ${term}`}
      document={document}
      pdf={pdf.data}
      scanFailed={pdf.isError}
      target={target}
      term={term}
      searchLabel={searchLabel}
    />
  );
}

/**
 * The reader of the document `id`, with a status line while it loads or when it fails;
 * `hasSearch={false}` leaves out the search in the document.
 */
export function DocumentReader({ id, hasSearch = true }: { id: number; hasSearch?: boolean }) {
  const text = useQuery({ queryKey: ["document", id], queryFn: () => fetchDocument(id) });
  if (text.data === undefined) {
    return (
      <p className="text-cousine-metadane text-muted-foreground" role="status">
        {text.isPending ? copy.reader.loading : copy.reader.error}
      </p>
    );
  }
  return <Reader document={text.data} searchLabel={hasSearch ? undefined : null} />;
}
