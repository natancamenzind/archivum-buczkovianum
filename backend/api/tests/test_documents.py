from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries

from archive.models import Document, Status
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    InstitutionFactory,
    NoteFactory,
    TagFactory,
    TypescriptFactory,
)

PUBLISHED = Status.PUBLISHED
TEXT = "Pierwsza strona. Druga strona. Trzecia strona."


def ocr_document(status: str = PUBLISHED, **typescript: Any) -> Document:
    document = DocumentFactory.create(ocr=True, text=TEXT, page_offsets=[0, 17, 31])
    TypescriptFactory.create(document=document, status=status, **typescript)
    return document


def payload(client: Client, document: Document) -> dict[str, Any]:
    response = client.get(reverse("document", args=[document.pk]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestDocumentEndpoint:
    def test_us_ra_08_ac3_the_reader_gets_text_pages_and_scan(self, client: Client) -> None:
        # Arrange
        document = ocr_document()

        # Act
        result = payload(client, document)

        # Assert
        assert result["id"] == document.pk
        assert result["kind"] == "ocr"
        assert result["text"] == TEXT
        assert result["page_offsets"] == [0, 17, 31]
        assert result["scan"].endswith(".pdf")
        assert result["fragments"] == []

    def test_r_11_fragments_in_text_order_with_number_page_and_published_tags(
        self, client: Client
    ) -> None:
        # Arrange
        document = ocr_document(institution=InstitutionFactory.create())
        second = FragmentFactory.create(
            document=document, start=20, end=25, location="rozdział II", shelfmark="1618.0019"
        )
        first = FragmentFactory.create(document=document, start=0, end=8)
        wies = TagFactory.create(title="Wieś", slug="wies", status=PUBLISHED)
        second.tags.add(TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED), wies)
        second.tags.add(TagFactory.create(title="Szkic", status=Status.DRAFT))

        # Act
        result = payload(client, document)

        # Assert
        assert result["fragments"] == [
            {
                "id": first.pk,
                "start": 0,
                "end": 8,
                "number": 1,
                "start_page": 1,
                "location": "",
                "shelfmark": "",
                "tags": [],
            },
            {
                "id": second.pk,
                "start": 20,
                "end": 25,
                "number": 2,
                "start_page": 2,
                "location": "rozdział II",
                "shelfmark": "ML, sygn. 1618.0019",
                "tags": [{"slug": "wies", "title": "Wieś"}, {"slug": "wojna", "title": "Wojna"}],
            },
        ]

    def test_r_11_a_plain_text_has_no_scan_or_pages(self, client: Client) -> None:
        # Arrange
        document = DocumentFactory.create(text="Notatka.")
        NoteFactory.create(
            status=PUBLISHED, content_kind="plain_text", external_url="", document=document
        )
        FragmentFactory.create(document=document, start=0, end=7)

        # Act
        result = payload(client, document)

        # Assert
        assert result["kind"] == "plain"
        assert result["scan"] == ""
        assert result["page_offsets"] == []
        assert result["fragments"][0]["start_page"] is None

    def test_r_06_the_text_of_a_draft_is_not_found(self, client: Client) -> None:
        # Arrange
        document = ocr_document(status=Status.DRAFT)

        # Act
        response = client.get(reverse("document", args=[document.pk]))

        # Assert
        assert response.status_code == 404

    def test_r_06_a_text_without_an_owner_is_not_found(self, client: Client) -> None:
        # Arrange
        document = DocumentFactory.create()

        # Act
        response = client.get(reverse("document", args=[document.pk]))

        # Assert
        assert response.status_code == 404

    def test_performance_document_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        document = ocr_document(institution=InstitutionFactory.create())

        def add_fragment() -> None:
            fragment = FragmentFactory.create(document=document, start=0, end=5)
            fragment.tags.add(TagFactory.create(status=PUBLISHED))

        add_fragment()
        with django_assert_num_queries(5):
            payload(client, document)
        for _ in range(5):
            add_fragment()

        # Act & Assert
        with django_assert_num_queries(5):
            result = payload(client, document)

        assert len(result["fragments"]) == 6


class TestDocumentSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["Document"]["required"]) == sorted(
            ("id", "kind", "text", "page_offsets", "scan", "fragments")
        )
        assert sorted(schemas["DocumentFragment"]["required"]) == sorted(
            ("id", "start", "end", "number", "start_page", "location", "shelfmark", "tags")
        )
