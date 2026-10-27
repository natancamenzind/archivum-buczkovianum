interface SectionHeaderProps {
  title: string;
}

/**
 * "Nagłówek sekcji" in design/components/: a section title over a subtle rule. Shared by all
 * pages (architecture §8). The counter and description of R-09 are added when a page needs them.
 */
export function SectionHeader({ title }: SectionHeaderProps) {
  return (
    <div className="flex flex-col gap-8 border-b border-border pb-12">
      <h2 className="text-lora-tytul-sekcji text-foreground">{title}</h2>
    </div>
  );
}
