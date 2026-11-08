// Latin and Latin Extended (Polish) only; the weights and styles used by tokens.css.
import "@fontsource/lora/latin-400.css";
import "@fontsource/lora/latin-ext-400.css";
import "@fontsource/lora/latin-400-italic.css";
import "@fontsource/lora/latin-ext-400-italic.css";
import "@fontsource/lora/latin-500.css";
import "@fontsource/lora/latin-ext-500.css";
import "@fontsource/cousine/latin-400.css";
import "@fontsource/cousine/latin-ext-400.css";
import "./index.css";

import * as Sentry from "@sentry/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import { createQueryClient } from "@/lib/query-client";
import { routes } from "@/routes";

// Errors and traces go to Sentry only when the build had VITE_SENTRY_DSN; without it the SDK
// sends nothing.
Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.VITE_SENTRY_ENVIRONMENT ?? import.meta.env.MODE,
  integrations: [Sentry.browserTracingIntegration()],
  tracesSampleRate: 0.2,
});

const root = document.getElementById("root");
if (root === null) {
  throw new Error("index.html has no #root element.");
}

createRoot(root, {
  onUncaughtError: Sentry.reactErrorHandler(),
  onCaughtError: Sentry.reactErrorHandler(),
  onRecoverableError: Sentry.reactErrorHandler(),
}).render(
  <StrictMode>
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={createBrowserRouter(routes)} />
    </QueryClientProvider>
  </StrictMode>,
);
