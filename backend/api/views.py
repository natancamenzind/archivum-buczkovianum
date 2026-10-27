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
    DocumentSerializer,
    HomePage,
    HomePageSerializer,
    HomeStatistics,
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
    WorkPage,
    WorkPageSerializer,
)
from archive.models import (
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
from search.query import autocomplete


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
    """The home page (US-RA-01): introduction and portrait, the counts, the work cards and the
    tag cloud."""
    cards = list(Work.objects.published().with_year().with_fragment_count())
    page = HomePage(
        settings=SiteSettings.load(),
        statistics=HomeStatistics(
            works=len(cards),
            fragments=Fragment.objects.visible().count(),
            tags=Tag.objects.published().count(),
        ),
        works=cards,
        tags=list(Tag.objects.published().in_use()),
    )
    return Response(HomePageSerializer(page).data)


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
        fragments=preview(
            Fragment.objects.sharing_tags_with(current)
            .select_related("document__typescript__institution")
            .prefetch_related(Prefetch("tags", published_tags))
            .with_number()
        ),
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


def source_works(fragments: list[Fragment], works: list[Work]) -> dict[int, list[Work]]:
    """The published works of the fragments' sources, by first edition, keyed by document ID:
    one query per kind of source instead of one per fragment. `works` holds them all."""
    by_pk = {work.pk: work for work in works}
    documents = {fragment.document_id for fragment in fragments}
    sources: dict[int, list[Work]] = defaultdict(list)
    for source in (Typescript, Note, SecondaryText, ContextualMaterial):
        document = f"{source.works_lookup}__document"
        pairs = (
            Work.objects.published()
            .with_year()
            .filter(**{f"{document}__in": documents})
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

    def by_work_then_text(fragment: Fragment) -> tuple[int, int, int, int, int]:
        first = sources.get(fragment.document_id)
        work = position[first[0].pk] if first else len(position)
        return (work, fragment.document_id, fragment.start, fragment.end, fragment.pk)

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
