import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import TeamMember
from archive.tests.factories import SiteSettingsFactory, TeamMemberFactory

Group = TeamMember.Group


@pytest.mark.django_db
class TestAboutEndpoint:
    def test_about_is_public_and_empty_without_content(self, client: Client) -> None:
        # Arrange
        url = reverse("about")

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"intro": "", "project": "", "team": []}

    def test_us_ra_13_ac2_returns_the_introduction(self, client: Client) -> None:
        # Arrange
        SiteSettingsFactory.create(about_intro="<p>Archiwum <em>Buczkowskiego</em>.</p>")

        # Act
        response = client.get(reverse("about"))

        # Assert
        assert response.json()["intro"] == "<p>Archiwum <em>Buczkowskiego</em>.</p>"

    def test_us_ra_13_ac3_returns_the_project_text(self, client: Client) -> None:
        # Arrange
        SiteSettingsFactory.create(about_project="<p>Cel archiwum.</p><p>Zakres zbiorów.</p>")

        # Act
        response = client.get(reverse("about"))

        # Assert
        assert response.json()["project"] == "<p>Cel archiwum.</p><p>Zakres zbiorów.</p>"

    def test_us_ra_13_ac4_groups_come_in_the_story_order(self, client: Client) -> None:
        # Arrange
        TeamMemberFactory.create(group=Group.SITE)
        TeamMemberFactory.create(group=Group.TEAM)
        TeamMemberFactory.create(group=Group.LEADERSHIP)

        # Act
        response = client.get(reverse("about"))

        # Assert
        assert [group["group"] for group in response.json()["team"]] == [
            "leadership",
            "team",
            "site",
        ]

    def test_us_ra_13_ac4_members_have_name_role_and_bio(self, client: Client) -> None:
        # Arrange
        TeamMemberFactory.create(
            name="Anna Nowak",
            role="Redaktorka naukowa",
            bio="Badaczka prozy Buczkowskiego.",
            group=Group.LEADERSHIP,
        )

        # Act
        response = client.get(reverse("about"))

        # Assert
        assert response.json()["team"] == [
            {
                "group": "leadership",
                "members": [
                    {
                        "name": "Anna Nowak",
                        "role": "Redaktorka naukowa",
                        "bio": "Badaczka prozy Buczkowskiego.",
                    }
                ],
            }
        ]

    def test_us_ra_13_ac4_members_are_ordered_by_order(self, client: Client) -> None:
        # Arrange
        TeamMemberFactory.create(name="Celina", order=2)
        TeamMemberFactory.create(name="Adam", order=1)
        TeamMemberFactory.create(name="Bogdan", order=1)

        # Act
        response = client.get(reverse("about"))

        # Assert
        members = response.json()["team"][0]["members"]
        assert [member["name"] for member in members] == ["Adam", "Bogdan", "Celina"]

    def test_us_ra_13_ac4_empty_groups_are_left_out(self, client: Client) -> None:
        # Arrange
        TeamMemberFactory.create(group=Group.LEADERSHIP)
        TeamMemberFactory.create(group=Group.SITE)

        # Act
        response = client.get(reverse("about"))

        # Assert
        assert [group["group"] for group in response.json()["team"]] == ["leadership", "site"]

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_about_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("about")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_about(
        self, client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        SiteSettingsFactory.create()
        for group in Group:
            TeamMemberFactory.create_batch(3, group=group)

        # Act & Assert
        with django_assert_max_num_queries(2):
            response = client.get(reverse("about"))

        assert response.status_code == 200


class TestSchema:
    def test_schema_describes_the_page_endpoints_only(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        response = client.get(url, {"format": "json"})

        # Assert
        assert sorted(response.json()["paths"]) == sorted(
            [
                "/api/about/",
                "/api/editor/fragments/",
                "/api/editor/fragments/{id}/",
                "/api/search/autocomplete/",
                "/api/tags/",
                "/api/typescripts/",
                "/api/works/",
            ]
        )

    def test_schema_marks_every_about_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert schemas["AboutPage"]["required"] == ["intro", "project", "team"]
        assert schemas["TeamGroup"]["required"] == ["group", "members"]
        assert sorted(schemas["TeamMember"]["required"]) == ["bio", "name", "role"]
