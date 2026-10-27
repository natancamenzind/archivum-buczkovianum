interface ColumnHeaderProps {
  label: string;
  /** "Liczba": the number of items under the header. Rendered only when given. */
  count?: number;
  /** The heading level: 2 when no h2 section precedes the column, so heading levels do not skip. */
  level?: 2 | 3;
}

/**
 * "Nagłówek kolumny" in design/components/: a small uppercase label over a subtle rule, heading
 * a list inside a section or a column of an entity page, with an optional count.
 */
export function ColumnHeader({ label, count, level = 3 }: ColumnHeaderProps) {
  const Heading = level === 2 ? "h2" : "h3";
  return (
    <div className="flex items-center justify-between border-b border-border pb-8">
      <Heading className="text-cousine-etykieta text-foreground">{label}</Heading>
      {count !== undefined && (
        <p className="text-cousine-metadane-male text-muted-foreground">{count}</p>
      )}
    </div>
  );
}
