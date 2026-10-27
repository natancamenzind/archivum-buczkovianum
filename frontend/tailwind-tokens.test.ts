// @vitest-environment node
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compile } from "tailwindcss";
import { describe, expect, it } from "vitest";

import tokensPlugin, { parseTokens, TOKENS_PATH } from "./tailwind-tokens";

const INDEX_CSS = fileURLToPath(new URL("./src/index.css", import.meta.url));
const require = createRequire(import.meta.url);

/** Builds the CSS for `candidates` from src/index.css, as the Vite plugin does. */
async function buildCss(candidates: string[]): Promise<string> {
  const compiler = await compile(await readFile(INDEX_CSS, "utf-8"), {
    base: dirname(INDEX_CSS),
    loadStylesheet: async (id, base) => {
      const path =
        id === "tailwindcss" ? require.resolve("tailwindcss/index.css") : resolve(base, id);
      return { path, base: dirname(path), content: await readFile(path, "utf-8") };
    },
    loadModule: (id, base) =>
      Promise.resolve({ path: resolve(base, id), base, module: tokensPlugin }),
  });
  return compiler.build(candidates);
}

describe("parseTokens", () => {
  it("reads the custom properties and typography styles of tokens.css", async () => {
    const tokens = parseTokens(await readFile(TOKENS_PATH, "utf-8"));

    expect(tokens.properties["--color-bg-page"]).toBe("var(--primitive-krem-100)");
    expect(tokens.properties["--shadow-karta"]).toContain("rgba(29, 25, 21, 0.04)");
    expect(tokens.textStyles["text-lora-tytul-strony"]).toMatchObject({
      "font-family": "'Lora', Georgia, 'Times New Roman', serif",
      "font-size": "56px",
    });
    expect(tokens.textStyles["text-cousine-etykieta"]).toMatchObject({
      "text-transform": "uppercase",
    });
  });

  it("ignores comments and other rules", () => {
    const tokens = parseTokens(
      "/* .text-x { color: red } */ .card { color: red } :root { --a: 1px; }",
    );

    expect(tokens).toEqual({ properties: { "--a": "1px" }, textStyles: {} });
  });
});

describe("the Tailwind theme", () => {
  it("gives typography styles responsive variants", async () => {
    const css = await buildCss(["md:text-lora-tytul-strony"]);

    expect(css).toMatch(
      /@media \(width >= 48rem\) \{\s*\.md\\:text-lora-tytul-strony \{[^}]*font-size: 56px/,
    );
  });

  it("puts typography styles in the utilities layer, so utilities can override them", async () => {
    const css = await buildCss(["text-lora-tekst"]);
    const utilities = css.slice(css.indexOf("@layer utilities"));

    expect(utilities).toContain(".text-lora-tekst {");
    expect(css).not.toMatch(/^\.text-lora-tekst/m);
  });

  it("has colour utilities for every kind of colour, including the shadcn/ui names", async () => {
    const css = await buildCss([
      "bg-primary",
      "text-primary-foreground",
      "border-input",
      "focus-visible:ring-ring",
      "outline-ring",
      "fill-icon",
      "stroke-accent-icon",
    ]);

    expect(css).toContain("background-color: var(--color-bg-accent)");
    expect(css).toContain("color: var(--color-text-inverse)");
    expect(css).toContain("border-color: var(--color-border-subtle)");
    expect(css).toContain("--tw-ring-color: var(--color-border-accent)");
    expect(css).toContain("outline-color: var(--color-border-accent)");
    expect(css).toContain("fill: var(--color-icon-primary)");
    expect(css).toContain("stroke: var(--color-icon-accent)");
  });

  it("has no utilities for values that are not tokens", async () => {
    const css = await buildCss(["bg-red-500", "p-5", "text-sm", "shadow-md", "rounded-xl"]);

    expect(css).not.toMatch(/\.(bg-red-500|p-5|text-sm|shadow-md|rounded-xl)/);
  });

  it("maps spacing, radius and shadow utilities to tokens", async () => {
    const css = await buildCss(["p-16", "px-page", "rounded-md", "shadow-card"]);

    expect(css).toContain("padding: var(--space-16)");
    expect(css).toContain("padding-inline: var(--layout-page-margin)");
    expect(css).toContain("border-radius: var(--radius-m)");
    expect(css).toContain("var(--shadow-karta)");
  });
});
