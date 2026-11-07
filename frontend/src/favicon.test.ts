import { describe, expect, it } from "vitest";

import indexHtml from "../index.html?raw";
import faviconSvg from "./assets/favicon.svg?raw";

function parse(source: string, type: DOMParserSupportedType): Document {
  return new DOMParser().parseFromString(source, type);
}

describe("favicon (ARC-38)", () => {
  it("test_arc_38_index_links_the_hypocycloid_favicon", () => {
    const index = parse(indexHtml, "text/html");
    const icon = index.querySelector('link[rel="icon"]');

    expect(icon?.getAttribute("type")).toBe("image/svg+xml");
    expect(icon?.getAttribute("href")).toBe("/src/assets/favicon.svg");
  });

  it("test_arc_38_favicon_is_a_well_formed_svg_with_the_curve_and_its_circle", () => {
    const svg = parse(faviconSvg, "image/svg+xml");

    expect(svg.querySelector("parsererror")).toBeNull();
    expect(svg.documentElement.getAttribute("viewBox")).toBe("0 0 32 32");
    expect(svg.querySelector("circle")).not.toBeNull();
    expect(svg.querySelector("path")?.getAttribute("d")).toMatch(/^M[\d. L]+Z$/);
  });

  it("test_arc_38_favicon_switches_colour_with_the_browser_colour_scheme", () => {
    const svg = parse(faviconSvg, "image/svg+xml");

    expect(svg.querySelector("style")?.textContent).toContain("prefers-color-scheme: dark");
  });
});
