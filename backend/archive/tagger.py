"""Helpers for the fragment tagger admin view (architecture section 5)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from django.db.models import QuerySet

from archive.models import Document, Fragment


def tagger_fragments(document: Document) -> QuerySet[Fragment]:
    """Fragments for the tagger UI and API, with tags prefetched and review-first ordering."""
    return document.fragments.prefetch_related("tags").order_by(
        "-needs_review", "start", "end", "pk"
    )


@dataclass(frozen=True)
class HighlightSegment:
    """A slice of document text and the fragments that cover it."""

    text: str
    fragment_ids: tuple[int, ...]


def highlight_segments(
    text: str, fragments: list[Fragment], start: int = 0
) -> list[HighlightSegment]:
    """Split `text` at every fragment boundary so overlaps render correctly (architecture §4.4).

    `text` begins at offset `start` of its document, as a page does.
    """
    end = start + len(text)
    points = sorted(
        {start, end}
        | {point for f in fragments for point in (f.start, f.end) if start < point < end}
    )
    segments: list[HighlightSegment] = []
    for left, right in itertools.pairwise(points):
        covering = tuple(
            fragment.pk
            for fragment in fragments
            if fragment.start <= left and fragment.end >= right
        )
        segments.append(
            HighlightSegment(text=text[left - start : right - start], fragment_ids=covering)
        )
    return segments


@dataclass(frozen=True)
class TaggerPage:
    """One scan page of the text, as the reader shows it (R-11), with its highlight segments.

    `start` is the page's first character offset. A plain text is one page without a number.
    """

    number: int | None
    start: int
    segments: list[HighlightSegment]


def tagger_pages(document: Document, fragments: list[Fragment]) -> list[TaggerPage]:
    """Split the document's text at its `page_offsets`, highlighting each page's fragments."""
    text = document.text
    if not document.page_offsets:
        return [TaggerPage(number=None, start=0, segments=highlight_segments(text, fragments))]
    bounds = [*document.page_offsets, len(text)]
    return [
        TaggerPage(
            number=number,
            start=start,
            segments=highlight_segments(text[start:end], fragments, start),
        )
        for number, (start, end) in enumerate(itertools.pairwise(bounds), start=1)
    ]
