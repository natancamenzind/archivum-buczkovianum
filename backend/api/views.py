import re
from collections import defaultdict

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import (
    AboutPage,
    AboutPageSerializer,
    TeamGroup,
    TypescriptGroup,
    TypescriptGroupSerializer,
    WorkCardSerializer,
)
from archive.models import SiteSettings, TeamMember, Typescript, Work


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


@extend_schema(responses=WorkCardSerializer(many=True))
@api_view(["GET"])
def works(request: Request) -> Response:
    """The works list (US-RA-18): every published work as a card, by first edition."""
    cards = Work.objects.published().with_year().with_fragment_count()
    return Response(WorkCardSerializer(cards, many=True).data)


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
