"""The `<title>` and meta description of every public page (user stories §4, SEO).

The URLs are React Router's (`frontend/src/routes.tsx`). Matching them here lets a crawler read a
page's title without running JavaScript, and lets a URL with no page answer 404. The Polish copy
follows the pages' headings in `frontend/src/copy/pl.ts`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.core.validators import slug_re
from django.http import HttpRequest
from django.utils.text import Truncator

from archive.models import (
    ContextualMaterial,
    Note,
    PublishableQuerySet,
    SecondaryText,
    Tag,
    Typescript,
    Work,
)

SITE_NAME = "Archivum Buczkovianum"
DESCRIPTION = (
    "Archiwum literackie Leopolda Buczkowskiego: utwory, maszynopisy, zapiski "
    "i materiały kontekstowe."
)
DESCRIPTION_LENGTH = 160
# The largest id and decade the database stores: PostgreSQL integer and smallint.
MAX_ID = 2**31 - 1
MAX_DECADE = 32767


@dataclass(frozen=True)
class PageMeta:
    title: str
    description: str = DESCRIPTION


def page_title(name: str) -> str:
    return f"{name} — {SITE_NAME}"


NOT_FOUND = PageMeta(page_title("Nie znaleziono strony"))

PAGES = {
    "": PageMeta(SITE_NAME),
    "works": PageMeta(
        page_title("Utwory"),
        "Wszystkie utwory Leopolda Buczkowskiego w archiwum, w kolejności wydania.",
    ),
    "typescripts": PageMeta(
        page_title("Maszynopisy"),
        "Jednostki archiwalne z maszynopisami utworów, pogrupowane według utworu.",
    ),
    "tags": PageMeta(page_title("Tagi"), "Motywy łączące fragmenty i zapiski z różnych utworów."),
    "about": PageMeta(
        page_title("O archiwum"), "O projekcie Archivum Buczkovianum i jego zespole."
    ),
}
SEARCH_DESCRIPTION = "Szukaj w archiwum: tytuły, opisy, transkrypcje i tagi."

# The first segment of an entity page's URL: its entities, and the field the second segment is.
ENTITIES: dict[str, tuple[Callable[[], PublishableQuerySet[Any]], str]] = {
    "works": (Work.objects.all, "slug"),
    "tags": (Tag.objects.all, "slug"),
    "typescripts": (Typescript.objects.all, "pk"),
    "notes": (Note.objects.all, "pk"),
    "secondary-texts": (SecondaryText.objects.all, "pk"),
    "materials": (ContextualMaterial.objects.all, "pk"),
}


def page_meta(request: HttpRequest) -> PageMeta | None:
    """The meta tags of the page at the request's URL, or None when no page is there."""
    segments = request.path[1:].removesuffix("/").split("/")
    if any(segment.startswith(".") for segment in segments):
        return None
    # React Router matches route paths case-insensitively.
    segments[0] = segments[0].lower()
    match segments:
        case ["search"]:
            return search_meta(request)
        case [name] if name in PAGES:
            return PAGES[name]
        case [kind, key] if kind in ENTITIES:
            return entity_meta(request, kind, key)
    return None


def is_id(value: str, maximum: int) -> bool:
    return value.isascii() and value.isdigit() and 0 < int(value) <= maximum


def search_meta(request: HttpRequest) -> PageMeta:
    """The search page's title follows what it shows: the entry, a query's results or everything.

    A blank query with a tab or a filter lists everything (US-RA-16 AC5), as `isBrowsing()` in
    `frontend/src/lib/search.ts` decides; without either it is the entry.
    """
    params = request.GET
    query = params.get("q", "").strip()
    decade = next(iter(params.getlist("decade")), "")
    if query:
        name = f"Wyniki dla „{query}”"
    elif (
        "tab" in params
        or params.get("has_scan") == "1"
        or params.get("has_text") == "1"
        or any(is_id(work, MAX_ID) for work in params.getlist("work"))
        or (is_id(decade, MAX_DECADE) and int(decade) % 10 == 0)
    ):
        name = "Wszystkie wyniki"
    else:
        name = "Wyszukiwanie"
    return PageMeta(page_title(name), SEARCH_DESCRIPTION)


def entity_meta(request: HttpRequest, kind: str, key: str) -> PageMeta | None:
    """A published entity's page; a draft's only for staff (R-06, US-WR-13)."""
    entities, field = ENTITIES[kind]
    if not (is_id(key, MAX_ID) if field == "pk" else slug_re.match(key)):
        return None
    queryset = entities() if request.user.is_staff else entities().published()
    entity = queryset.filter(**{field: key}).first()
    if entity is None:
        return None
    description = " ".join(entity.description_text.split())
    return PageMeta(
        page_title(entity.title),
        Truncator(description).chars(DESCRIPTION_LENGTH) or DESCRIPTION,
    )
