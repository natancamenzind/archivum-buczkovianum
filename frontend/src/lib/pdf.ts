import { useQuery } from "@tanstack/react-query";
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from "pdfjs-dist/legacy/build/pdf.mjs";
import workerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.mjs?url";
import jbig2Url from "pdfjs-dist/wasm/jbig2.wasm?url";
import openjpegUrl from "pdfjs-dist/wasm/openjpeg.wasm?url";
import qcmsUrl from "pdfjs-dist/wasm/qcms_bg.wasm?url";

export type { PDFDocumentProxy, PDFPageProxy, RenderTask };

// pdf.js's WebAssembly image decoders: JPEG 2000, JBIG2 and ICC colour. Its other WebAssembly
// module runs scripts in PDF forms, which scans do not have.
const decoderUrls: Record<string, string> = {
  "openjpeg.wasm": openjpegUrl,
  "jbig2.wasm": jbig2Url,
  "qcms_bg.wasm": qcmsUrl,
};

// Each decoder is downloaded once per page load: pdf.js opens every scan in its own worker.
const decoders = new Map<string, Promise<ArrayBuffer>>();

async function download(filename: string, url: string): Promise<ArrayBuffer> {
  const response = await fetch(new URL(url, window.location.href));
  if (!response.ok) {
    throw new Error(`Unable to load ${filename}: ${String(response.status)}`);
  }
  return response.arrayBuffer();
}

/**
 * Gives pdf.js the WebAssembly decoders it asks for by file name. OCR programs save searchable
 * PDFs with JPEG 2000 or JBIG2 page images, which pdf.js cannot draw without them. The build
 * names each file by its content, so pdf.js's one-folder `wasmUrl` option cannot point at them.
 */
export class ScanDataFactory {
  async fetch({ kind, filename }: { kind: string; filename: string }): Promise<Uint8Array> {
    const url = kind === "wasmUrl" ? decoderUrls[filename] : undefined;
    if (url === undefined) {
      throw new Error(`pdf.js asked for ${kind} ${filename}, which the site does not serve.`);
    }
    let decoder = decoders.get(filename);
    if (decoder === undefined) {
      decoder = download(filename, url);
      decoders.set(filename, decoder);
      // A failed download is tried again by the next scan.
      decoder.catch(() => decoders.delete(filename));
    }
    // A copy: pdf.js may hand the bytes over to its worker, which empties the original.
    return new Uint8Array((await decoder).slice(0));
  }
}

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
  return pdfjs.getDocument({
    url: new URL(url, window.location.href).href,
    BinaryDataFactory: ScanDataFactory,
  }).promise;
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
