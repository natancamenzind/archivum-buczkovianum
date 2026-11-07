import type { MouseEventHandler } from "react";
import { Link } from "react-router";

import { ArrowRightIcon } from "@/components/icons";

interface ArrowLinkProps {
  /** Names the target and its count, e.g. "Wszystkie fragmenty (24)" (R-09). */
  label: string;
  to: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  /** Set as a section title, always underlined, with the arrow on the underline (ARC-31). */
  prominent?: boolean;
}

/**
 * "Link ze strzałką" in design/components/: the only "more" link, ending a preview (R-09). On
 * hover and keyboard focus it is underlined and the arrow moves 4 px away.
 */
export function ArrowLink({ label, to, onClick, prominent = false }: ArrowLinkProps) {
  if (prominent) {
    return (
      <Link
        to={to}
        onClick={onClick}
        preventScrollReset
        className="group flex w-fit items-end gap-12 text-lora-tytul-sekcji text-foreground hover:text-accent-foreground-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      >
        <span className="border-b-2 border-current pb-4">{label}</span>
        <ArrowRightIcon className="size-24 translate-y-1/2 transition-transform duration-150 ease-out group-hover:translate-x-4 group-focus-visible:translate-x-4 motion-reduce:transition-none" />
      </Link>
    );
  }
  return (
    <Link
      to={to}
      onClick={onClick}
      preventScrollReset
      className="group flex w-fit items-center gap-4 text-cousine-metadane text-accent-foreground underline-offset-3 hover:text-accent-foreground-hover hover:underline focus-visible:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      {label}
      <ArrowRightIcon className="size-16 transition-transform duration-150 ease-out group-hover:translate-x-4 group-focus-visible:translate-x-4 motion-reduce:transition-none" />
    </Link>
  );
}
