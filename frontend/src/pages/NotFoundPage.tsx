import { Link } from "react-router";

import { Hypocycloid } from "@/components/Hypocycloid";
import { copy } from "@/copy/pl";

/**
 * Shown for any URL that matches no page. Django serves index.html for it all the same.
 * The main fills the page between header and footer, with the hypocycloid behind the text (ARC-32).
 */
export function NotFoundPage() {
  return (
    <main className="relative flex-1 overflow-hidden p-page-mobile md:p-page">
      <Hypocycloid tone="page" placement="notFound" />
      <div className="relative flex flex-col gap-24">
        <h1 className="text-lora-tytul-strony-mobile md:text-lora-tytul-strony">
          {copy.notFound.title}
        </h1>
        <p className="text-lora-tekst">{copy.notFound.body}</p>
        <Link
          to="/"
          className="text-cousine-nawigacja text-accent-foreground hover:text-accent-foreground-hover"
        >
          {copy.notFound.backHome}
        </Link>
      </div>
    </main>
  );
}
