from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import AboutPage, AboutPageSerializer, TeamGroup, WorkCardSerializer
from archive.models import SiteSettings, TeamMember, Work


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
