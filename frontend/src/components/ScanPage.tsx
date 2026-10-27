import { useEffect, useRef, useState } from "react";

import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from "@/lib/pdf";

// Pages are drawn at 1.5× their PDF size and scaled down to the column, so text stays sharp.
const SCAN_SCALE = 1.5;

// A scan page is drawn while it is within one screen of the view, so a long typescript keeps
// only a few drawn pages in memory.
const DRAW_MARGIN = "100% 0px";

/**
 * One scan page, drawn by pdf.js once the scan is open and the page nears the view, and dropped
 * when it moves away: in the reader (R-11) and as the fragment card's thumbnail (R-10). A page
 * that fails to draw stays blank.
 */
export function ScanPage({
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
    let drawn: PDFPageProxy | undefined;
    let task: RenderTask | undefined;
    const element = canvas.current;
    pdf
      .getPage(number)
      .then((page) => {
        drawn = page;
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
      // pdf.js keeps a drawn page's decoded scan until it is cleaned up, and Safari counts a
      // removed canvas against its memory limit until it is collected.
      drawn?.cleanup();
      if (element !== null) {
        element.width = 0;
        element.height = 0;
      }
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
