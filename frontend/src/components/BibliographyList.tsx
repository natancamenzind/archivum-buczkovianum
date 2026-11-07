interface BibliographyListProps {
  /** The entries' texts, in their order. */
  entries: string[];
}

/**
 * A work's bibliography as a numbered list of "Pozycja bibliografii" (design/components/): each
 * entry's number over a subtle rule, then its text (US-RA-21). The number is decorative, since
 * the entries sit in an ordered list.
 */
export function BibliographyList({ entries }: BibliographyListProps) {
  return (
    <ol>
      {entries.map((text, index) => (
        // Entries have no ID in the API, and the list never reorders.
        <li key={index} className="flex gap-12 border-b border-border py-12">
          <span aria-hidden="true" className="text-cousine-metadane-male text-muted-foreground">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-lora-tekst-maly text-foreground">{text}</span>
        </li>
      ))}
    </ol>
  );
}
