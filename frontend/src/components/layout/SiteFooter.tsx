import { copy } from "@/copy/pl";

/**
 * "Stopka" in design/components/: service name and subtitle, funding note (R-07). The funding
 * note takes the place of Figma's language switch, which is out of scope for v1. The main
 * navigation is in the header.
 */
export function SiteFooter() {
  return (
    <footer className="flex flex-col gap-12 border-t border-border bg-background px-page-mobile py-24 md:flex-row md:items-center md:justify-between md:gap-32 md:px-page">
      <div className="flex flex-col gap-4">
        <p className="text-cousine-etykieta text-foreground">{copy.siteName}</p>
        <p className="text-cousine-metadane-male text-muted-foreground">
          {copy.layout.footerSubtitle}
        </p>
      </div>
      <p className="text-cousine-metadane text-muted-foreground md:text-right">
        {copy.layout.fundingNote}
      </p>
    </footer>
  );
}
