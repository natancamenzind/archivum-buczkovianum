import { Link } from "react-router";

import { copy } from "@/copy/pl";

/** Shown for any URL that matches no page. Django serves index.html for it all the same. */
export function NotFoundPage() {
  return (
    <main className="flex flex-col gap-24 p-page-mobile md:p-page">
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
    </main>
  );
}
