import type { RouteObject } from "react-router";

import { SiteLayout } from "@/components/layout/SiteLayout";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

/** One route per public page (docs/architecture.md, section 8). Django serves every one of them. */
export const routes: RouteObject[] = [
  {
    // The header, navigation and footer of every page (R-07), a missing one included.
    element: <SiteLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
