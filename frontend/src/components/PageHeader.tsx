import type { ReactNode } from "react";

import { HeroBackdrop } from "@/components/HeroBackdrop";

interface PageHeaderProps {
  /** The line above the title: the site name here, the object's type line on entity pages. */
  label: string;
  title: string;
  /** Rendered only when given; the caller leaves it out when the text is empty (R-02). */
  description?: ReactNode;
  /** The entity's header image behind the text (ARC-29). Left out when it has none. */
  image?: { src: string; alt: string };
}

const DESCRIPTION_CLASSES =
  "text-lora-glosa text-inverse-foreground md:max-w-3xl md:text-lora-wstep";

/**
 * "Nagłówek strony" in design/components/: the dark hero at the top of every subpage, with the
 * ornament, label, title and an optional description. Shared by all pages (architecture §8).
 * An entity's header image lies behind the text, as the portrait does on the home page.
 */
export function PageHeader({ label, title, description, image }: PageHeaderProps) {
  return (
    // A div, not <header>: the site header is the page's only banner landmark (R-07).
    <div
      data-slot="page-header"
      className="relative overflow-hidden bg-inverse px-page-mobile pt-32 pb-24 md:px-page md:py-48"
    >
      {image !== undefined && <HeroBackdrop src={image.src} alt={image.alt} />}
      <div className="relative flex flex-col gap-16">
        {/* The design's ornament is 40 px wide; 48 is the nearest spacing token. */}
        <div aria-hidden="true" className="h-px w-48 bg-inverse-border" />
        <p className="text-cousine-etykieta text-inverse-muted-foreground">{label}</p>
        <h1 className="text-lora-tytul-strony-mobile text-inverse-foreground md:text-lora-tytul-strony">
          {title}
        </h1>
        {/* A string is one paragraph; rich text (a node) brings its own. */}
        {typeof description === "string" ? (
          <p className={DESCRIPTION_CLASSES}>{description}</p>
        ) : (
          description !== undefined && <div className={DESCRIPTION_CLASSES}>{description}</div>
        )}
      </div>
    </div>
  );
}
