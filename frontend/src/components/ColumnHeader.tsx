interface ColumnHeaderProps {
  label: string;
}

/**
 * "Nagłówek kolumny" in design/components/: a small uppercase label over a subtle rule, heading
 * a list inside a section. The design's count ("Pokaż liczbę") is added when a page needs it.
 */
export function ColumnHeader({ label }: ColumnHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-8">
      <h3 className="text-cousine-etykieta text-foreground">{label}</h3>
    </div>
  );
}
