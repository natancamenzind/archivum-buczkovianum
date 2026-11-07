/**
 * An image behind a hero's text, darkened towards the text on the left: the home hero's portrait
 * and an entity's header image (ARC-29). The hero is `relative` and its text sits above this.
 */
export function HeroBackdrop({ src, alt }: { src: string; alt: string }) {
  return (
    <>
      <img src={src} alt={alt} className="absolute inset-0 size-full object-cover" />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-linear-to-r from-inverse/94 via-inverse/72 to-inverse/20"
      />
    </>
  );
}
