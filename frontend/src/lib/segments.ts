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
  const position = new Map(boundaries.map((offset, index) => [offset, index]));

  const result: Segment[] = boundaries
    .slice(1)
    .map((end, index) => ({ start: boundaries[index] ?? 0, end, ids: [] }));
  for (const range of clamped) {
    const last = position.get(range.end) ?? 0;
    for (let index = position.get(range.start) ?? last; index < last; index++) {
      result[index]?.ids.push(range.id);
    }
  }
  return result;
}
