import { useQuery } from "@tanstack/react-query";

import { copy } from "@/copy/pl";
import { api } from "@/lib/api";

interface ApiInfo {
  title: string;
  version: string;
}

function readApiInfo(schema: Record<string, unknown> | undefined): ApiInfo {
  const info = schema?.info;
  if (typeof info === "object" && info !== null && "title" in info && "version" in info) {
    return { title: String(info.title), version: String(info.version) };
  }
  throw new Error("The API schema has no info block.");
}

async function fetchApiInfo(): Promise<ApiInfo> {
  const { data, response } = await api.GET("/api/schema/", {
    params: { query: { format: "json" } },
  });
  if (!response.ok) {
    throw new Error(`The API schema request failed with ${String(response.status)}.`);
  }
  return readApiInfo(data);
}

/**
 * Placeholder home page (docs/plan.md, step 1). It proves the chain from React Router through
 * TanStack Query and the generated client to Django. US-RA-01 replaces it.
 */
export function HomePage() {
  const apiInfo = useQuery({ queryKey: ["api-info"], queryFn: fetchApiInfo });

  return (
    <main className="flex flex-col gap-24 p-page-mobile md:p-page">
      <h1 className="text-lora-tytul-strony">{copy.siteName}</h1>
      <p className="text-lora-wstep text-secondary">{copy.home.lead}</p>
      <p className="text-cousine-metadane text-secondary" role="status">
        {apiInfo.isPending && copy.home.apiLoading}
        {apiInfo.isSuccess && copy.home.apiReady(apiInfo.data.title, apiInfo.data.version)}
        {apiInfo.isError && copy.home.apiError}
      </p>
    </main>
  );
}
