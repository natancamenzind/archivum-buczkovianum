from datetime import date
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import SecondaryText, Status, Work
from archive.tests.factories import (
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def published_work(year: int, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    EditionFactory.create(work=work, year=year)
    return work


def published_text(**kwargs: Any) -> SecondaryText:
    return SecondaryTextFactory.create(status=PUBLISHED, **kwargs)


def page(client: Client, text: SecondaryText) -> dict[str, Any]:
    response = client.get(reverse("secondary-text", args=[text.pk]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestSecondaryTextPageEndpoint:
    def test_us_ra_10_ac1_the_hero_has_kind_sender_date_title_and_description(
        self, client: Client
    ) -> None:
        # Arrange
        letter = published_text(
            title="List nr 32",
            description="<p>Transkrypcja listu.</p>",
            kind=SecondaryText.Kind.LETTER,
            sender="Leopold Buczkowski",
            letter_date=date(1947, 10, 1),
        )

        # Act
        result = page(client, letter)

        # Assert
        assert result["id"] == letter.pk
        assert result["title"] == "List nr 32"
        assert result["description"] == "<p>Transkrypcja listu.</p>"
        assert result["kind"] == "letter"
        assert result["sender"] == "Leopold Buczkowski"
        assert result["letter_date"] == "1947-10-01"

    def test_us_ra_10_ac1_a_text_without_a_date_has_none(self, client: Client) -> None:
        # Arrange
        review = published_text(kind=SecondaryText.Kind.REVIEW)

        # Act
        result = page(client, review)

        # Assert
        assert (result["kind"], result["sender"], result["letter_date"]) == ("review", "", None)

    def test_us_ra_10_ac2_related_works_by_first_edition(self, client: Client) -> None:
        # Arrange
        text = published_text()
        later = published_work(1966, slug="pierwsza-swietnosc", title="Pierwsza świetność")
        earlier = published_work(1947, slug="wertepy", title="Wertepy")
        for work in (later, earlier, WorkFactory.create(status=Status.DRAFT)):
            SecondaryTextWorkLinkFactory.create(secondary_text=text, work=work)
        published_work(1954)

        # Act
        result = page(client, text)

        # Assert: drafts are not listed (R-06).
        assert result["works"] == [
            {"slug": "wertepy", "title": "Wertepy", "year": 1947, "fragment_count": 0},
            {
                "slug": "pierwsza-swietnosc",
                "title": "Pierwsza świetność",
                "year": 1966,
                "fragment_count": 0,
            },
        ]

    def test_us_ra_10_ac3_the_reader_gets_the_document(self, client: Client) -> None:
        # Arrange
        text = published_text(document=DocumentFactory.create(ocr=True))

        # Act
        result = page(client, text)

        # Assert
        assert result["document"] == text.document_id

    def test_us_ra_10_ac3_related_fragments_preview_as_fragment_cards(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 2
        tag = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        text = published_text()
        FragmentFactory.create(document=text.document).tags.add(tag)
        work = published_work(1947, title="Wertepy")
        typescript = TypescriptFactory.create(
            work=work, status=PUBLISHED, institution=InstitutionFactory.create()
        )
        fragments = [
            FragmentFactory.create(
                document=typescript.document, start=start, end=start + 5, shelfmark="1618.0009"
            )
            for start in (0, 6, 12)
        ]
        for fragment in fragments:
            fragment.tags.add(tag)
        fragments[0].tags.add(TagFactory.create(status=Status.DRAFT))
        assert typescript.document is not None

        # Act
        result = page(client, text)

        # Assert: the text's own fragments are not typescript fragments; no "all" link, so
        # only the total (US-RA-10 AC3). A card's draft tag is not shown (R-06).
        assert result["fragments"]["total"] == 3
        first, second = result["fragments"]["items"]
        assert second["id"] == fragments[1].pk
        assert first == {
            "id": fragments[0].pk,
            "url": f"/typescripts/{typescript.pk}?fragment={fragments[0].pk}",
            "source_type": "typescript",
            "work": "Wertepy",
            "number": 1,
            "location": "",
            "quote": "Czarn",
            "scan": typescript.document.scan.url,
            "start_page": 1,
            "shelfmark": "ML, sygn. 1618.0009",
            "description": "",
            "tags": [{"slug": "pamiec", "title": "Pamięć"}],
        }

    def test_us_ra_10_ac4_tags_on_the_text_its_fragments_and_its_work_links(
        self, client: Client
    ) -> None:
        # Arrange
        text = published_text()
        pamiec = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        pisanie = TagFactory.create(title="Pisanie", slug="pisanie", status=PUBLISHED)
        wojna = TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED)
        text.tags.add(pamiec, TagFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=text.document).tags.add(wojna, pamiec)
        SecondaryTextWorkLinkFactory.create(
            secondary_text=text, work=published_work(1947)
        ).tags.add(pisanie)
        SecondaryTextWorkLinkFactory.create(
            secondary_text=text, work=WorkFactory.create(status=Status.DRAFT)
        ).tags.add(TagFactory.create(title="Szkic utworu", status=PUBLISHED))
        published_text().tags.add(TagFactory.create(title="Inny", status=PUBLISHED))

        # Act
        result = page(client, text)

        # Assert: alphabetical, each once, draft tags never; a link to a draft work brings none.
        assert result["tags"] == [
            {"slug": "pamiec", "title": "Pamięć"},
            {"slug": "pisanie", "title": "Pisanie"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_r_06_a_draft_secondary_text_is_not_found(self, client: Client) -> None:
        # Arrange
        text = SecondaryTextFactory.create(status=Status.DRAFT)

        # Act
        response = client.get(reverse("secondary-text", args=[text.pk]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_secondary_text_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("secondary-text", args=[published_text().pk])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_secondary_text_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        text = published_text()
        institution = InstitutionFactory.create()

        def add_related() -> None:
            tag = TagFactory.create(status=PUBLISHED)
            text.tags.add(tag)
            FragmentFactory.create(document=text.document).tags.add(tag)
            work = published_work(1947)
            SecondaryTextWorkLinkFactory.create(secondary_text=text, work=work).tags.add(tag)
            typescript = TypescriptFactory.create(
                work=work, status=PUBLISHED, institution=institution
            )
            FragmentFactory.create(document=typescript.document).tags.add(tag)

        for _ in range(2):
            add_related()
        page(client, text)
        with django_assert_num_queries(8):
            page(client, text)
        for _ in range(4):
            add_related()

        # Act & Assert: a full preview names each card's works with one query (FragmentCard).
        with django_assert_num_queries(8):
            result = page(client, text)

        assert len(result["works"]) == 6
        assert result["fragments"]["total"] == 6


class TestSecondaryTextPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["SecondaryTextPage"]["required"]) == sorted(
            (
                "id",
                "is_draft",
                "title",
                "description",
                "kind",
                "sender",
                "letter_date",
                "document",
                "works",
                "fragments",
                "tags",
            )
        )
