import { type Range, type Segment, segments } from "@/lib/segments";

/** A search match's character range in a document's text. */
export interface Match {
  start: number;
  end: number;
}

/** A paragraph of a page: the segments between two blank lines. */
export interface Paragraph {
  start: number;
  segments: Segment[];
}

/** One page of the reader: its paragraphs and the fragments that start on it. */
export interface Page<F extends Range> {
  paragraphs: Paragraph[];
  /** The fragments starting on the page, in text order: each one's note goes on this page. */
  starts: F[];
}

// A blank line, which may hold spaces, separates two paragraphs.
const PARAGRAPH_BREAK = /\n[^\S\n]*\n\s*/g;

/** The id of a fragment's note, which the fragment's highlight names as its description. */
export function noteId(fragment: number): string {
  return `fragment-note-${String(fragment)}`;
}

/** The page (from 1) an offset is on: the last page starting at or before it. */
export function pageOf(offsets: number[], offset: number): number {
  return Math.max(offsets.filter((start) => start <= offset).length, 1);
}

/**
 * Every case-insensitive occurrence of `term` in `text`, in order (R-11 AC5). Each word of the
 * term matches from the start of a word and covers the rest of it, so the start of a word finds
 * all its forms: "wertep" finds "Wertepy" and "wertepami" (ARC-59), as the archive search does
 * (ARC-45). The words may be separated by any whitespace, line breaks included. The term is
 * matched literally, not as a regular expression.
 */
export function findMatches(text: string, term: string): Match[] {
  const words = term.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) {
    return [];
  }
  const escaped = words
    .map((word) => `${word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}[\\p{L}\\p{N}]*`)
    .join("\\s+");
  const pattern = new RegExp(`(?<![\\p{L}\\p{N}])${escaped}`, "giu");
  return Array.from(text.matchAll(pattern), (found) => ({
    start: found.index,
    end: found.index + found[0].length,
  }));
}

/** The index of the match (in text order) covering the range from `start` to `end`, or -1. */
export function matchAt(matches: Match[], start: number, end: number): number {
  let low = 0;
  let high = matches.length - 1;
  while (low <= high) {
    const middle = (low + high) >> 1;
    const match = matches[middle];
    if (match === undefined || match.end <= start) {
      low = middle + 1;
    } else if (match.start > start) {
      high = middle - 1;
    } else {
      return end <= match.end ? middle : -1;
    }
  }
  return -1;
}

/**
 * Splits a document's text into its scan pages (architecture §4.4), each page into paragraphs
 * at blank lines, and each paragraph into segments at fragment and match boundaries. The blank
 * lines themselves are left out: paragraphs are set apart by spacing. A text with no pages is
 * one page.
 */
export function layoutPages<F extends Range>(
  text: string,
  offsets: number[],
  fragments: F[],
  matches: Match[],
): Page<F>[] {
  const pages: Page<F>[] = Array.from({ length: Math.max(offsets.length, 1) }, () => ({
    paragraphs: [],
    starts: [],
  }));
  const breaks = Array.from(text.matchAll(PARAGRAPH_BREAK), (found) => ({
    start: found.index,
    end: found.index + found[0].length,
  }));
  const cuts = [
    ...offsets,
    ...breaks.flatMap((range) => [range.start, range.end]),
    ...matches.flatMap((match) => [match.start, match.end]),
  ];

  let page = 0;
  let paragraph: Paragraph | null = null;
  let breakIndex = 0;
  for (const segment of segments(text.length, fragments, cuts)) {
    while ((offsets[page + 1] ?? Infinity) <= segment.start) {
      page++;
      paragraph = null;
    }
    while ((breaks[breakIndex]?.end ?? Infinity) <= segment.start) {
      breakIndex++;
    }
    const inBreak = (breaks[breakIndex]?.start ?? Infinity) <= segment.start;
    if (inBreak) {
      paragraph = null;
      continue;
    }
    if (paragraph === null) {
      paragraph = { start: segment.start, segments: [] };
      pages[page]?.paragraphs.push(paragraph);
    }
    paragraph.segments.push(segment);
  }

  for (const fragment of [...fragments].sort((a, b) => a.start - b.start)) {
    const start = Math.min(Math.max(fragment.start, 0), text.length);
    pages[Math.min(pageOf(offsets, start), pages.length) - 1]?.starts.push(fragment);
  }
  return pages;
}
