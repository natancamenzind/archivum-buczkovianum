import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";

import type { components } from "@/api/schema";
import { EntityLayout } from "@/components/EntityLayout";
import { MediaContent } from "@/components/MediaContent";
import { PageHeader } from "@/components/PageHeader";
import { RelatedFragments, RelatedTags, RelatedWorks } from "@/components/Related";
import { RichText } from "@/components/RichText";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";
import { NotFoundPage } from "@/pages/NotFoundPage";

type MaterialData = components["schemas"]["MaterialPage"];

class NotFound extends Error {}

async function fetchMaterial(id: number): Promise<MaterialData> {
  const { data, response } = await api.GET("/api/materials/{id}/", {
    params: { path: { id } },
  });
  if (response.status === 404) {
    throw new NotFound();
  }
  if (data === undefined) {
    throw new Error(`The material request failed with ${String(response.status)}.`);
  }
  return data;
}

/**
 * The contextual material page (US-RA-12) in the secondary text page's layout (R-05): the
 * related works in the context column; the content by its kind and the related fragments in the
 * main column; the tags of the material, its fragments and its work links. Empty blocks are not
 * rendered (R-02).
 */
export function MaterialPage() {
  const id = Number(useParams().id);
  const page = useQuery({
    queryKey: ["material", id],
    queryFn: () => fetchMaterial(id),
    enabled: !Number.isNaN(id),
  });
  const material = page.data;

  if (page.error instanceof NotFound || Number.isNaN(id)) {
    return <NotFoundPage />;
  }
  if (material === undefined) {
    return (
      <main className="p-page-mobile md:p-page">
        <p className="text-cousine-metadane text-muted-foreground" role="status">
          {page.isPending ? copy.material.loading : copy.material.error}
        </p>
      </main>
    );
  }

  const { works, fragments, tags } = material;

  return (
    <EntityLayout
      header={
        <PageHeader
          label={[copy.material.kinds[material.content.kind], material.shelfmark]
            .filter(Boolean)
            .join(" · ")}
          title={material.title}
          description={
            material.description === "" ? undefined : <RichText html={material.description} />
          }
        />
      }
      context={
        works.length > 0 ? <RelatedWorks label={copy.material.works} works={works} /> : undefined
      }
      main={
        <>
          <MediaContent content={material.content} />
          {fragments.total > 0 && (
            <RelatedFragments title={copy.material.fragments} fragments={fragments} />
          )}
        </>
      }
      tags={tags.length > 0 ? <RelatedTags label={copy.material.tags} tags={tags} /> : undefined}
    />
  );
}
