import type { ComponentType } from "react";
import { Link } from "react-router";

import type { components } from "@/api/schema";
import { ArrowLink } from "@/components/ArrowLink";
import {
  ArrowUpRightIcon,
  BookIcon,
  ImageIcon,
  LibraryIcon,
  NoteIcon,
  TypescriptIcon,
} from "@/components/icons";
import { copy, formatCount, nouns } from "@/copy/pl";

type WorkResultData = components["schemas"]["WorkResult"];
type TagResultData = components["schemas"]["TagResult"];
type ItemResultData = components["schemas"]["ItemResult"];
type IconComponent = ComponentType<{ className?: string }>;
export type ItemGroup = "notes" | "typescripts" | "secondary_texts" | "materials";

const ICONS: Record<ItemGroup, IconComponent> = {
  notes: NoteIcon,
  typescripts: TypescriptIcon,
  secondary_texts: LibraryIcon,
  materials: ImageIcon,
};

/** A snippet from the API: escaped text with the search terms in `<mark>` (US-RA-15 AC6). */
function Snippet({ html }: { html: string }) {
  return (
    <span
      className="block text-lora-tekst-maly text-muted-foreground [&_mark]:bg-accent [&_mark]:text-foreground"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

interface ResultRowProps {
  icon: IconComponent;
  title: string;
  /** The type (R-04) and what identifies the result, under the title. */
  meta: string;
  to: string;
  /** "Dopasowanie": what matched, next to the arrow. */
  match?: string;
  snippet?: string;
}

/**
 * "Wynik wyszukiwania / Utwór" and "/ Zapisek" in design/components/: the type icon, title and
 * metadata, the match and an arrow. The whole row links to the result.
 */
function ResultRow({ icon: Icon, title, meta, to, match, snippet }: ResultRowProps) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-16 border-b border-border py-16 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <span className="shrink-0 rounded-sm bg-muted p-12">
        <Icon className="size-16 text-icon" />
      </span>
      <span className="flex grow flex-col gap-4">
        <span className="text-lora-tytul-elementu text-foreground group-hover:text-accent-foreground">
          {title}
        </span>
        <span className="text-cousine-metadane-male text-muted-foreground">{meta}</span>
        {snippet !== undefined && snippet !== "" && <Snippet html={snippet} />}
      </span>
      <span className="flex shrink-0 items-center gap-8 text-cousine-metadane-male text-accent-foreground">
        {match}
        <ArrowUpRightIcon className="size-16 text-accent-icon" />
      </span>
    </Link>
  );
}

/** A work: author, genre, year and how many of its fragments match; no snippet (AC5, AC6). */
export function WorkResult({ work }: { work: WorkResultData }) {
  return (
    <ResultRow
      icon={BookIcon}
      title={work.title}
      meta={[copy.searchResults.types.works, copy.author, work.genre, work.year?.toString()]
        .filter(Boolean)
        .join(" · ")}
      to={work.url}
      match={formatCount(work.fragments, nouns.fragment)}
    />
  );
}

/** A note, typescript, secondary text or contextual material, with its snippet. */
export function ItemResult({ item, group }: { item: ItemResultData; group: ItemGroup }) {
  return (
    <ResultRow
      icon={ICONS[group]}
      title={item.title}
      meta={[copy.searchResults.types[group], item.shelfmark].filter(Boolean).join(" · ")}
      to={item.url}
      snippet={item.snippet}
    />
  );
}

/**
 * "Wynik wyszukiwania / Tag" in design/components/: the name, the snippet of its description,
 * the occurrences and a link to the tag.
 */
export function TagResult({ tag }: { tag: TagResultData }) {
  return (
    <article className="flex flex-col gap-8 border-b border-border py-16">
      <p className="text-cousine-etykieta text-muted-foreground">{copy.searchResults.types.tags}</p>
      <h3 className="text-lora-tytul-elementu text-accent-foreground">{tag.title}</h3>
      {tag.snippet !== "" && <Snippet html={tag.snippet} />}
      <div className="flex items-center gap-16">
        <p className="text-cousine-metadane-male text-muted-foreground">
          {formatCount(tag.occurrences, nouns.occurrence)}
        </p>
        <ArrowLink label={copy.searchResults.openTag} to={tag.url} />
      </div>
    </article>
  );
}
