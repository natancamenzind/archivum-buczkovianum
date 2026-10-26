/**
 * Tailwind plugin that loads design/tokens/tokens.css, the Figma export (design/README.md).
 *
 * The custom properties go into the base layer, and each `.text-*` typography style becomes a
 * Tailwind utility, so it takes variants (`md:text-lora-tytul-strony`) and sorts with the other
 * utilities. tokens.css stays the single source: nothing here repeats a token value.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import plugin from "tailwindcss/plugin";

export const TOKENS_PATH = fileURLToPath(new URL("../design/tokens/tokens.css", import.meta.url));

type Declarations = Record<string, string>;

export interface DesignTokens {
  /** Custom properties declared on `:root`. */
  properties: Declarations;
  /** Typography styles by class name, e.g. `text-lora-tekst`. */
  textStyles: Record<string, Declarations>;
}

function parseDeclarations(block: string): Declarations {
  const declarations: Declarations = {};
  for (const declaration of block.split(";")) {
    const colon = declaration.indexOf(":");
    if (colon > 0) {
      declarations[declaration.slice(0, colon).trim()] = declaration.slice(colon + 1).trim();
    }
  }
  return declarations;
}

/** Reads the flat rule blocks of tokens.css: `:root { … }` and `.text-… { … }`. */
export function parseTokens(css: string): DesignTokens {
  const source = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const properties: Declarations = {};
  const textStyles: Record<string, Declarations> = {};
  for (const [, selector = "", block = ""] of source.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const name = selector.trim();
    if (name === ":root") {
      Object.assign(properties, parseDeclarations(block));
    } else if (/^\.text-[\w-]+$/.test(name)) {
      textStyles[name.slice(1)] = parseDeclarations(block);
    }
  }
  return { properties, textStyles };
}

export default plugin((api) => {
  const tokens = parseTokens(readFileSync(TOKENS_PATH, "utf-8"));
  api.addBase({ ":root": tokens.properties });
  api.addUtilities(
    Object.fromEntries(
      Object.entries(tokens.textStyles).map(([name, declarations]) => [`.${name}`, declarations]),
    ),
  );
});
