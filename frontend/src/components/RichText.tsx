import { cn } from "@/lib/utils";

interface RichTextProps {
  /** HTML of a rich text field. The server sanitizes it when an editor saves it. */
  html: string;
  /** The typography of the paragraphs, e.g. `text-lora-tekst`. */
  className?: string;
}

/**
 * A rich text field: paragraphs, bold, italic, links, lists and h3–h4 headings, the editor's
 * toolbar (architecture §5).
 */
export function RichText({ html, className }: RichTextProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-16",
        "[&_a]:underline [&_a]:underline-offset-4",
        "[&_ol]:list-decimal [&_ol]:pl-24 [&_ul]:list-disc [&_ul]:pl-24",
        "[&_h3]:text-lora-tytul-elementu [&_h4]:text-lora-tytul-elementu",
        className,
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
