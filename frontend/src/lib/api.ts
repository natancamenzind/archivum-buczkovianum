import createClient from "openapi-fetch";

import type { paths } from "@/api/schema";

/**
 * Typed client for the Django API, generated from its OpenAPI schema (`make api-client`).
 * The API is on the same origin as the page; an absolute base URL also works in tests.
 */
export const api = createClient<paths>({ baseUrl: window.location.origin });
