import { QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { axe } from "vitest-axe";

import { createQueryClient } from "@/lib/query-client";
import { routes } from "@/routes";

/**
 * Renders the app at `url` with the real routes and the app's query client, minus retries.
 * The router tells where a navigation went, for pages that are not built yet.
 */
export function renderRoute(
  url: string,
): RenderResult & { router: ReturnType<typeof createMemoryRouter> } {
  const queryClient = createQueryClient();
  queryClient.setDefaultOptions({
    queries: { ...queryClient.getDefaultOptions().queries, retry: false },
  });
  const router = createMemoryRouter(routes, { initialEntries: [url] });
  const result = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { ...result, router };
}

/** The accessibility violations axe finds in `container` (R-12); a test expects none. */
export async function axeViolations(container: Element): Promise<string[]> {
  // An embedded player's frame is the provider's page, which jsdom cannot load or check.
  const results = await axe(container, { iframes: false });
  return results.violations.map((violation) => `${violation.id}: ${violation.help}`);
}
