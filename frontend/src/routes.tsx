import type { RouteObject } from "react-router";

import { SiteLayout } from "@/components/layout/SiteLayout";
import { AboutPage } from "@/pages/AboutPage";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { WorksPage } from "@/pages/WorksPage";

/** One route per public page (docs/architecture.md, section 8). Django serves every one of them. */
export const routes: RouteObject[] = [
  {
    // The header, navigation and footer of every page (R-07), a missing one included.
    element: <SiteLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "works", element: <WorksPage /> },
      { path: "about", element: <AboutPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
