import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// tailwind-merge must know the theme in src/index.css, or it cannot tell which classes conflict.
// The `.text-*` typography styles from tokens.css set the font size, so they share that group.
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      spacing: ["page", "page-mobile", "card", "card-mobile"],
      shadow: ["card", "raised", "document"],
      text: [
        (value: string) => /^(lora|cousine)-/.test(value),
        (value: string) => /^chmura-tagow-\d$/.test(value),
      ],
    },
  },
});

/** Joins class names, letting later Tailwind classes override conflicting earlier ones (shadcn/ui). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
