import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach } from "vitest";

import { installIntersectionObserver } from "./intersection";
import { installMatchMedia, setViewport } from "./media";
import { server } from "./server";

installIntersectionObserver();
// Tests of build tooling run in Node, without a window.
if (typeof window !== "undefined") {
  installMatchMedia();
}

// Listen before test files are imported, so the API client's fetch goes through MSW.
// An unmocked request fails the test instead of reaching a real server.
server.listen({ onUnhandledFrame: "error" });

afterEach(() => {
  cleanup();
  server.resetHandlers();
  setViewport("desktop");
  if (typeof window !== "undefined") {
    window.localStorage.clear();
  }
});

afterAll(() => {
  server.close();
});
