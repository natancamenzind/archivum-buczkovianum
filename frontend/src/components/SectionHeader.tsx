interface SectionHeaderProps {
  title: string;
  /** "Licznik": the number of items, or "shown of all" ("2 z 24"). Rendered only when given. */
  count?: string;
  /** "Opis": one line under the title, e.g. the order of the items. Rendered only when given. */
  description?: string;
}

/**
 * "Nagłówek sekcji" in design/components/: a section title over a subtle rule, with an optional
 * counter and description (plan D24). Shared by all pages (architecture §8). The preview link of
 * R-09 is added when a page needs it.
 */
export function SectionHeader({ title, count, description }: SectionHeaderProps) {
  return (
    <div className="flex flex-col gap-8 border-b border-border pb-12">
      <div className="flex items-end justify-between gap-16">
        <h2 className="text-lora-tytul-sekcji text-foreground">{title}</h2>
        {count !== undefined && (
          <p className="text-cousine-metadane text-muted-foreground">{count}</p>
        )}
      </div>
      {description !== undefined && (
        <p className="text-cousine-metadane-male text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
