from dataclasses import dataclass

from rest_framework import serializers

from archive.models import TeamMember


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
