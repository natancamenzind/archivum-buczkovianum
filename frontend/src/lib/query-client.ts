import { QueryClient } from "@tanstack/react-query";

/** The archive changes rarely, so data stays fresh for a while and failed requests retry once. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 5 * 60 * 1000, retry: 1 },
    },
  });
}
