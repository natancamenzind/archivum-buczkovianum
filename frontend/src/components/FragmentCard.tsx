import type { ReactNode } from "react";
import { Link } from "react-router";

import type { components } from "@/api/schema";
import { NoteIcon } from "@/components/icons";
import { RichText } from "@/components/RichText";
import { ScanPage } from "@/components/ScanPage";
import { TagList } from "@/components/TagList";
import { copy, fragmentLabel } from "@/copy/pl";
import { usePdf } from "@/lib/pdf";

type Fragment = components["schemas"]["FragmentCard"];
type Note = components["schemas"]["NoteCard"];
type Tag = components["schemas"]["TagChip"];

interface EntryCardProps {
  /** Names the card's link. */
  location: string;
  type: string;
  to: string;
  /** The quote, the scan thumbnail or the image, between the location and the shelfmark. */
  children: ReactNode;
  shelfmark: string;
  description?: ReactNode;
  tags: Tag[];
}

/**
 * The layout of "Fragment / Maszynopis" and "Fragment / Zapisek" in design/components/. The
 * location line's link covers the whole card; links in the description and the tags sit above
 * it and keep their own targets.
 */
function EntryCard({ location, type, to, children, shelfmark, description, tags }: EntryCardProps) {
  return (
    <article className="relative flex flex-col gap-12 border-b border-border pb-24">
      <div className="flex items-center justify-between gap-12">
        <Link
          to={to}
          className="text-cousine-metadane-male text-muted-foreground after:absolute after:inset-0 hover:text-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          {location}
        </Link>
        <span className="shrink-0 text-cousine-etykieta text-accent-foreground">{type}</span>
      </div>
      {children}
      {shelfmark !== "" && <p className="text-lora-tytul-elementu text-foreground">{shelfmark}</p>}
      {description !== undefined && (
        <div data-slot="card-description" className="[&_a]:relative">
          {description}
        </div>
      )}
      {tags.length > 0 && (
        <div className="relative">
          <TagList tags={tags} />
        </div>
      )}
    </article>
  );
}

/** "Skan": the board holding a card's scan page, image or placeholder. */
function MediaFrame({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-sm bg-media p-12">
      <div className="flex aspect-4/1 items-center justify-center overflow-hidden">{children}</div>
    </div>
  );
}

/** The scan page the fragment starts on, drawn by pdf.js; nothing if the scan cannot open. */
function Thumbnail({ scan, page }: { scan: string; page: number }) {
  const pdf = usePdf(scan);
  if (pdf.isError) {
    return null;
  }
  return (
    <MediaFrame>
      {/* The top of the page, at the frame's width. */}
      <div className="w-full self-start">
        <ScanPage pdf={pdf.data} number={page} label={copy.card.scan(page)} />
      </div>
    </MediaFrame>
  );
}

/**
 * The fragment card (R-10): location line with the source type, the quote, the scan page it
 * starts on for an OCR source, then shelfmark, description and tags. It opens the source,
 * scrolled to the fragment.
 */
export function FragmentCard({ fragment }: { fragment: Fragment }) {
  const location = [fragment.work, fragmentLabel(fragment.number), fragment.location]
    .filter(Boolean)
    .join(" · ");
  return (
    <EntryCard
      location={location}
      type={copy.card.types[fragment.source_type]}
      to={fragment.url}
      shelfmark={fragment.shelfmark}
      description={
        fragment.description === "" ? undefined : (
          <p className="text-lora-glosa text-muted-foreground">{fragment.description}</p>
        )
      }
      tags={fragment.tags}
    >
      <blockquote className="line-clamp-4 text-lora-tekst text-foreground">
        {fragment.quote}
      </blockquote>
      {fragment.scan !== "" && fragment.start_page !== null && (
        <Thumbnail scan={fragment.scan} page={fragment.start_page} />
      )}
    </EntryCard>
  );
}

/**
 * The note card (US-RA-04 AC3): title and type, the image or the placeholder board, then
 * shelfmark, description and tags. It opens the note's page.
 */
export function NoteCard({ note }: { note: Note }) {
  return (
    <EntryCard
      location={note.title}
      type={copy.card.types.note}
      to={note.url}
      shelfmark={note.shelfmark}
      description={
        note.description === "" ? undefined : (
          <RichText html={note.description} className="text-lora-glosa text-muted-foreground" />
        )
      }
      tags={note.tags}
    >
      <MediaFrame>
        {note.image === "" ? (
          <div aria-hidden="true" className="flex flex-col items-center gap-8">
            <NoteIcon className="size-16 text-icon" />
            <p className="text-cousine-metadane-male text-muted-foreground">
              {copy.card.notePlaceholder}
            </p>
          </div>
        ) : (
          <img src={note.image} alt={note.image_alt} className="size-full object-cover" />
        )}
      </MediaFrame>
    </EntryCard>
  );
}
