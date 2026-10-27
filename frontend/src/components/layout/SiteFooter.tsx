import { MainNav } from "@/components/layout/MainNav";
import { copy } from "@/copy/pl";

/**
 * "Stopka" in design/components/: service name and subtitle, main navigation, funding note
 * (R-07). The funding note takes the place of Figma's language switch, which is out of scope
 * for v1. On mobile the navigation is a fixed bottom bar, so the footer leaves room for it.
 */
export function SiteFooter() {
  return (
    <footer className="flex flex-col gap-12 border-t border-border bg-background px-page-mobile pt-24 pb-64 md:flex-row md:items-stretch md:justify-between md:gap-32 md:px-page md:pt-0 md:pb-0">
      <div className="flex flex-col gap-4 md:self-center">
        <p className="text-cousine-etykieta text-foreground">{copy.siteName}</p>
        <p className="text-cousine-metadane-male text-muted-foreground">
          {copy.layout.footerSubtitle}
        </p>
      </div>
      <MainNav />
      <p className="pb-24 text-cousine-metadane text-muted-foreground md:self-center md:pb-0">
        {copy.layout.fundingNote}
      </p>
    </footer>
  );
}
