"""Searching the index (docs/architecture.md, section 6; US-RA-15, US-RA-16).

`search()` answers one search page in one call: the results grouped by type, and the counts of
every tab and filter value over the same query. `autocomplete()` suggests works and tags while
the reader types (US-RA-17).
"""

from dataclasses import dataclass, replace

from django.conf import settings
from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank
from django.db import connection, models
from django.db.models import Case, Count, F, Func, QuerySet, Value, When
from django.db.models.functions import Collate, Lower
from django.utils.html import escape

from archive.models import Tag
from search.models import EntityType, SearchEntry

# How many tags the "no results" page suggests (US-RA-15 AC8).
SUGGESTED_TAGS = 3
# Control characters around matched terms in `ts_headline` output. Texts never contain them.
MARK = ("\x02", "\x03")
# How many suggestions the search fields show (US-RA-17).
AUTOCOMPLETE_LIMIT = 8
# A database with the "C" collation changes the case of ASCII letters only, so "ś" would not
# match "Śmierć". ICU's root locale lowercases every letter and ships with PostgreSQL.
CASE_FOLDING_COLLATION = "und-x-icu"


class Tab(models.TextChoices):
    """Search tabs (US-RA-16 AC1). Typescripts, secondary texts and materials are only in "all"."""

    ALL = "all"
    WORKS = "works"
    FRAGMENTS = "fragments"
    NOTES = "notes"
    TAGS = "tags"


TAB_TYPES: dict[Tab, tuple[EntityType, ...]] = {
    Tab.ALL: tuple(EntityType),
    Tab.WORKS: (EntityType.WORK,),
    Tab.FRAGMENTS: (EntityType.FRAGMENT,),
    Tab.NOTES: (EntityType.NOTE,),
    Tab.TAGS: (EntityType.TAG,),
}


class Sort(models.TextChoices):
    RELEVANCE = "relevance"
    TITLE = "title"


@dataclass(frozen=True)
class Filters:
    """Selected filters (US-RA-16 AC2). Values within one filter are alternatives."""

    work_ids: tuple[int, ...] = ()
    decades: tuple[int, ...] = ()
    has_scan: bool = False
    has_text: bool = False


@dataclass(frozen=True)
class Hit:
    entry: SearchEntry
    # HTML: the escaped body with the search terms in <mark>; empty for works, for fragments
    # (their cards show the quote) and for an empty query.
    snippet: str
    # The first matched word of the snippet, as the text spells it, for the reader to scroll to
    # (R-11 AC3); empty when the snippet has none.
    term: str


@dataclass(frozen=True)
class Group:
    entity_type: EntityType
    hits: list[Hit]


@dataclass(frozen=True)
class Facets:
    """Counts shown next to every tab and filter value. Each filter's counts apply all the
    other filters but not itself, so choosing a value never hides its alternatives."""

    tabs: dict[Tab, int]
    works: dict[int, int]
    decades: dict[int, int]
    has_scan: int
    has_text: int


@dataclass(frozen=True)
class SearchResults:
    total: int
    groups: list[Group]
    facets: Facets
    # The most frequent tags, only when nothing was found (US-RA-15 AC8).
    suggested_tags: list[Tag]
    # How many matching fragments each work has, by work id (US-RA-15 AC5).
    work_fragments: dict[int, int]


def search(
    text: str,
    tab: Tab = Tab.ALL,
    filters: Filters | None = None,
    sort: Sort = Sort.RELEVANCE,
) -> SearchResults:
    """Find entries matching `text` (web search syntax: "quoted phrases", or, -word).

    An empty `text`, or one without words to search for, matches everything in the tab and
    filters, sorted by title (US-RA-16 AC5).
    """
    filters = filters or Filters()
    query = None
    matching = SearchEntry.objects.all()
    if _has_lexemes(text):
        query = SearchQuery(text, search_type="websearch", config=settings.SEARCH_TS_CONFIG)
        matching = matching.filter(vector=query)

    in_tab = matching.filter(entity_type__in=TAB_TYPES[tab])
    hits = _hits(_filtered(in_tab, filters), query, sort)
    groups = [
        Group(entity_type, [hit for hit in hits if hit.entry.entity_type == entity_type])
        for entity_type in TAB_TYPES[tab]
    ]
    return SearchResults(
        total=len(hits),
        groups=[group for group in groups if group.hits],
        facets=_facets(matching, in_tab, tab, filters),
        suggested_tags=[] if hits else _suggested_tags(),
        work_fragments=_value_counts(
            _filtered(matching, filters).filter(entity_type=EntityType.FRAGMENT), "work_ids"
        ),
    )


def work_fragment_count(work_id: int) -> int:
    """How many fragments the Fragmenty tab filtered to the work lists (US-RA-02 AC2)."""
    in_tab = SearchEntry.objects.filter(entity_type__in=TAB_TYPES[Tab.FRAGMENTS])
    return _filtered(in_tab, Filters(work_ids=(work_id,))).count()


def _has_lexemes(text: str) -> bool:
    """Whether `text` has a word to search for. Operators alone ("-") and stopwords have none,
    and PostgreSQL would match nothing with them. PostgreSQL's `polish` has no stopwords."""
    if not text.strip():
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT numnode(websearch_to_tsquery(%s::regconfig, %s))",
            [settings.SEARCH_TS_CONFIG, text],
        )
        row = cursor.fetchone()
    return bool(row and row[0])


def _filtered(entries: QuerySet[SearchEntry], filters: Filters) -> QuerySet[SearchEntry]:
    if filters.work_ids:
        entries = entries.filter(work_ids__overlap=list(filters.work_ids))
    if filters.decades:
        entries = entries.filter(decades__overlap=list(filters.decades))
    if filters.has_scan:
        entries = entries.filter(has_scan=True)
    if filters.has_text:
        entries = entries.filter(has_text=True)
    return entries


def _hits(entries: QuerySet[SearchEntry], query: SearchQuery | None, sort: Sort) -> list[Hit]:
    """Results by group in the order of US-RA-15 AC3, then by relevance or title."""
    group = Case(*(When(entity_type=t, then=i) for i, t in enumerate(EntityType)))
    if query is None:
        ordered = entries.annotate(snippet=Value("")).order_by(group, "title", "pk")
    else:
        headline = SearchHeadline(
            "body", query, config=settings.SEARCH_TS_CONFIG, start_sel=MARK[0], stop_sel=MARK[1]
        )
        ordered = entries.annotate(
            rank=SearchRank(F("vector"), query),
            snippet=Case(
                When(entity_type__in=(EntityType.WORK, EntityType.FRAGMENT), then=Value("")),
                default=headline,
                output_field=models.TextField(),
            ),
        )
        within_group = ("-rank", "title") if sort == Sort.RELEVANCE else ("title", "-rank")
        ordered = ordered.order_by(group, *within_group, "pk")
    return [
        Hit(entry=entry, snippet=highlight(entry.snippet), term=_first_term(entry.snippet))
        for entry in ordered
    ]


def highlight(snippet: str) -> str:
    """Escape the text, then turn the markers around matched terms into <mark> tags."""
    return escape(snippet).replace(MARK[0], "<mark>").replace(MARK[1], "</mark>")


def _first_term(snippet: str) -> str:
    """The first marked term of a raw `ts_headline` snippet, or "" without one."""
    start = snippet.find(MARK[0])
    end = snippet.find(MARK[1], start)
    return snippet[start + 1 : end] if start >= 0 and end >= 0 else ""


def _facets(
    matching: QuerySet[SearchEntry], in_tab: QuerySet[SearchEntry], tab: Tab, filters: Filters
) -> Facets:
    per_type = dict(
        _filtered(matching, filters)
        .values_list("entity_type")
        .annotate(count=Count("pk"))
        .order_by()
    )
    return Facets(
        tabs={t: sum(per_type.get(e, 0) for e in types) for t, types in TAB_TYPES.items()},
        works=_value_counts(_filtered(in_tab, replace(filters, work_ids=())), "work_ids"),
        decades=_value_counts(_filtered(in_tab, replace(filters, decades=())), "decades"),
        has_scan=_filtered(in_tab, replace(filters, has_scan=False)).filter(has_scan=True).count(),
        has_text=_filtered(in_tab, replace(filters, has_text=False)).filter(has_text=True).count(),
    )


def _value_counts(entries: QuerySet[SearchEntry], array_field: str) -> dict[int, int]:
    """How many entries hold each value of an array field."""
    values = entries.annotate(value=Func(F(array_field), function="unnest")).values("value")
    return dict(values.annotate(count=Count("pk")).values_list("value", "count").order_by())


def _suggested_tags() -> list[Tag]:
    return list(Tag.objects.published().in_use()[:SUGGESTED_TAGS])


def autocomplete(text: str) -> list[SearchEntry]:
    """Works and tags whose title contains `text`, in any case (US-RA-17). Titles that start
    with it come first, then works before tags, then by title."""
    text = text.strip().lower()
    if not text:
        return []
    entries = SearchEntry.objects.annotate(
        folded=Lower(Collate("title", CASE_FOLDING_COLLATION))
    ).filter(entity_type__in=(EntityType.WORK, EntityType.TAG), folded__contains=text)
    return list(
        entries.order_by(
            Case(When(folded__startswith=text, then=0), default=1),
            Case(When(entity_type=EntityType.WORK, then=0), default=1),
            "title",
            "pk",
        )[:AUTOCOMPLETE_LIMIT]
    )
