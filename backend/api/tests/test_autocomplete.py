from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import Status
from archive.tests.factories import (
    FragmentFactory,
    NoteFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def suggestions(client: Client, q: str) -> list[dict[str, Any]]:
    response = client.get(reverse("search-autocomplete"), {"q": q})
    assert response.status_code == 200
    result: list[dict[str, Any]] = response.json()
    return result


def titles(client: Client, q: str) -> list[str]:
    return [suggestion["title"] for suggestion in suggestions(client, q)]


@pytest.mark.django_db
class TestAutocompleteEndpoint:
    def test_us_ra_17_ac1_suggests_matching_work_titles_and_tag_names(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Czarny potok")
        WorkFactory.create(status=PUBLISHED, title="Wertepy")
        TagFactory.create(status=PUBLISHED, title="Czarny las")

        # Act
        result = titles(client, "czarny")

        # Assert
        assert result == ["Czarny potok", "Czarny las"]

    def test_us_ra_17_ac1_narrows_while_typing(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Czarny potok")
        TagFactory.create(status=PUBLISHED, title="Czarny las")

        # Act
        result = titles(client, "czarny p")

        # Assert
        assert result == ["Czarny potok"]

    def test_us_ra_17_ac1_matches_inside_a_title(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Czarny potok")

        # Act
        result = titles(client, "POTOK")

        # Assert
        assert result == ["Czarny potok"]

    def test_us_ra_17_ac1_ignores_the_case_of_polish_letters(self, client: Client) -> None:
        # Arrange
        TagFactory.create(status=PUBLISHED, title="Śmierć")
        WorkFactory.create(status=PUBLISHED, title="Pierwsza świetność")

        # Act & Assert
        assert titles(client, "śmie") == ["Śmierć"]
        assert titles(client, "ŚWIETN") == ["Pierwsza świetność"]

    def test_us_ra_17_ac1_titles_that_start_with_the_text_come_first(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Czarny las")
        TagFactory.create(status=PUBLISHED, title="Las")
        TagFactory.create(status=PUBLISHED, title="Głuchy las")
        WorkFactory.create(status=PUBLISHED, title="Lasy")

        # Act
        result = titles(client, "las")

        # Assert
        assert result == ["Lasy", "Las", "Czarny las", "Głuchy las"]

    def test_us_ra_17_ac1_suggests_only_works_and_tags(self, client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED, title="Potok")
        typescript = TypescriptFactory.create(
            status=PUBLISHED, work=work, title="Potok, maszynopis", document__text="potok"
        )
        FragmentFactory.create(document=typescript.document, start=0, end=5)
        NoteFactory.create(status=PUBLISHED, title="Potok, notatka")

        # Act
        result = titles(client, "potok")

        # Assert
        assert result == ["Potok"]

    def test_us_ra_17_ac1_drafts_are_never_suggested(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=Status.DRAFT, title="Dezerter (szkic)")
        TagFactory.create(status=Status.DRAFT, title="Dezerter")

        # Act
        result = titles(client, "dezerter")

        # Assert
        assert result == []

    @pytest.mark.parametrize("q", ("", "   ", "%", "_"))
    def test_us_ra_17_ac1_a_blank_text_or_a_wildcard_suggests_nothing(
        self, client: Client, q: str
    ) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Wertepy")

        # Act
        result = suggestions(client, q)

        # Assert
        assert result == []

    def test_us_ra_17_ac1_without_a_query_suggests_nothing(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Wertepy")

        # Act
        response = client.get(reverse("search-autocomplete"))

        # Assert
        assert response.json() == []

    def test_us_ra_17_ac1_suggests_at_most_eight(self, client: Client) -> None:
        # Arrange
        TagFactory.create_batch(10, status=PUBLISHED)

        # Act
        result = suggestions(client, "tag")

        # Assert
        assert len(result) == 8

    def test_us_ra_17_ac2_a_suggestion_links_to_its_page(self, client: Client) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Wertepy", slug="wertepy")
        TagFactory.create(status=PUBLISHED, title="Wertepy (motyw)", slug="wertepy-motyw")

        # Act
        result = suggestions(client, "wertepy")

        # Assert
        assert result == [
            {"type": "work", "title": "Wertepy", "url": "/works/wertepy"},
            {"type": "tag", "title": "Wertepy (motyw)", "url": "/tags/wertepy-motyw"},
        ]

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_autocomplete_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("search-autocomplete")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_autocomplete_takes_one_query(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        TagFactory.create_batch(5, status=PUBLISHED)
        WorkFactory.create_batch(5, status=PUBLISHED, title="Tagi")

        # Act & Assert
        with django_assert_num_queries(1):
            result = suggestions(client, "tag")

        assert len(result) == 8


class TestAutocompleteSchema:
    def test_schema_marks_every_suggestion_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["Suggestion"]["required"]) == ["title", "type", "url"]
