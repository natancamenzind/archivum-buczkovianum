from pathlib import Path
from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import Status, Work
from archive.tests.factories import (
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    NoteFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def published_work(**kwargs: Any) -> Work:
    return WorkFactory.create(status=PUBLISHED, **kwargs)


def add_fragments(work: Work, count: int, **typescript: Any) -> None:
    """A typescript of `work` with `count` fragments; published and main unless overridden."""
    options = {"status": PUBLISHED, "is_main": True, **typescript}
    document = TypescriptFactory.create(work=work, **options).document
    FragmentFactory.create_batch(count, document=document)


def cards(client: Client) -> list[dict[str, Any]]:
    response = client.get(reverse("works"))
    assert response.status_code == 200
    result: list[dict[str, Any]] = response.json()
    return result


@pytest.mark.django_db
class TestWorksEndpoint:
    def test_works_is_public_and_empty_without_works(self, client: Client) -> None:
        # Act
        result = cards(client)

        # Assert
        assert result == []

    def test_us_ra_18_ac2_a_card_has_what_the_work_card_shows(self, client: Client) -> None:
        # Arrange
        work = published_work(slug="wertepy", title="Wertepy", genre="powieść")
        EditionFactory.create(work=work, year=1947)
        add_fragments(work, 3)

        # Act
        result = cards(client)

        # Assert
        assert result == [
            {
                "slug": "wertepy",
                "title": "Wertepy",
                "genre": "powieść",
                "year": 1947,
                "cover_image": "",
                "cover_image_alt": "",
                "fragment_count": 3,
            }
        ]

    def test_us_ra_18_ac2_drafts_are_left_out(self, client: Client) -> None:
        # Arrange
        published_work(title="Wertepy")
        WorkFactory.create(title="Szkic", status=Status.DRAFT)

        # Act
        result = cards(client)

        # Assert
        assert [card["title"] for card in result] == ["Wertepy"]

    def test_us_ra_18_ac2_lists_published_works_by_first_edition(self, client: Client) -> None:
        # Arrange
        for title, years in (
            ("Pierwsza świetność", (1966,)),
            ("Wertepy", (1973, 1947, 1957)),
            ("Czarny potok", (1954,)),
            ("Aaa", (1954,)),
        ):
            work = published_work(title=title)
            for year in years:
                EditionFactory.create(work=work, year=year)

        # Act
        result = cards(client)

        # Assert
        assert [(card["title"], card["year"]) for card in result] == [
            ("Wertepy", 1947),
            ("Aaa", 1954),
            ("Czarny potok", 1954),
            ("Pierwsza świetność", 1966),
        ]

    def test_us_ra_18_ac2_a_work_without_editions_comes_last(self, client: Client) -> None:
        # Arrange
        published_work(title="Aaa bez wydań")
        EditionFactory.create(work=published_work(title="Wertepy"), year=1947)

        # Act
        result = cards(client)

        # Assert
        assert [(card["title"], card["year"]) for card in result] == [
            ("Wertepy", 1947),
            ("Aaa bez wydań", None),
        ]

    def test_us_ra_01_ac3_the_count_ignores_fragments_of_other_typescripts(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work()
        add_fragments(work, 2)
        add_fragments(work, 5, is_main=False)
        add_fragments(published_work(), 7)
        FragmentFactory.create_batch(
            4,
            document=NoteFactory.create(
                status=PUBLISHED, document=DocumentFactory.create()
            ).document,
        )

        # Act
        result = cards(client)

        # Assert
        assert {card["slug"]: card["fragment_count"] for card in result}[work.slug] == 2

    def test_us_ra_01_ac3_the_count_ignores_a_draft_main_typescript(self, client: Client) -> None:
        # Arrange
        work = published_work()
        add_fragments(work, 3, status=Status.DRAFT)

        # Act
        result = cards(client)

        # Assert
        assert result[0]["fragment_count"] == 0

    def test_us_ra_01_ac3_the_count_is_0_without_a_main_typescript(self, client: Client) -> None:
        # Arrange
        work = published_work()
        add_fragments(work, 3, is_main=False)

        # Act
        result = cards(client)

        # Assert
        assert result[0]["fragment_count"] == 0

    def test_us_ra_01_ac3_a_work_without_a_cover_has_an_empty_cover(
        self, client: Client, settings: Settings, tmp_path: Path
    ) -> None:
        # Arrange
        settings.MEDIA_ROOT = tmp_path
        work = published_work()
        # D25: an edition's cover is not a fallback.
        EditionFactory.create(
            work=work,
            cover_image=ContentFile(b"img", name="edition.png"),
            cover_image_alt="Okładka",
        )

        # Act
        result = cards(client)

        # Assert
        assert (result[0]["cover_image"], result[0]["cover_image_alt"]) == ("", "")

    def test_us_ra_01_ac3_returns_the_cover_and_its_alternative(
        self, client: Client, settings: Settings, tmp_path: Path
    ) -> None:
        # Arrange
        settings.MEDIA_ROOT = tmp_path
        published_work(
            cover_image=ContentFile(b"img", name="wertepy.png"), cover_image_alt="Koń na okładce"
        )

        # Act
        result = cards(client)

        # Assert
        assert result[0]["cover_image"] == "/media/works/wertepy.png"
        assert result[0]["cover_image_alt"] == "Koń na okładce"

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_works_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("works")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_works_query_count_does_not_grow_with_works(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        def add_work() -> None:
            work = published_work()
            EditionFactory.create(work=work)
            add_fragments(work, 2)

        add_work()
        with django_assert_num_queries(1):
            cards(client)
        for _ in range(5):
            add_work()

        # Act & Assert
        with django_assert_num_queries(1):
            result = cards(client)

        assert len(result) == 6


class TestWorksSchema:
    def test_schema_marks_every_card_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["WorkCard"]["required"]) == [
            "cover_image",
            "cover_image_alt",
            "fragment_count",
            "genre",
            "slug",
            "title",
            "year",
        ]
