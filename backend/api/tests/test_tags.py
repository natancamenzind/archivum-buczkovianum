from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import Status, Tag
from archive.tests.factories import NoteFactory, TagFactory, WorkFactory

PUBLISHED = Status.PUBLISHED


def used_tag(occurrences: int = 1, **kwargs: Any) -> Tag:
    """A published tag carried by `occurrences` published notes."""
    tag = TagFactory.create(status=PUBLISHED, **kwargs)
    for note in NoteFactory.create_batch(occurrences, status=PUBLISHED):
        note.tags.add(tag)
    return tag


def tags(client: Client) -> list[dict[str, Any]]:
    response = client.get(reverse("tags"))
    assert response.status_code == 200
    result: list[dict[str, Any]] = response.json()
    return result


@pytest.mark.django_db
class TestTagsEndpoint:
    def test_tags_is_public_and_empty_without_tags(self, client: Client) -> None:
        # Act
        result = tags(client)

        # Assert
        assert result == []

    def test_us_ra_20_ac2_a_tag_has_its_name_link_and_occurrence_count(
        self, client: Client
    ) -> None:
        # Arrange
        tag = used_tag(2, slug="dezerter", title="Dezerter")
        work = WorkFactory.create(status=PUBLISHED)
        work.tags.add(tag)

        # Act
        result = tags(client)

        # Assert
        assert result == [{"slug": "dezerter", "title": "Dezerter", "occurrences": 3}]

    def test_us_ra_20_ac2_drafts_are_left_out(self, client: Client) -> None:
        # Arrange
        used_tag(title="Wojna")
        draft = TagFactory.create(title="Szkic", status=Status.DRAFT)
        NoteFactory.create(status=PUBLISHED).tags.add(draft)

        # Act
        result = tags(client)

        # Assert
        assert [tag["title"] for tag in result] == ["Wojna"]

    def test_us_ra_20_ac2_tags_without_occurrences_are_left_out(self, client: Client) -> None:
        # Arrange
        used_tag(title="Wojna")
        TagFactory.create(title="Nieużywany", status=PUBLISHED)
        NoteFactory.create().tags.add(TagFactory.create(title="Tylko w szkicu", status=PUBLISHED))

        # Act
        result = tags(client)

        # Assert
        assert [tag["title"] for tag in result] == ["Wojna"]

    def test_us_ra_20_ac2_every_tag_in_use_is_listed(self, client: Client) -> None:
        # Arrange
        for title, occurrences in (("Zima", 2), ("Wojna", 31), ("Dezerter", 4)):
            used_tag(occurrences, title=title)

        # Act
        result = tags(client)

        # Assert
        assert {tag["title"]: tag["occurrences"] for tag in result} == {
            "Zima": 2,
            "Wojna": 31,
            "Dezerter": 4,
        }

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_tags_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("tags")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_tags_query_count_does_not_grow_with_tags(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        used_tag(2)
        with django_assert_num_queries(1):
            tags(client)
        for _ in range(5):
            used_tag(2)

        # Act & Assert
        with django_assert_num_queries(1):
            result = tags(client)

        assert len(result) == 6


class TestTagsSchema:
    def test_schema_marks_every_tag_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["TagCount"]["required"]) == ["occurrences", "slug", "title"]
