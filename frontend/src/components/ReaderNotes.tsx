import { type FocusEvent, useLayoutEffect, useRef } from "react";

import type { components } from "@/api/schema";
import { TagList } from "@/components/TagList";
import { noteId } from "@/lib/reader";
import { cn } from "@/lib/utils";

type Fragment = components["schemas"]["DocumentFragment"];

// The space between two notes that would overlap: --space-12.
const NOTE_GAP = 12;

interface NoteProps {
  fragment: Fragment;
  active: boolean;
  /** Hovering or focusing the note highlights its fragment; leaving it, null. */
  onHover: (id: number | null) => void;
}

/**
 * "Tagi fragmentu (margines)": a fragment's tags, with no number or comment (ARC-57). The note
 * of a highlighted fragment takes the accent border, and its tags the accent look.
 */
export function FragmentNote({ fragment, active, onHover }: NoteProps) {
  function leave(event: FocusEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget)) {
      onHover(null);
    }
  }

  return (
    <div
      id={noteId(fragment.id)}
      data-note={fragment.id}
      onMouseEnter={() => {
        onHover(fragment.id);
      }}
      onMouseLeave={() => {
        onHover(null);
      }}
      onFocus={() => {
        onHover(fragment.id);
      }}
      onBlur={leave}
      className={cn("border-l border-border pl-12", active && "border-l-2 border-accent-border")}
    >
      <TagList tags={fragment.tags} active={active} />
    </div>
  );
}

interface MarginProps {
  notes: Fragment[];
  /** The highlighted fragment, or null. */
  active: number | null;
  onHover: (id: number | null) => void;
  /** The reader's view: in "scan" the notes are stacked from the top; otherwise each stands
   * level with its fragment's start, which moves when the view changes the text's width. */
  view: "both" | "text" | "scan";
  className?: string;
}

/**
 * The right margin of a reader page (ARC-57). Each note stands level with the line where its
 * fragment starts, which is the element marked `data-starts` in the page; a note that would
 * overlap the one above moves down. In the "Skan" view the notes are stacked from the top.
 */
export function ReaderMargin({ notes, active, onHover, view, className }: MarginProps) {
  const margin = useRef<HTMLDivElement>(null);
  const stacked = view === "scan";

  useLayoutEffect(() => {
    const element = margin.current;
    const row = element?.parentElement;
    if (stacked || element == null || row == null) {
      return;
    }
    function place() {
      if (element === null || row == null) {
        return;
      }
      const top = element.getBoundingClientRect().top;
      let bottom = -NOTE_GAP;
      for (const note of Array.from(element.children) as HTMLElement[]) {
        const anchor = row.querySelector(`[data-starts~="${note.dataset.for ?? ""}"]`);
        const wanted = anchor === null ? 0 : anchor.getBoundingClientRect().top - top;
        const at = Math.max(wanted, bottom + NOTE_GAP);
        note.style.top = `${String(at)}px`;
        bottom = at + note.offsetHeight;
      }
      element.style.minHeight = `${String(Math.max(bottom, 0))}px`;
    }
    place();
    window.addEventListener("resize", place);
    // Text set in the web fonts takes other lines than in the fallback font. jsdom has no fonts.
    if ("fonts" in window.document) {
      void window.document.fonts.ready.then(place);
    }
    return () => {
      window.removeEventListener("resize", place);
    };
  }, [notes, stacked, view]);

  return (
    <div
      ref={margin}
      className={cn(stacked ? "flex flex-col gap-12 pt-48" : "relative", className)}
    >
      {notes.map((fragment) => (
        <div
          key={fragment.id}
          data-for={fragment.id}
          className={cn(!stacked && "absolute inset-x-0")}
        >
          <FragmentNote fragment={fragment} active={active === fragment.id} onHover={onHover} />
        </div>
      ))}
    </div>
  );
}
