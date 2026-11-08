import { type KeyboardEvent, type PointerEvent, useEffect, useRef, useState } from "react";

import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from "@/components/icons";
import { Dialog, DialogClose, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { copy } from "@/copy/pl";
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from "@/lib/pdf";
import { cn } from "@/lib/utils";

// Each step of − and + scales the page by this factor, within these bounds.
const STEP = 1.25;
const MIN_SCALE = 0.25;
const MAX_SCALE = 4;

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
const BUTTON_CLASSES = cn(
  "flex size-32 items-center justify-center rounded-sm bg-card text-cousine-metadane text-foreground",
  FOCUS_CLASSES,
);
const PAGE_BUTTON_CLASSES = cn(
  "flex size-48 shrink-0 items-center justify-center rounded-full bg-card text-foreground disabled:invisible",
  FOCUS_CLASSES,
);

function clamp(scale: number): number {
  return Math.min(Math.max(scale, MIN_SCALE), MAX_SCALE);
}

interface ScanZoomProps {
  pdf?: PDFDocumentProxy;
  /** The page shown (from 1), or null when the zoom is closed. */
  page: number | null;
  count: number;
  onPage: (page: number) => void;
  /** Closing returns the reader to the page shown last. */
  onClose: () => void;
}

/**
 * "Powiększenie skanu": a scan page on the whole screen (ARC-57), drawn by pdf.js at the zoom
 * scale. −, + and "Dopasuj" (fit to the window) set the scale, as does Ctrl with the wheel or
 * a pinch; dragging moves the page; ← and → change the page; Esc closes.
 */
export function ScanZoom({ pdf, page, count, onPage, onClose }: ScanZoomProps) {
  // The dialog's content mounts after it opens, so its frame is state, not a ref, for the
  // effects below to run once it is there.
  const [frame, setFrame] = useState<HTMLDivElement | null>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null);
  // null fits the page to the window.
  const [scale, setScale] = useState<number | null>(null);
  const [fit, setFit] = useState(1);
  const shown = scale ?? fit;

  // A pinch on a trackpad comes as a wheel event with Ctrl held. React's wheel listener is
  // passive, so it cannot stop the browser from zooming the whole site instead.
  useEffect(() => {
    const element = frame;
    if (element === null) {
      return;
    }
    function wheel(event: WheelEvent) {
      if (event.ctrlKey) {
        event.preventDefault();
        setScale((current) => clamp((current ?? fit) * (event.deltaY < 0 ? STEP : 1 / STEP)));
      }
    }
    element.addEventListener("wheel", wheel, { passive: false });
    return () => {
      element.removeEventListener("wheel", wheel);
    };
  }, [frame, fit]);

  useEffect(() => {
    if (pdf === undefined || page === null || frame === null) {
      return;
    }
    let cancelled = false;
    let drawn: PDFPageProxy | undefined;
    let task: RenderTask | undefined;
    const element = canvas.current;
    pdf
      .getPage(page)
      .then((loaded) => {
        drawn = loaded;
        if (cancelled || element === null) {
          return;
        }
        const natural = loaded.getViewport({ scale: 1 });
        const fitted = clamp(
          Math.min(frame.clientWidth / natural.width, frame.clientHeight / natural.height),
        );
        setFit(fitted);
        const viewport = loaded.getViewport({
          scale: (scale ?? fitted) * window.devicePixelRatio,
        });
        element.width = viewport.width;
        element.height = viewport.height;
        element.style.width = `${String(natural.width * (scale ?? fitted))}px`;
        task = loaded.render({ canvas: element, viewport });
        return task.promise;
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      task?.cancel();
      drawn?.cleanup();
    };
  }, [pdf, page, scale, frame]);

  function keyDown(event: KeyboardEvent) {
    if (page === null) {
      return;
    }
    if (event.key === "ArrowLeft" && page > 1) {
      onPage(page - 1);
    } else if (event.key === "ArrowRight" && page < count) {
      onPage(page + 1);
    }
  }

  function pointerDown(event: PointerEvent<HTMLDivElement>) {
    const element = event.currentTarget;
    drag.current = {
      x: event.clientX,
      y: event.clientY,
      left: element.scrollLeft,
      top: element.scrollTop,
    };
    element.setPointerCapture(event.pointerId);
  }

  function pointerMove(event: PointerEvent<HTMLDivElement>) {
    const start = drag.current;
    if (start !== null) {
      event.currentTarget.scrollLeft = start.left - (event.clientX - start.x);
      event.currentTarget.scrollTop = start.top - (event.clientY - start.y);
    }
  }

  return (
    <Dialog
      open={page !== null}
      onOpenChange={(open) => {
        if (!open) {
          setScale(null);
          onClose();
        }
      }}
    >
      <DialogContent
        aria-describedby="scan-zoom-hint"
        onKeyDown={keyDown}
        // The reader moves the focus to the zoom button of the page shown last.
        onCloseAutoFocus={(event) => {
          event.preventDefault();
        }}
        className="bg-inverse"
      >
        <div className="flex items-center justify-between gap-16 px-24 py-16">
          <DialogTitle className="flex-1 text-cousine-metadane text-inverse-muted-foreground">
            {page === null ? "" : copy.reader.page(page, count)}
          </DialogTitle>
          <div className="flex items-center gap-8">
            <button
              type="button"
              aria-label={copy.reader.zoomOut}
              onClick={() => {
                setScale(clamp(shown / STEP));
              }}
              className={BUTTON_CLASSES}
            >
              −
            </button>
            <output aria-live="polite" className="text-cousine-metadane text-inverse-foreground">
              {copy.reader.zoomScale(Math.round(shown * 100))}
            </output>
            <button
              type="button"
              aria-label={copy.reader.zoomIn}
              onClick={() => {
                setScale(clamp(shown * STEP));
              }}
              className={BUTTON_CLASSES}
            >
              +
            </button>
            <button
              type="button"
              aria-label={copy.reader.zoomFitLabel}
              onClick={() => {
                setScale(null);
              }}
              className={cn(BUTTON_CLASSES, "w-auto px-12")}
            >
              {copy.reader.zoomFit}
            </button>
          </div>
          <div className="flex flex-1 justify-end">
            <DialogClose aria-label={copy.reader.zoomClose} className={BUTTON_CLASSES}>
              <CloseIcon className="size-16" />
            </DialogClose>
          </div>
        </div>
        <div className="flex min-h-0 flex-1 items-center gap-16 px-24">
          <button
            type="button"
            aria-label={copy.reader.previousPage}
            disabled={page === null || page <= 1}
            onClick={() => {
              if (page !== null) {
                onPage(page - 1);
              }
            }}
            className={PAGE_BUTTON_CLASSES}
          >
            <ChevronLeftIcon className="size-16" />
          </button>
          <div
            ref={setFrame}
            onPointerDown={pointerDown}
            onPointerMove={pointerMove}
            onPointerUp={() => {
              drag.current = null;
            }}
            className="grid h-full min-w-0 flex-1 cursor-grab touch-none place-items-center overflow-auto active:cursor-grabbing"
          >
            <canvas ref={canvas} className="block max-w-none" />
          </div>
          <button
            type="button"
            aria-label={copy.reader.nextPage}
            disabled={page === null || page >= count}
            onClick={() => {
              if (page !== null) {
                onPage(page + 1);
              }
            }}
            className={PAGE_BUTTON_CLASSES}
          >
            <ChevronRightIcon className="size-16" />
          </button>
        </div>
        <p
          id="scan-zoom-hint"
          className="px-24 pt-12 pb-16 text-center text-cousine-metadane-male text-inverse-muted-foreground"
        >
          {copy.reader.zoomHint}
        </p>
      </DialogContent>
    </Dialog>
  );
}
