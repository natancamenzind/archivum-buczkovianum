import createClient from "openapi-fetch";

import type { components, paths } from "@/api/schema";

/**
 * Typed client for the Django API, generated from its OpenAPI schema (`make api-client`).
 * The API is on the same origin as the page; an absolute base URL also works in tests.
 */
export const api = createClient<paths>({ baseUrl: window.location.origin });

/** A text for the reader; pages cache it under `["document", id]`. */
export async function fetchDocument(id: number): Promise<components["schemas"]["Document"]> {
  const { data, response } = await api.GET("/api/documents/{id}/", {
    params: { path: { id } },
  });
  if (data === undefined) {
    throw new Error(`The document request failed with ${String(response.status)}.`);
  }
  return data;
}
