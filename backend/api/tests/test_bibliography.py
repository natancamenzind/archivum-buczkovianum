"""The work's bibliography page endpoint (US-RA-21)."""

from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import Status, Work
from archive.tests.factories import BibliographyEntryFactory, EditionFactory, WorkFactory

PUBLISHED = Status.PUBLISHED


def work_with_bibliography(
    year: int | None = 1947, entries: int = 1, status: Status = PUBLISHED, **kwargs: Any
) -> Work:
    work = WorkFactory.create(status=status, **kwargs)
    if year is not None:
        EditionFactory.create(work=work, year=year)
    for number in range(1, entries + 1):
        BibliographyEntryFactory.create(work=work, text=f"{work.title} {number}", order=number)
    return work


def url(work: Work) -> str:
    return reverse("work-bibliography", args=[work.slug])


def page(client: Client, work: Work) -> dict[str, Any]:
    response = client.get(url(work))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestBibliographyPageEndpoint:
    def test_us_ra_21_ac2_names_the_work(self, client: Client) -> None:
        # Arrange
        work = work_with_bibliography(slug="wertepy", title="Wertepy")

        # Act
        result = page(client, work)

        # Assert
        assert (result["slug"], result["title"], result["is_draft"]) == (
            "wertepy",
            "Wertepy",
            False,
        )

    def test_us_ra_21_ac3_every_entry_in_the_order_the_editor_set(self, client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        for text, order in (("Trzecia", 3), ("Pierwsza", 1), ("Druga", 2)):
            BibliographyEntryFactory.create(work=work, text=text, order=order)
        for number in range(4, 13):
            BibliographyEntryFactory.create(work=work, text=f"Pozycja {number}", order=number)

        # Act
        result = page(client, work)

        # Assert
        assert result["entries"] == [
            "Pierwsza",
            "Druga",
            "Trzecia",
            *(f"Pozycja {number}" for number in range(4, 13)),
        ]

    def test_us_ra_21_ac4_published_works_with_a_bibliography_by_first_edition(
        self, client: Client
    ) -> None:
        # Arrange
        wertepy = work_with_bibliography(1947, slug="wertepy", title="Wertepy")
        work_with_bibliography(1958, slug="pamiec", title="Pamięć")
        work_with_bibliography(1932, slug="czarny-potok", title="Czarny potok")
        work_with_bibliography(None, slug="bez-wydan", title="Bez wydań")
        work_with_bibliography(1940, entries=0, slug="pusty", title="Pusty")
        work_with_bibliography(1941, status=Status.DRAFT, slug="szkic", title="Szkic")

        # Act
        result = page(client, wertepy)

        # Assert
        assert result["works"] == [
            {"slug": "czarny-potok", "title": "Czarny potok", "year": 1932},
            {"slug": "wertepy", "title": "Wertepy", "year": 1947},
            {"slug": "pamiec", "title": "Pamięć", "year": 1958},
            {"slug": "bez-wydan", "title": "Bez wydań", "year": None},
        ]

    def test_us_ra_21_ac5_a_work_without_entries_has_no_bibliography_page(
        self, client: Client
    ) -> None:
        # Arrange
        work = work_with_bibliography(entries=0)

        # Act
        response = client.get(url(work))

        # Assert
        assert response.status_code == 404

    def test_us_ra_21_ac5_a_draft_works_bibliography_is_not_found(self, client: Client) -> None:
        # Arrange
        work = work_with_bibliography(status=Status.DRAFT)

        # Act
        response = client.get(url(work))

        # Assert
        assert response.status_code == 404

    def test_us_ra_21_ac5_staff_previews_a_draft_works_bibliography(self, client: Client) -> None:
        # Arrange
        work = work_with_bibliography(status=Status.DRAFT)
        client.force_login(User.objects.create_user(username="editor", is_staff=True))

        # Act
        result = page(client, work)

        # Assert
        assert result["is_draft"] is True
        assert work.slug not in [item["slug"] for item in result["works"]]

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_bibliography_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        work = work_with_bibliography()

        # Act
        response = getattr(client, method)(url(work))

        # Assert
        assert response.status_code == 405

    def test_performance_bibliography_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        work = work_with_bibliography(entries=2)
        work_with_bibliography()
        with django_assert_num_queries(3) as before:
            page(client, work)
        for _ in range(5):
            BibliographyEntryFactory.create(work=work)
            work_with_bibliography(entries=3)

        # Act & Assert
        with django_assert_num_queries(len(before.captured_queries)):
            result = page(client, work)

        assert len(result["works"]) == 7


class TestBibliographyPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        schema_url = reverse("schema")

        # Act
        schemas = client.get(schema_url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        for name, fields in (
            ("BibliographyPage", ("slug", "is_draft", "title", "entries", "works")),
            ("BibliographyWork", ("slug", "title", "year")),
        ):
            assert set(schemas[name]["required"]) == set(fields), name
