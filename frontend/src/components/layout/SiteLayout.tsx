import { Outlet } from "react-router";

import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteHeader } from "@/components/layout/SiteHeader";

/**
 * The page shell of every route (R-07). Each page renders its own `<main>`. Below `lg` the main
 * navigation is a bar fixed to the bottom of the viewport, so the shell leaves room for it.
 */
export function SiteLayout() {
  return (
    <div className="flex min-h-svh flex-col pb-64 lg:pb-0">
      <SiteHeader />
      <div className="flex flex-1 flex-col">
        <Outlet />
      </div>
      <SiteFooter />
    </div>
  );
}
