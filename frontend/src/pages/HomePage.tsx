import { copy } from "@/copy/pl";

/** Placeholder home page (docs/plan.md, D21). US-RA-01 replaces it in step 17. */
export function HomePage() {
  return (
    <main className="flex flex-col gap-24 p-page-mobile md:p-page">
      <h1 className="text-lora-tytul-strony-mobile md:text-lora-tytul-strony">{copy.siteName}</h1>
      <p className="text-lora-wstep text-muted-foreground">{copy.home.lead}</p>
    </main>
  );
}
