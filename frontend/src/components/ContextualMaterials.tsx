import { Link } from "react-router";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { ImageIcon } from "@/components/icons";
import { SectionHeader } from "@/components/SectionHeader";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";

type Materials = components["schemas"]["ContextualMaterials"];
type MaterialText = components["schemas"]["MaterialText"];
type VisualMaterial = components["schemas"]["VisualMaterial"];

const FOCUS_CLASSES =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

/** "Pozycja bibliograficzna": author and title, then the source. Empty parts are left out. */
function TextItem({ item, number }: { item: MaterialText; number: number }) {
  return (
    <Link
      to={item.url}
      className={`flex gap-12 border-b border-border py-12 hover:text-accent-foreground ${FOCUS_CLASSES}`}
    >
      <span aria-hidden="true" className="text-cousine-metadane-male text-muted-foreground">
        {String(number).padStart(2, "0")}
      </span>
      <span className="flex flex-col gap-4">
        <span className="text-lora-tekst-maly">
          {[item.author, item.title].filter(Boolean).join(", ")}
        </span>
        {item.publication !== "" && (
          <span className="text-cousine-metadane-male text-muted-foreground">
            {item.publication}
          </span>
        )}
      </span>
    </Link>
  );
}

/** "Miniatura materiału": the image, or the placeholder board, with title and shelfmark. */
function VisualItem({ item }: { item: VisualMaterial }) {
  return (
    <Link to={item.url} className={`flex flex-col gap-8 ${FOCUS_CLASSES}`}>
      <span className="flex aspect-3/2 items-center justify-center overflow-hidden rounded-sm bg-media">
        {item.image === "" ? (
          <ImageIcon className="size-16 text-icon" />
        ) : (
          <img src={item.image} alt={item.image_alt} className="size-full object-cover" />
        )}
      </span>
      <span className="text-cousine-metadane-male text-muted-foreground">
        {[item.title, item.shelfmark].filter(Boolean).join(", ")}
      </span>
    </Link>
  );
}

/**
 * The contextual materials block (R-08, "Materiały kontekstowe" in design/components/): a
 * numbered list of secondary texts and other materials, and a gallery of visual materials.
 * Each page passes the items it includes. Empty parts, and an empty block, are not rendered
 * (R-02).
 */
export function ContextualMaterials({ materials }: { materials: Materials }) {
  const { texts, visuals } = materials;
  if (texts.length === 0 && visuals.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-24">
      <SectionHeader title={copy.materials.title} description={copy.materials.description} />
      <div className="grid grid-cols-1 gap-24 md:grid-cols-2">
        {texts.length > 0 && (
          <Card className="gap-8 p-24 md:p-24">
            <ColumnHeader label={copy.materials.texts} count={texts.length} />
            <ol>
              {texts.map((item, index) => (
                <li key={item.url}>
                  <TextItem item={item} number={index + 1} />
                </li>
              ))}
            </ol>
          </Card>
        )}
        {visuals.length > 0 && (
          <Card className="gap-16 p-24 md:p-24">
            <ColumnHeader label={copy.materials.visuals} count={visuals.length} />
            <ul className="grid grid-cols-2 gap-16 sm:grid-cols-3">
              {visuals.map((item) => (
                <li key={item.url}>
                  <VisualItem item={item} />
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </div>
  );
}
