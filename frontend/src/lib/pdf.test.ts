import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/test/server";

// A fresh module per test: the decoders it downloads are kept for the page's lifetime.
async function factory() {
  const { ScanDataFactory } = await import("./pdf");
  return new ScanDataFactory();
}

function serveDecoder(filename: string, bytes: number[]) {
  const requests = { count: 0 };
  server.use(
    http.get(`*/${filename}`, () => {
      requests.count += 1;
      return HttpResponse.arrayBuffer(new Uint8Array(bytes).buffer);
    }),
  );
  return requests;
}

describe("ScanDataFactory", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("serves pdf.js the JPEG 2000 decoder that searchable PDF scans need (ARC-19)", async () => {
    serveDecoder("openjpeg.wasm", [0, 97, 115, 109]);

    const decoder = await (await factory()).fetch({ kind: "wasmUrl", filename: "openjpeg.wasm" });

    expect([...decoder]).toEqual([0, 97, 115, 109]);
  });

  it("serves the JBIG2 decoder too", async () => {
    serveDecoder("jbig2.wasm", [1]);

    const decoder = await (await factory()).fetch({ kind: "wasmUrl", filename: "jbig2.wasm" });

    expect([...decoder]).toEqual([1]);
  });

  it("downloads a decoder once for every scan on the page", async () => {
    const requests = serveDecoder("openjpeg.wasm", [7]);
    const scans = [await factory(), await factory()];

    const decoders = await Promise.all(
      scans.map((scan) => scan.fetch({ kind: "wasmUrl", filename: "openjpeg.wasm" })),
    );

    expect(decoders.map((decoder) => [...decoder])).toEqual([[7], [7]]);
    expect(requests.count).toBe(1);
  });

  it("fails for a file the site does not serve, as pdf.js does without one", async () => {
    const scan = await factory();

    await expect(scan.fetch({ kind: "cMapUrl", filename: "Identity-H.bcmap" })).rejects.toThrow(
      "does not serve",
    );
    await expect(scan.fetch({ kind: "wasmUrl", filename: "missing.wasm" })).rejects.toThrow(
      "does not serve",
    );
  });

  it("fails when a decoder cannot be downloaded, and tries again for the next scan", async () => {
    serveDecoder("openjpeg.wasm", [3]);
    // Handlers added later come first: the first download fails.
    server.use(
      http.get("*/openjpeg.wasm", () => new HttpResponse(null, { status: 404 }), { once: true }),
    );
    const scan = await factory();

    await expect(scan.fetch({ kind: "wasmUrl", filename: "openjpeg.wasm" })).rejects.toThrow("404");
    const decoder = await scan.fetch({ kind: "wasmUrl", filename: "openjpeg.wasm" });

    expect([...decoder]).toEqual([3]);
  });
});
