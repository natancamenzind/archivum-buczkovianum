import re
from collections import defaultdict
from operator import attrgetter

from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import (
    AboutPage,
    AboutPageSerializer,
    ContextualMaterials,
    DecadeFacet,
    DocumentSerializer,
    FeaturedFragment,
    Found,
    HomePage,
    HomePageSerializer,
    HomeStatistics,
    MaterialPage,
    MaterialPageSerializer,
    NotePage,
    NotePageSerializer,
    SearchFacets,
    SearchPage,
    SearchPageSerializer,
    SearchParamsSerializer,
    SecondaryTextPage,
    SecondaryTextPageSerializer,
    SuggestionSerializer,
    TagCountSerializer,
    TagPage,
    TagPageSerializer,
    TeamGroup,
    TypescriptGroup,
    TypescriptGroupSerializer,
    TypescriptPage,
    TypescriptPageSerializer,
    WorkCardSerializer,
    WorkFacet,
    WorkPage,
    WorkPageSerializer,
)
from archive.models import (
    Archival,
    ContentKind,
    ContextualMaterial,
    Document,
    Fragment,
    MaterialWorkLink,
    Note,
    Preview,
    Publishable,
    PublishableQuerySet,
    SecondaryText,
    SecondaryTextWorkLink,
    SiteSettings,
    Status,
    Tag,
    TeamMember,
    Typescript,
    Work,
    preview,
)
from search.models import EntityType
from search.query import (
    Facets,
    Filters,
    Hit,
    Sort,
    Tab,
    autocomplete,
    search,
    work_fragment_count,
)


@extend_schema(responses=AboutPageSerializer)
@api_view(["GET"])
def about(request: Request) -> Response:
    """The About page (US-RA-13): introduction, project text and the team by group.

    Empty groups are left out (R-02), so the page renders every group it gets.
    """
    settings = SiteSettings.load()
    members = list(TeamMember.objects.all())
    team = [
        TeamGroup(group=group, members=[member for member in members if member.group == group])
        for group in TeamMember.Group
    ]
    page = AboutPage(
        intro=settings.about_intro,
        project=settings.about_project,
        team=[group for group in team if group.members],
    )
    return Response(AboutPageSerializer(page).data)


@extend_schema(responses=HomePageSerializer)
@api_view(["GET"])
def home(request: Request) -> Response:
    """The home page (US-RA-01): introduction and portrait, the counts, the work cards, a random
    featured fragment (US-RA-02) and the tag cloud."""
    cards = list(Work.objects.published().with_year().with_fragment_count())
    owners = [f"document__{owner}__institution" for owner in Document.owner_accessors()]
    fragment = (
        Fragment.objects.visible()
        .filter(is_featured=True)
        .with_number()
        .select_related(*owners)
        .prefetch_related(Prefetch("tags", Tag.objects.published()))
        .order_by("?")
        .first()
    )
    sources = source_works([fragment] if fragment else [], cards)
    featured = (
        FeaturedFragment(fragment, featured_work(sources.get(fragment.document_id, [])))
        if fragment
        else None
    )
    page = HomePage(
        settings=SiteSettings.load(),
        statistics=HomeStatistics(
            works=len(cards),
            fragments=Fragment.objects.visible().count(),
            tags=Tag.objects.published().count(),
        ),
        works=cards,
        featured=featured,
        tags=list(Tag.objects.published().in_use()),
    )
    return Response(HomePageSerializer(page, context={"works": sources}).data)


def featured_work(works: list[Work]) -> WorkFacet | None:
    """The first of a featured fragment's works, with the count of the Fragmenty search filtered
    to it (US-RA-02 AC2)."""
    return WorkFacet(works[0], work_fragment_count(works[0].pk)) if works else None


@extend_schema(responses=WorkCardSerializer(many=True))
@api_view(["GET"])
def works(request: Request) -> Response:
    """The works list (US-RA-18): every published work as a card, by first edition."""
    cards = Work.objects.published().with_year().with_fragment_count()
    return Response(WorkCardSerializer(cards, many=True).data)


@extend_schema(responses=TagCountSerializer(many=True))
@api_view(["GET"])
def tags(request: Request) -> Response:
    """The tags list (US-RA-20): published tags with at least one occurrence (D26), the most
    frequent first. The cloud and the alphabetical index both take this one list."""
    return Response(TagCountSerializer(Tag.objects.published().in_use(), many=True).data)


def shelfmark_order(typescript: Typescript) -> tuple[bool, list[int | str], str]:
    """Shelfmarks compare as numbers ("999" before "1618"); typescripts without one come last."""
    parts = re.split(r"(\d+)", typescript.shelfmark)
    number: list[int | str] = [int(part) if part.isdecimal() else part for part in parts]
    return (typescript.shelfmark == "", number, typescript.title)


@extend_schema(responses=TypescriptGroupSerializer(many=True))
@api_view(["GET"])
def typescripts(request: Request) -> Response:
    """The typescripts list (US-RA-19): published typescripts grouped by their published work,
    works by first edition. A work without published typescripts has no group (R-02)."""
    by_work: dict[int, list[Typescript]] = defaultdict(list)
    for typescript in Typescript.objects.published().select_related("institution"):
        by_work[typescript.work_id].append(typescript)
    groups = [
        TypescriptGroup(work=work, typescripts=sorted(by_work[work.pk], key=shelfmark_order))
        for work in Work.objects.published().filter(pk__in=list(by_work)).with_year()
    ]
    return Response([TypescriptGroupSerializer(group).data for group in groups])


@extend_schema(
    parameters=[OpenApiParameter("q", str, description="What the reader has typed so far.")],
    responses=SuggestionSerializer(many=True),
)
@api_view(["GET"])
def search_autocomplete(request: Request) -> Response:
    """Suggestions under the search fields (US-RA-17): published works and tags whose title
    contains `q`. Empty for a blank `q`."""
    suggestions = autocomplete(request.query_params.get("q", ""))
    return Response(SuggestionSerializer(suggestions, many=True).data)


def found[M: Publishable](queryset: PublishableQuerySet[M], hits: list[Hit]) -> list[Found[M]]:
    """The published entities of `hits`, in the order of the hits."""
    items = queryset.published().in_bulk([hit.entry.entity_id for hit in hits])
    return [Found(items[hit.entry.entity_id], hit) for hit in hits if hit.entry.entity_id in items]


def search_facets(facets: Facets, filters: Filters, works: list[Work]) -> SearchFacets:
    """The filter values to offer: those with results, and the selected ones, so they can be
    cleared. `works` are the published works, by first edition."""
    return SearchFacets(
        tabs={tab.value: count for tab, count in facets.tabs.items()},
        works=[
            WorkFacet(work, facets.works.get(work.pk, 0))
            for work in works
            if work.pk in facets.works or work.pk in filters.work_ids
        ],
        decades=[
            DecadeFacet(decade, facets.decades.get(decade, 0))
            for decade in sorted({*facets.decades, *filters.decades})
        ],
        has_scan=facets.has_scan,
        has_text=facets.has_text,
    )


@extend_schema(parameters=[SearchParamsSerializer], responses=SearchPageSerializer)
@api_view(["GET"])
def search_results(request: Request) -> Response:
    """The search results (US-RA-15, US-RA-16) in the tab and filters, grouped by type. A blank
    `q`, or one of stopwords only, finds everything."""
    params = SearchParamsSerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    options = params.validated_data
    filters = Filters(
        work_ids=tuple(options["work"]),
        decades=tuple(options["decade"]),
        has_scan=options["has_scan"],
        has_text=options["has_text"],
    )
    results = search(
        options["q"], tab=Tab(options["tab"]), filters=filters, sort=Sort(options["sort"])
    )
    hits = {group.entity_type: group.hits for group in results.groups}

    fragment_ids = [hit.entry.entity_id for hit in hits.get(EntityType.FRAGMENT, [])]
    owners = Document.owner_accessors()
    by_pk = (
        Fragment.objects.visible()
        .with_number()
        .select_related(*(f"document__{owner}__institution" for owner in owners))
        .prefetch_related(Prefetch("tags", Tag.objects.published()))
        .in_bulk(fragment_ids)
    )
    fragments = [by_pk[pk] for pk in fragment_ids if pk in by_pk]
    works = list(Work.objects.published().with_year())
    works_by_pk = {work.pk: work for work in works}
    page = SearchPage(
        facets=search_facets(results.facets, filters, works),
        works=[
            Found(works_by_pk[hit.entry.entity_id], hit)
            for hit in hits.get(EntityType.WORK, [])
            if hit.entry.entity_id in works_by_pk
        ],
        tags=found(Tag.objects.with_occurrences(), hits.get(EntityType.TAG, [])),
        fragments=fragments,
        notes=found(Note.objects.select_related("institution"), hits.get(EntityType.NOTE, [])),
        typescripts=found(
            Typescript.objects.select_related("institution"), hits.get(EntityType.TYPESCRIPT, [])
        ),
        secondary_texts=found(
            SecondaryText.objects.select_related("institution"),
            hits.get(EntityType.SECONDARY_TEXT, []),
        ),
        materials=found(
            ContextualMaterial.objects.select_related("institution"),
            hits.get(EntityType.MATERIAL, []),
        ),
        suggested_tags=results.suggested_tags,
    )
    context = {
        "work_fragments": results.work_fragments,
        "works": source_works(fragments, works),
    }
    return Response(SearchPageSerializer(page, context=context).data)


def contextual_materials(
    secondary_texts: PublishableQuerySet[SecondaryText],
    materials: PublishableQuerySet[ContextualMaterial],
) -> ContextualMaterials:
    """The published items of the contextual materials block (R-08): images in the gallery,
    secondary texts and the other materials in the list, both by title."""
    published = list(materials.published().select_related("institution"))
    texts: list[SecondaryText | ContextualMaterial] = [
        *secondary_texts.published(),
        *(material for material in published if material.content_kind != ContentKind.IMAGE),
    ]
    return ContextualMaterials(
        texts=sorted(texts, key=attrgetter("title")),
        visuals=[material for material in published if material.content_kind == ContentKind.IMAGE],
    )


@extend_schema(responses=TypescriptPageSerializer)
@api_view(["GET"])
def typescript(request: Request, pk: int) -> Response:
    """The typescript page (US-RA-08). A draft typescript is not found (R-06); a draft work
    leaves out the work, its contextual materials and nothing else."""
    current = get_object_or_404(
        Typescript.objects.published().select_related("institution", "document"), pk=pk
    )
    work = (
        Work.objects.published()
        .filter(pk=current.work_id)
        .with_year()
        .with_fragment_count()
        .first()
    )
    page = TypescriptPage(
        typescript=current,
        work=work,
        work_typescripts=sorted(
            Typescript.objects.published()
            .filter(work=current.work_id)
            .select_related("institution"),
            key=shelfmark_order,
        ),
        fragments=Fragment.objects.filter(document=current.document).with_number().preview(),
        tags=list(
            Tag.objects.published()
            .filter(Q(typescripts=current) | Q(fragments__document=current.document))
            .distinct()
            .order_by("title")
        ),
        materials=contextual_materials(
            SecondaryText.objects.filter(works=work),
            ContextualMaterial.objects.filter(works=work),
        )
        if work
        else ContextualMaterials(texts=[], visuals=[]),
    )
    context = {"institution": current.institution}
    return Response(TypescriptPageSerializer(page, context=context).data)


@extend_schema(responses=WorkPageSerializer)
@api_view(["GET"])
def work(request: Request, slug: str) -> Response:
    """The work page (US-RA-04). A draft work is not found (R-06)."""
    current = get_object_or_404(
        Work.objects.published().with_year().prefetch_related("editions"), slug=slug
    )
    typescripts = Typescript.objects.published().filter(work=current)
    main = typescripts.filter(is_main=True).first()
    published_tags = Prefetch("tags", Tag.objects.published())
    fragments = (
        Fragment.objects.filter(document__typescript=main)
        .select_related("document__typescript__institution")
        .prefetch_related(published_tags)
        .with_number()
        .preview()
        if main
        else Preview[Fragment](items=[], total=0)
    )
    page = WorkPage(
        work=current,
        main_typescript=main.pk if main else None,
        fragments=fragments,
        typescripts=sorted(typescripts.select_related("institution"), key=shelfmark_order),
        notes=list(
            Note.objects.published()
            .filter(works=current)
            .select_related("institution")
            .prefetch_related(published_tags)
        ),
        tags=list(Tag.objects.published().referring_to(current).distinct().order_by("title")),
        materials=contextual_materials(
            SecondaryText.objects.filter(works=current),
            ContextualMaterial.objects.filter(works=current),
        ),
    )
    return Response(WorkPageSerializer(page).data)


def related_fragments(item: Note | SecondaryText | ContextualMaterial) -> Preview[Fragment]:
    """The preview of an item's related fragments (US-RA-10 AC3), loaded for fragment cards."""
    return preview(
        Fragment.objects.sharing_tags_with(item)
        .select_related("document__typescript__institution")
        .prefetch_related(Prefetch("tags", Tag.objects.published()))
        .with_number()
    )


@extend_schema(responses=SecondaryTextPageSerializer)
@api_view(["GET"])
def secondary_text(request: Request, pk: int) -> Response:
    """The secondary text page (US-RA-10). A draft secondary text is not found (R-06)."""
    current = get_object_or_404(SecondaryText.objects.published(), pk=pk)
    published_tags = Tag.objects.published()
    links = SecondaryTextWorkLink.objects.visible().filter(secondary_text=current)
    page = SecondaryTextPage(
        secondary_text=current,
        works=list(current.related_works().with_fragment_count()),
        fragments=related_fragments(current),
        tags=list(
            published_tags.filter(
                Q(secondarytexts=current)
                | Q(fragments__document=current.document_id)
                | Q(pk__in=links.values("tags"))
            )
            .distinct()
            .order_by("title")
        ),
    )
    return Response(SecondaryTextPageSerializer(page).data)


@extend_schema(responses=NotePageSerializer)
@api_view(["GET"])
def note(request: Request, pk: int) -> Response:
    """The note page (US-RA-11). A draft note is not found (R-06)."""
    current = get_object_or_404(Note.objects.published().select_related("institution"), pk=pk)
    published_tags = Tag.objects.published()
    page = NotePage(
        note=current,
        works=list(current.related_works().with_fragment_count()),
        fragments=related_fragments(current),
        tags=list(
            published_tags.filter(Q(notes=current) | Q(fragments__document__note=current))
            .distinct()
            .order_by("title")
        ),
    )
    return Response(NotePageSerializer(page).data)


@extend_schema(responses=MaterialPageSerializer)
@api_view(["GET"])
def material(request: Request, pk: int) -> Response:
    """The contextual material page (US-RA-12). A draft material is not found (R-06)."""
    current = get_object_or_404(
        ContextualMaterial.objects.published().select_related("institution"), pk=pk
    )
    published_tags = Tag.objects.published()
    links = MaterialWorkLink.objects.visible().filter(material=current)
    page = MaterialPage(
        material=current,
        works=list(current.related_works().with_fragment_count()),
        fragments=related_fragments(current),
        tags=list(
            published_tags.filter(
                Q(contextualmaterials=current)
                | Q(fragments__document__contextualmaterial=current)
                | Q(pk__in=links.values("tags"))
            )
            .distinct()
            .order_by("title")
        ),
    )
    return Response(MaterialPageSerializer(page).data)


# The kinds of item a fragment's text belongs to, in the order the tag page lists their
# fragments within a work.
SOURCES = (Typescript, Note, SecondaryText, ContextualMaterial)


def source_works(fragments: list[Fragment], works: list[Work]) -> dict[int, list[Work]]:
    """The published works of the fragments' sources, by first edition, keyed by document ID:
    one query per kind of source present instead of one per fragment. `works` holds them all."""
    by_pk = {work.pk: work for work in works}
    documents: dict[type[Archival], set[int]] = defaultdict(set)
    for fragment in fragments:
        owner = fragment.document.owner
        assert owner is not None
        documents[type(owner)].add(fragment.document_id)
    sources: dict[int, list[Work]] = defaultdict(list)
    for source, ids in documents.items():
        document = f"{source.works_lookup}__document"
        pairs = (
            Work.objects.published()
            .with_year()
            .filter(**{f"{document}__in": ids})
            .values_list(document, "pk")
        )
        for document_id, work_id in pairs:
            sources[document_id].append(by_pk[work_id])
    return sources


@extend_schema(responses=TagPageSerializer)
@api_view(["GET"])
def tag(request: Request, slug: str) -> Response:
    """The tag page (US-RA-07). A draft tag is not found (R-06)."""
    current = get_object_or_404(Tag.objects.published().with_occurrences(), slug=slug)
    works = list(
        Work.objects.published()
        .referred_to_by(current)
        .with_year()
        .with_fragment_count(current)
        .distinct()
    )
    published_tags = Prefetch("tags", Tag.objects.published())
    owners = [f"document__{owner}__institution" for owner in Document.owner_accessors()]
    fragments = list(
        Fragment.objects.visible()
        .filter(tags=current)
        .select_related("document", *owners)
        .prefetch_related(published_tags)
        .with_number()
    )
    sources = source_works(fragments, works)
    position = {work.pk: index for index, work in enumerate(works)}

    def by_work_then_text(fragment: Fragment) -> tuple[int, int, int, int, int, int]:
        first = sources.get(fragment.document_id)
        work = position[first[0].pk] if first else len(position)
        kind = SOURCES.index(type(fragment.document.owner))
        return (work, kind, fragment.document_id, fragment.start, fragment.end, fragment.pk)

    carrying = Q(tags=current) | Q(document__fragments__tags=current)
    page = TagPage(
        tag=current,
        works=works,
        fragments=sorted(fragments, key=by_work_then_text),
        notes=list(
            Note.objects.published()
            .filter(carrying)
            .distinct()
            .select_related("institution")
            .prefetch_related(published_tags)
        ),
        related=list(Tag.objects.published().filter(related=current).order_by("title")),
        materials=contextual_materials(
            SecondaryText.objects.filter(
                carrying
                | Q(work_links__in=SecondaryTextWorkLink.objects.visible().filter(tags=current))
            ).distinct(),
            ContextualMaterial.objects.filter(
                carrying | Q(work_links__in=MaterialWorkLink.objects.visible().filter(tags=current))
            ).distinct(),
        ),
    )
    return Response(TagPageSerializer(page, context={"works": sources}).data)


@extend_schema(responses=DocumentSerializer)
@api_view(["GET"])
def document(request: Request, pk: int) -> Response:
    """The text of a published item for the reader (R-11), with its fragments and their
    published tags. The text of a draft, or of no item, is not found (R-06)."""
    fragments = Fragment.objects.with_number().order_by("start", "end", "pk")
    text = get_object_or_404(
        Document.objects.prefetch_related(
            Prefetch(
                "fragments",
                fragments.prefetch_related(Prefetch("tags", Tag.objects.published())),
            )
        ),
        pk=pk,
    )
    owner = text.owner
    if not isinstance(owner, Publishable) or owner.status != Status.PUBLISHED:
        raise Http404
    context = {"document": text, "institution": owner.institution}
    return Response(DocumentSerializer(text, context=context).data)
