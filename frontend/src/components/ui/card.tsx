import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

/**
 * shadcn/ui Card on the design's tokens: the panel of design/components/ ("O projekcie",
 * "Zespół"), with the card background, subtle border, medium radius and Cień/karta.
 * Only `Card` is kept, because the design's panels have no separate header or footer slots.
 */
function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      data-slot="card"
      className={cn(
        "flex flex-col gap-24 rounded-md border border-border bg-card p-card-mobile text-card-foreground shadow-card md:p-card",
        className,
      )}
      {...props}
    />
  );
}

export { Card };
