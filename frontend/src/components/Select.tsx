import type { SelectHTMLAttributes } from "react";

import { ChevronDownIcon } from "@/components/icons";
import { cn } from "@/lib/utils";

/**
 * A native select drawn with the design's chevron (design/assets/icons/rozwin.svg) instead of the
 * browser's arrow, inset from the right edge as in the design. `className` sizes the box; the
 * select fills it.
 */
export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className={cn("relative", className)}>
      <select
        {...props}
        className="w-full cursor-pointer appearance-none rounded-sm border border-accent-border bg-card py-8 pr-48 pl-12 text-cousine-metadane text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:cursor-default"
      />
      <ChevronDownIcon className="pointer-events-none absolute top-1/2 right-16 size-16 -translate-y-1/2 text-icon" />
    </div>
  );
}
