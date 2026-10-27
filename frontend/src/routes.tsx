import type { RouteObject } from "react-router";

import { SiteLayout } from "@/components/layout/SiteLayout";
import { AboutPage } from "@/pages/AboutPage";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { SearchPage } from "@/pages/SearchPage";
import { SecondaryTextPage } from "@/pages/SecondaryTextPage";
import { TagPage } from "@/pages/TagPage";
import { TagsPage } from "@/pages/TagsPage";
import { TypescriptPage } from "@/pages/TypescriptPage";
import { TypescriptsPage } from "@/pages/TypescriptsPage";
import { WorkPage } from "@/pages/WorkPage";
import { WorksPage } from "@/pages/WorksPage";

/** One route per public page (docs/architecture.md, section 8). Django serves every one of them. */
export const routes: RouteObject[] = [
  {
    // The header, navigation and footer of every page (R-07), a missing one included.
    element: <SiteLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "works", element: <WorksPage /> },
      { path: "typescripts", element: <TypescriptsPage /> },
      { path: "tags", element: <TagsPage /> },
      { path: "works/:slug", element: <WorkPage /> },
      { path: "tags/:slug", element: <TagPage /> },
      { path: "typescripts/:id", element: <TypescriptPage /> },
      { path: "secondary-texts/:id", element: <SecondaryTextPage /> },
      { path: "about", element: <AboutPage /> },
      { path: "search", element: <SearchPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
