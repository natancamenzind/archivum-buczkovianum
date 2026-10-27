import { useQuery } from "@tanstack/react-query";
import { type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";

import type { components } from "@/api/schema";
import { TagList } from "@/components/TagList";
import { copy, fragmentLabel } from "@/copy/pl";
import { loadPdf, type PDFDocumentProxy, type RenderTask } from "@/lib/pdf";
import { type Segment, segments } from "@/lib/segments";
import { cn } from "@/lib/utils";

type Document = components["schemas"]["Document"];
type Fragment = components["schemas"]["DocumentFragment"];
type View = "scan" | "text";

// Pages are drawn at 1.5× their PDF size and scaled down to the column, so text stays sharp.
const SCAN_SCALE = 1.5;

// A scan page is drawn while it is within one screen of the view, so a long typescript keeps
// only a few drawn pages in memory.
const DRAW_MARGIN = "100% 0px";

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

/**
 * One scan page, drawn by pdf.js once the scan is open and the page nears the view, and dropped
 * when it moves away. A page that fails to draw stays blank; the reader reports a scan that
 * cannot be opened.
 */
function ScanPage({
  pdf,
  number,
  label,
}: {
  pdf?: PDFDocumentProxy;
  number: number;
  label: string;
}) {
  const frame = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [near, setNear] = useState(false);
  // Until it is first drawn, a page keeps the A4 proportions of a typescript page, then its
  // own, so the reader's scroll position holds as pages are drawn and dropped.
  const [ratio, setRatio] = useState("210 / 297");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          setNear(entry.isIntersecting);
        }
      },
      { rootMargin: DRAW_MARGIN },
    );
    if (frame.current !== null) {
      observer.observe(frame.current);
    }
    return () => {
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (pdf === undefined || !near) {
      return;
    }
    let cancelled = false;
    let task: RenderTask | undefined;
    pdf
      .getPage(number)
      .then((page) => {
        const element = canvas.current;
        if (cancelled || element === null) {
          return;
        }
        const viewport = page.getViewport({ scale: SCAN_SCALE });
        setRatio(`${String(viewport.width)} / ${String(viewport.height)}`);
        element.width = viewport.width;
        element.height = viewport.height;
        task = page.render({ canvas: element, viewport });
        return task.promise;
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      task?.cancel();
    };
  }, [pdf, number, near]);

  return (
    <div
      ref={frame}
      role="img"
      aria-label={label}
      style={{ aspectRatio: ratio }}
      className="w-full shadow-document"
    >
      {near && <canvas ref={canvas} className="block h-full w-full" />}
    </div>
  );
}

/** The page (from 1) an offset is on: the last page starting at or before it. */
function pageOf(offsets: number[], offset: number): number {
  return Math.max(offsets.filter((start) => start <= offset).length, 1);
}

/** What the reader shows of a clicked fragment: its number, location and tags (R-11 AC2). */
function FragmentDetails({ fragment }: { fragment: Fragment }) {
  return (
    <div className="mt-16 flex flex-col gap-8 rounded-sm border border-border bg-card p-16">
      <p className="text-cousine-metadane text-foreground">
        {[fragmentLabel(fragment.number), fragment.location].filter(Boolean).join(" · ")}
      </p>
      {fragment.tags.length > 0 && <TagList tags={fragment.tags} />}
    </div>
  );
}

interface ReaderBodyProps {
  document: Document;
  pdf?: PDFDocumentProxy;
  scanFailed: boolean;
  /** The fragment the URL names (`?fragment=`), or null. */
  target: number | null;
}

function ReaderBody({ document, pdf, scanFailed, target }: ReaderBodyProps) {
  const [selected, setSelected] = useState(target);
  const [view, setView] = useState<View>(target === null ? "scan" : "text");
  const textColumn = useRef<HTMLDivElement>(null);

  // R-11 AC3: opened with a fragment reference, the reader scrolls to it, and again if a scan
  // that cannot be opened leaves the text alone, at full width.
  useEffect(() => {
    if (target !== null) {
      textColumn.current
        ?.querySelector(`[data-fragments~="${String(target)}"]`)
        ?.scrollIntoView({ block: "center" });
    }
  }, [target, scanFailed]);

  const { text, page_offsets: offsets, fragments } = document;
  const pageCount = offsets.length;
  // Split once per text, not on every click: a whole typescript has hundreds of pages.
  const { pages, byId } = useMemo(() => {
    const split: Segment[][] = Array.from({ length: Math.max(offsets.length, 1) }, () => []);
    for (const segment of segments(text.length, fragments, offsets)) {
      split[pageOf(offsets, segment.start) - 1]?.push(segment);
    }
    return { pages: split, byId: new Map(fragments.map((fragment) => [fragment.id, fragment])) };
  }, [text, offsets, fragments]);
  const selectedFragment = selected === null ? undefined : byId.get(selected);
  const selectedPage =
    selectedFragment === undefined
      ? null
      : pageOf(offsets, Math.min(selectedFragment.start, text.length));
  const hasScans = pageCount > 0 && !scanFailed;

  /** Of the fragments covering a segment, the shortest: the innermost one. */
  function innermost(segment: Segment): Fragment | undefined {
    return segment.ids
      .flatMap((id) => byId.get(id) ?? [])
      .reduce<Fragment | undefined>(
        (best, fragment) =>
          best === undefined || fragment.end - fragment.start < best.end - best.start
            ? fragment
            : best,
        undefined,
      );
  }

  function selectByKey(event: KeyboardEvent, id: number | null) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setSelected(id);
    }
  }

  return (
    <div className="flex flex-col gap-16">
      {hasScans && (
        <div role="group" aria-label={copy.reader.views} className="flex gap-8 md:hidden">
          {(["scan", "text"] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={view === option}
              onClick={() => {
                setView(option);
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
      )}
      {scanFailed && (
        <p role="status" className="text-cousine-metadane text-muted-foreground">
          {copy.reader.scanError}
        </p>
      )}
      <div ref={textColumn} className="flex flex-col gap-24">
        {pages.map((pageSegments, index) => (
          <div key={index} className="grid grid-cols-1 gap-16 md:grid-cols-2">
            {hasScans && (
              <div
                className={cn(
                  "flex flex-col gap-12 rounded-md bg-media p-16",
                  view === "text" && "hidden md:flex",
                )}
              >
                <p className="text-cousine-metadane-male text-muted-foreground">
                  {copy.reader.page(index + 1, pageCount)}
                </p>
                <ScanPage
                  pdf={pdf}
                  number={index + 1}
                  label={copy.reader.page(index + 1, pageCount)}
                />
              </div>
            )}
            <div
              className={cn(
                "flex flex-col",
                hasScans ? view === "scan" && "hidden md:flex" : "md:col-span-2",
              )}
            >
              <p className="text-lora-tekst whitespace-pre-wrap text-foreground">
                {pageSegments.map((segment) => {
                  const part = text.slice(segment.start, segment.end);
                  if (segment.ids.length === 0) {
                    return part;
                  }
                  const isSelected = selected !== null && segment.ids.includes(selected);
                  const fragment = innermost(segment);
                  const id = fragment?.id ?? null;
                  return (
                    <mark
                      key={segment.start}
                      role="button"
                      tabIndex={0}
                      aria-pressed={isSelected}
                      aria-label={
                        fragment === undefined
                          ? undefined
                          : `${fragmentLabel(fragment.number)}: ${part}`
                      }
                      data-fragments={segment.ids.join(" ")}
                      onClick={() => {
                        setSelected(id);
                      }}
                      onKeyDown={(event) => {
                        selectByKey(event, id);
                      }}
                      className={cn(
                        "cursor-pointer bg-accent text-foreground",
                        isSelected && "underline decoration-accent-border decoration-2",
                        FOCUS_CLASSES,
                      )}
                    >
                      {part}
                    </mark>
                  );
                })}
              </p>
              {/* A live region, so a screen reader reads the details of a selected fragment. */}
              <div aria-live="polite">
                {selectedFragment !== undefined && selectedPage === index + 1 && (
                  <FragmentDetails fragment={selectedFragment} />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * The reader of every OCR document (R-11): on desktop each scan page next to its OCR text, on
 * mobile a "Skan" / "Transkrypcja" toggle. Fragments are highlighted; clicking one shows its
 * tags. `?fragment=<id>` scrolls to that fragment and selects it. A plain text is shown as text
 * only. The text is split as architecture §4.4 describes.
 */
export function Reader({ document }: { document: Document }) {
  const [params] = useSearchParams();
  const target = Number(params.get("fragment")) || null;
  const pdf = useQuery({
    queryKey: ["pdf", document.scan],
    queryFn: () => loadPdf(document.scan),
    enabled: document.scan !== "",
    staleTime: Infinity,
  });

  return (
    // A new fragment reference starts over: select it, show the text and scroll to it.
    <ReaderBody
      key={target ?? ""}
      document={document}
      pdf={pdf.data}
      scanFailed={pdf.isError}
      target={target}
    />
  );
}
