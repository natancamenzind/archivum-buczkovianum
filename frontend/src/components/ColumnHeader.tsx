interface ColumnHeaderProps {
  label: string;
  /** "Liczba": the number of items under the header. Rendered only when given. */
  count?: number;
}

/**
 * "Nagłówek kolumny" in design/components/: a small uppercase label over a subtle rule, heading
 * a list inside a section or a column of an entity page, with an optional count.
 */
export function ColumnHeader({ label, count }: ColumnHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-8">
      <h3 className="text-cousine-etykieta text-foreground">{label}</h3>
      {count !== undefined && (
        <p className="text-cousine-metadane-male text-muted-foreground">{count}</p>
      )}
    </div>
  );
}
