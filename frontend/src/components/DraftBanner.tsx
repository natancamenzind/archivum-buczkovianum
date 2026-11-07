import { copy } from "@/copy/pl";

/** Above a page that staff preview as a draft (US-WR-13 AC2). */
export function DraftBanner() {
  return (
    <p className="border-b border-accent-border bg-accent px-page-mobile py-8 text-cousine-etykieta text-accent-foreground lg:px-page">
      {copy.draftBanner}
    </p>
  );
}
