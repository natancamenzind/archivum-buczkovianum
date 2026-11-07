import type { RouteObject } from "react-router";

import { SiteLayout } from "@/components/layout/SiteLayout";
import { AboutPage } from "@/pages/AboutPage";
import { BibliographyPage } from "@/pages/BibliographyPage";
import { HomePage } from "@/pages/HomePage";
import { MaterialPage } from "@/pages/MaterialPage";
import { NotePage } from "@/pages/NotePage";
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
      { path: "utwory", element: <WorksPage /> },
      { path: "maszynopisy", element: <TypescriptsPage /> },
      { path: "tagi", element: <TagsPage /> },
      { path: "utwory/:slug", element: <WorkPage /> },
      { path: "utwory/:slug/bibliografia", element: <BibliographyPage /> },
      { path: "tagi/:slug", element: <TagPage /> },
      { path: "maszynopisy/:id", element: <TypescriptPage /> },
      { path: "zapiski/:id", element: <NotePage /> },
      { path: "materialy/:id", element: <MaterialPage /> },
      { path: "teksty-sekundarne/:id", element: <SecondaryTextPage /> },
      { path: "o-archiwum", element: <AboutPage /> },
      { path: "szukaj", element: <SearchPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
