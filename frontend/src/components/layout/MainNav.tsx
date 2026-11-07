import type { ComponentType, SVGProps } from "react";
import { NavLink } from "react-router";

import { LibraryIcon, TagIcon, TypescriptIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

/**
 * The items of R-07. A link is active on its list and on every page under it (/utwory and
 * /utwory/:slug → Utwory). Other pages have no active item; the service name leads home.
 */
const NAV_ITEMS: NavItem[] = [
  { to: "/utwory", label: copy.layout.nav.works, Icon: LibraryIcon },
  { to: "/maszynopisy", label: copy.layout.nav.typescripts, Icon: TypescriptIcon },
  { to: "/tagi", label: copy.layout.nav.tags, Icon: TagIcon },
];

/**
 * Main navigation ("Pozycja nawigacji" in design/components/). One element for both layouts:
 * a bar fixed to the bottom of the viewport below `lg` (vertical items, active one overlined),
 * part of the sticky header row from `lg` up (horizontal items, full header height, active one
 * underlined). Between `lg` and `xl` the items drop their icons to fit the row.
 * NavLink sets aria-current="page" on the active item.
 */
export function MainNav() {
  return (
    <nav
      aria-label={copy.layout.navLabel}
      className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-background lg:static lg:border-t-0 lg:bg-transparent"
    >
      {NAV_ITEMS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              "group flex h-64 flex-1 flex-col items-center justify-center gap-4 border-t-2 text-center border-transparent px-4 py-8",
              "text-cousine-metadane-male text-muted-foreground transition-colors duration-150 ease-out motion-reduce:transition-none",
              "hover:text-accent-foreground focus-visible:text-accent-foreground",
              "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring",
              "lg:h-auto lg:flex-none lg:flex-row lg:gap-8 lg:border-t-0 lg:border-b-2 lg:px-16 lg:py-0 lg:text-cousine-nawigacja",
              isActive && "border-accent-border text-accent-foreground",
            )
          }
        >
          <Icon className="size-16 text-icon group-aria-[current=page]:text-accent-icon lg:hidden xl:block" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
