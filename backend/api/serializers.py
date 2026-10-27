from dataclasses import dataclass

from rest_framework import serializers

from archive.models import TeamMember, Work


@dataclass(frozen=True)
class TeamGroup:
    group: TeamMember.Group
    members: list[TeamMember]


@dataclass(frozen=True)
class AboutPage:
    intro: str
    project: str
    team: list[TeamGroup]


class TeamMemberSerializer(serializers.ModelSerializer[TeamMember]):
    class Meta:
        model = TeamMember
        fields = ("name", "role", "bio")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class TeamGroupSerializer(serializers.Serializer[TeamGroup]):
    group = serializers.ChoiceField(choices=TeamMember.Group.choices)
    members = TeamMemberSerializer(many=True)


class AboutPageSerializer(serializers.Serializer[AboutPage]):
    """US-RA-13. Texts are plain text until step 10 makes them rich text."""

    intro = serializers.CharField(allow_blank=True)
    project = serializers.CharField(allow_blank=True)
    team = TeamGroupSerializer(
        many=True, help_text="Groups that have members, in the order of TeamMember.Group."
    )


class WorkCardSerializer(serializers.ModelSerializer[Work]):
    """The work card (US-RA-01 AC3), from a queryset with `with_year()` and
    `with_fragment_count()`."""

    year = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="The year of the first edition; null without editions.",
    )
    cover_image = serializers.SerializerMethodField(help_text="Empty when the work has no cover.")
    fragment_count = serializers.IntegerField(
        read_only=True, help_text="Visible fragments of the main typescript (D19); 0 without one."
    )

    class Meta:
        model = Work
        fields = (
            "slug",
            "title",
            "genre",
            "year",
            "cover_image",
            "cover_image_alt",
            "fragment_count",
        )
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_cover_image(self, work: Work) -> str:
        return work.cover_image.url if work.cover_image else ""
