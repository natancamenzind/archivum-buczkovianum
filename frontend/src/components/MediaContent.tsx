import type { components } from "@/api/schema";
import { DocumentReader } from "@/components/Reader";
import { ScanPage } from "@/components/ScanPage";
import { SectionHeader } from "@/components/SectionHeader";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { usePdf } from "@/lib/pdf";

type Content = components["schemas"]["MediaContent"];

const LINK_CLASSES =
  "w-fit text-cousine-metadane text-accent-foreground underline underline-offset-3 hover:text-accent-foreground-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

/** The player address of a YouTube, Vimeo, archive.org or SoundCloud link; null for any other. */
function embedUrl(link: string): string | null {
  let url: URL;
  try {
    url = new URL(link);
  } catch {
    return null;
  }
  const host = url.hostname.replace(/^(www|m)\./, "");
  let id: string | null | undefined;
  if (host === "youtube.com") {
    id =
      url.pathname === "/watch"
        ? url.searchParams.get("v")
        : /^\/(?:embed|shorts)\/([^/]+)/.exec(url.pathname)?.[1];
  } else if (host === "youtu.be") {
    id = url.pathname.slice(1);
  } else if (host === "vimeo.com") {
    const video = /^\/(\d+)$/.exec(url.pathname)?.[1];
    return video === undefined ? null : `https://player.vimeo.com/video/${video}`;
  } else if (host === "archive.org") {
    const item = /^\/(?:details|embed)\/([\w.-]+)/.exec(url.pathname)?.[1];
    return item === undefined ? null : `https://archive.org/embed/${item}`;
  } else if (host === "soundcloud.com") {
    const track = /^\/[\w-]+\/(?:sets\/)?[\w-]+\/?$/.exec(url.pathname)?.[0];
    return track === undefined
      ? null
      : `https://w.soundcloud.com/player/?visual=true&url=${encodeURIComponent(`https://soundcloud.com${track}`)}`;
  }
  return id != null && /^[\w-]+$/.test(id) ? `https://www.youtube-nocookie.com/embed/${id}` : null;
}

/** An audio or video link: the provider's player if it is a known provider, otherwise a link. */
export function ExternalMedia({ link }: { link: string }) {
  const player = embedUrl(link);
  return player === null ? (
    <a href={link} className={LINK_CLASSES}>
      {copy.content.link}
    </a>
  ) : (
    <iframe
      src={player}
      title={copy.content.player}
      allow="encrypted-media; fullscreen; picture-in-picture"
      className="aspect-video w-full rounded-md"
    />
  );
}

function isPdf(file: string): boolean {
  return new URL(file, window.location.href).pathname.toLowerCase().endsWith(".pdf");
}

function Download({ file }: { file: string }) {
  return (
    <a href={file} download className={LINK_CLASSES}>
      {copy.content.download}
    </a>
  );
}

/** A PDF drawn page by page with pdf.js; one that cannot be opened is offered as a download. */
function PdfPages({ file }: { file: string }) {
  const pdf = usePdf(file);
  if (pdf.isError) {
    return <Download file={file} />;
  }
  if (pdf.data === undefined) {
    return (
      <p className="text-cousine-metadane text-muted-foreground" role="status">
        {copy.content.loading}
      </p>
    );
  }
  const count = pdf.data.numPages;
  return (
    <ol className="flex flex-col gap-24">
      {Array.from({ length: count }, (_, index) => (
        <li key={index}>
          <ScanPage pdf={pdf.data} number={index + 1} label={copy.content.page(index + 1, count)} />
        </li>
      ))}
    </ol>
  );
}

/**
 * The content of a note or contextual material, by its kind (US-RA-11 AC3): an image inline; a
 * PDF inline, another file as a download; an audio or video link as `ExternalMedia`; a text in
 * the reader (R-11), under "Transkrypcja".
 */
export function MediaContent({ content }: { content: Content }) {
  if (content.document !== null) {
    return (
      <Card>
        <SectionHeader title={copy.content.text} />
        <DocumentReader id={content.document} />
      </Card>
    );
  }
  return (
    <Card>
      {content.kind === "image" && (
        <img src={content.image} alt={content.image_alt} className="w-full rounded-md" />
      )}
      {content.kind === "document" &&
        (isPdf(content.file) ? <PdfPages file={content.file} /> : <Download file={content.file} />)}
      {content.kind === "external_media" && <ExternalMedia link={content.external_url} />}
    </Card>
  );
}
