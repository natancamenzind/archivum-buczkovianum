from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import Status, Typescript, Work
from archive.tests.factories import (
    EditionFactory,
    InstitutionFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def published_work(year: int | None = None, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    if year is not None:
        EditionFactory.create(work=work, year=year)
    return work


def published_typescript(work: Work, **kwargs: Any) -> Typescript:
    return TypescriptFactory.create(work=work, status=PUBLISHED, **kwargs)


def groups(client: Client) -> list[dict[str, Any]]:
    response = client.get(reverse("typescripts"))
    assert response.status_code == 200
    result: list[dict[str, Any]] = response.json()
    return result


def titles(result: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    return [
        (group["title"], [typescript["title"] for typescript in group["typescripts"]])
        for group in result
    ]


@pytest.mark.django_db
class TestTypescriptsEndpoint:
    def test_typescripts_is_public_and_empty_without_typescripts(self, client: Client) -> None:
        # Act
        result = groups(client)

        # Assert
        assert result == []

    def test_us_ra_19_ac2_a_group_has_what_its_header_and_cards_show(self, client: Client) -> None:
        # Arrange
        work = published_work(1947, slug="wertepy", title="Wertepy", genre="powieść")
        typescript = published_typescript(
            work, title="Pierwsza wersja", institution=InstitutionFactory.create(), shelfmark="1618"
        )

        # Act
        result = groups(client)

        # Assert
        assert result == [
            {
                "slug": "wertepy",
                "title": "Wertepy",
                "genre": "powieść",
                "year": 1947,
                "typescripts": [
                    {"id": typescript.pk, "title": "Pierwsza wersja", "shelfmark": "ML, sygn. 1618"}
                ],
            }
        ]

    def test_us_ra_19_ac2_groups_come_by_first_edition(self, client: Client) -> None:
        # Arrange
        for title, year in (
            ("Pierwsza świetność", 1966),
            ("Bez wydań", None),
            ("Wertepy", 1947),
            ("Czarny potok", 1954),
        ):
            published_typescript(published_work(year, title=title), title=f"Maszynopis {title}")

        # Act
        result = groups(client)

        # Assert
        assert [(group["title"], group["year"]) for group in result] == [
            ("Wertepy", 1947),
            ("Czarny potok", 1954),
            ("Pierwsza świetność", 1966),
            ("Bez wydań", None),
        ]

    def test_us_ra_19_ac2_typescripts_are_ordered_by_shelfmark_as_numbers(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work(1947)
        for title, shelfmark in (("Bez sygnatury", ""), ("B", "1619"), ("C", "999"), ("A", "1618")):
            published_typescript(work, title=title, shelfmark=shelfmark)

        # Act
        result = groups(client)

        # Assert
        assert titles(result) == [(work.title, ["C", "A", "B", "Bez sygnatury"])]

    def test_us_ra_19_ac2_drafts_are_left_out(self, client: Client) -> None:
        # Arrange
        work = published_work(1947, title="Wertepy")
        published_typescript(work, title="Opublikowany")
        TypescriptFactory.create(work=work, title="Szkic", status=Status.DRAFT)
        # R-06: a draft work's group would show the draft's title.
        draft_work = WorkFactory.create(title="Szkic utworu", status=Status.DRAFT)
        published_typescript(draft_work, title="Maszynopis szkicu")

        # Act
        result = groups(client)

        # Assert
        assert titles(result) == [("Wertepy", ["Opublikowany"])]

    def test_us_ra_19_ac2_a_work_without_published_typescripts_has_no_group(
        self, client: Client
    ) -> None:
        # Arrange
        published_typescript(published_work(1947, title="Wertepy"), title="Maszynopis")
        TypescriptFactory.create(work=published_work(1954), status=Status.DRAFT)
        published_work(1957)

        # Act
        result = groups(client)

        # Assert
        assert titles(result) == [("Wertepy", ["Maszynopis"])]

    def test_us_ra_19_ac2_a_shelfmark_without_institution_or_number(self, client: Client) -> None:
        # Arrange
        work = published_work(1947)
        published_typescript(work, title="A", shelfmark="1618")
        published_typescript(work, title="B", shelfmark="")

        # Act
        result = groups(client)

        # Assert
        shelfmarks = [typescript["shelfmark"] for typescript in result[0]["typescripts"]]
        assert shelfmarks == ["sygn. 1618", ""]

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_typescripts_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("typescripts")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_typescripts_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        institution = InstitutionFactory.create()

        def add_work() -> None:
            work = published_work(1947)
            for _ in range(2):
                published_typescript(work, institution=institution, shelfmark="1618")

        add_work()
        with django_assert_num_queries(2):
            groups(client)
        for _ in range(5):
            add_work()

        # Act & Assert
        with django_assert_num_queries(2):
            result = groups(client)

        assert len(result) == 6


class TestTypescriptsSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["TypescriptGroup"]["required"]) == [
            "genre",
            "slug",
            "title",
            "typescripts",
            "year",
        ]
        assert sorted(schemas["TypescriptRow"]["required"]) == ["id", "shelfmark", "title"]
