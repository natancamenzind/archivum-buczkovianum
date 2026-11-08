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


def highlight_segments(text: str, fragments: list[Fragment]) -> list[HighlightSegment]:
    """Split `text` at every fragment boundary so overlaps render correctly (architecture §4.4)."""
    points = sorted({0, len(text), *(f.start for f in fragments), *(f.end for f in fragments)})
    segments: list[HighlightSegment] = []
    for start, end in itertools.pairwise(points):
        covering = tuple(
            fragment.pk for fragment in fragments if fragment.start <= start and fragment.end >= end
        )
        segments.append(HighlightSegment(text=text[start:end], fragment_ids=covering))
    return segments
