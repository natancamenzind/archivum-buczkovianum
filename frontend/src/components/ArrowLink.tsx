import type { MouseEventHandler } from "react";
import { Link } from "react-router";

import { ArrowRightIcon } from "@/components/icons";

interface ArrowLinkProps {
  /** Names the target and its count, e.g. "Wszystkie fragmenty (24)" (R-09). */
  label: string;
  to: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
}

/**
 * "Link ze strzałką" in design/components/: the only "more" link, ending a preview (R-09). On
 * hover and keyboard focus it is underlined and the arrow moves 4 px away.
 */
export function ArrowLink({ label, to, onClick }: ArrowLinkProps) {
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
