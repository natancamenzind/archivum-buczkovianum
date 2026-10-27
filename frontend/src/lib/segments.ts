/** A fragment's character range in a document's text (architecture §4.4). */
export interface Range {
  id: number;
  start: number;
  end: number;
}

/** A stretch of text with the same fragments over all of it. */
export interface Segment {
  start: number;
  end: number;
  /** The fragments covering the segment, in the order of `ranges`. */
  ids: number[];
}

/**
 * Splits a text of `length` characters at every range boundary and at every `cut` (e.g. page
 * starts) into non-overlapping segments. A range a re-anchoring left past the end of a changed
 * text is clamped to it (#9); one with nothing left covers no segment.
 */
export function segments(length: number, ranges: Range[], cuts: number[] = []): Segment[] {
  const clamped = ranges.map(({ id, start, end }) => {
    const from = Math.min(Math.max(start, 0), length);
    return { id, start: from, end: Math.min(Math.max(end, from), length) };
  });
  const boundaries = [
    ...new Set([0, length, ...cuts, ...clamped.flatMap((range) => [range.start, range.end])]),
  ]
    .filter((offset) => offset >= 0 && offset <= length)
    .sort((a, b) => a - b);

  return boundaries.slice(1).map((end, index) => {
    const start = boundaries[index] ?? 0;
    const ids = clamped
      .filter((range) => range.start <= start && range.end >= end)
      .map((range) => range.id);
    return { start, end, ids };
  });
}
