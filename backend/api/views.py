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
    SuggestionSerializer,
    TagCountSerializer,
    TeamGroup,
    TypescriptGroup,
    TypescriptGroupSerializer,
    TypescriptPage,
    TypescriptPageSerializer,
    WorkCardSerializer,
)
from archive.models import (
    ContentKind,
    ContextualMaterial,
    Document,
    Fragment,
    Publishable,
    PublishableQuerySet,
    SecondaryText,
    SiteSettings,
    Status,
    Tag,
    TeamMember,
    Typescript,
    Work,
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
    tag cloud. The featured fragment (US-RA-02) is not here yet."""
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
