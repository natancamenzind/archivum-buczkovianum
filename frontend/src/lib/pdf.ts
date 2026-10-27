import { useQuery } from "@tanstack/react-query";
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from "pdfjs-dist/legacy/build/pdf.mjs";
import workerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.mjs?url";

export type { PDFDocumentProxy, PDFPageProxy, RenderTask };

/**
 * Opens a scan with pdf.js (architecture §2). The legacy build also runs in browsers that lack
 * the newest JavaScript built-ins. pdf.js is loaded only when a page shows a scan.
 */
export async function loadPdf(url: string): Promise<PDFDocumentProxy> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  // Without Web Workers (Node, in tests) pdf.js parses on the main thread with its own loader.
  if (typeof Worker !== "undefined") {
    pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
  }
  // Scan URLs are relative to the site; outside a browser pdf.js would read them as file paths.
  return pdfjs.getDocument({ url: new URL(url, window.location.href).href }).promise;
}

/** A scan, opened once and shared by every component that shows it. No scan: `url` is "". */
export function usePdf(url: string) {
  return useQuery({
    queryKey: ["pdf", url],
    queryFn: () => loadPdf(url),
    enabled: url !== "",
    staleTime: Infinity,
  });
}
