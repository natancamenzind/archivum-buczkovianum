import type { ComponentType, SVGProps } from "react";
import { NavLink } from "react-router";

import { HomeIcon, LibraryIcon, TagIcon, TypescriptIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

/**
 * The items of R-07. A link is active on its list and on every page under it (/works and
 * /works/:slug → Utwory); the home link only on `/`. Other pages have no active item.
 */
const NAV_ITEMS: NavItem[] = [
  { to: "/", label: copy.layout.nav.home, Icon: HomeIcon },
  { to: "/works", label: copy.layout.nav.works, Icon: LibraryIcon },
  { to: "/typescripts", label: copy.layout.nav.typescripts, Icon: TypescriptIcon },
  { to: "/tags", label: copy.layout.nav.tags, Icon: TagIcon },
];

/**
 * Main navigation ("Pozycja nawigacji" in design/components/). One element for both layouts:
 * a bar fixed to the bottom of the viewport on mobile (vertical items), part of the footer row
 * from `md` up (horizontal items). NavLink sets aria-current="page" on the active item.
 */
export function MainNav() {
  return (
    <nav
      aria-label={copy.layout.navLabel}
      className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-background md:static md:border-t-0 md:bg-transparent"
    >
      {NAV_ITEMS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            cn(
              "group flex h-64 flex-1 flex-col items-center justify-center gap-4 border-t-2 text-center border-transparent px-4 py-8",
              "text-cousine-metadane-male text-muted-foreground transition-colors duration-150 ease-out motion-reduce:transition-none",
              "hover:text-accent-foreground focus-visible:text-accent-foreground",
              "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring",
              "md:h-auto md:flex-none md:flex-row md:gap-8 md:px-16 md:py-32 md:text-cousine-nawigacja",
              isActive && "border-accent-border text-accent-foreground",
            )
          }
        >
          <Icon className="size-16 text-icon group-aria-[current=page]:text-accent-icon" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
