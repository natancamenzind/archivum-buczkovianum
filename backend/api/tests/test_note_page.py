from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import ContentKind, Note, Status, Work
from archive.tests.factories import (
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    NoteFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def published_work(year: int, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    EditionFactory.create(work=work, year=year)
    return work


def published_note(**kwargs: Any) -> Note:
    return NoteFactory.create(status=PUBLISHED, **kwargs)


def text_note(**kwargs: Any) -> Note:
    return published_note(
        content_kind=ContentKind.PLAIN_TEXT,
        external_url="",
        document=DocumentFactory.create(),
        **kwargs,
    )


def page(client: Client, note: Note) -> dict[str, Any]:
    response = client.get(reverse("note", args=[note.pk]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestNotePageEndpoint:
    def test_us_ra_11_ac1_the_hero_has_shelfmark_title_and_description(
        self, client: Client
    ) -> None:
        # Arrange
        note = published_note(
            title="Notes 18 · karta 4",
            description="<p>Notatka o dezerterze.</p>",
            institution=InstitutionFactory.create(abbreviation="ML"),
            shelfmark="1678.0104",
        )

        # Act
        result = page(client, note)

        # Assert
        assert result["id"] == note.pk
        assert result["title"] == "Notes 18 · karta 4"
        assert result["description"] == "<p>Notatka o dezerterze.</p>"
        assert result["shelfmark"] == "ML, sygn. 1678.0104"

    def test_us_ra_11_ac1_a_note_without_a_shelfmark_has_none(self, client: Client) -> None:
        # Arrange
        note = published_note()

        # Act
        result = page(client, note)

        # Assert
        assert (result["shelfmark"], result["description"]) == ("", "")

    def test_us_ra_11_ac2_related_works_by_first_edition(self, client: Client) -> None:
        # Arrange
        note = published_note()
        later = published_work(1966, slug="pierwsza-swietnosc", title="Pierwsza świetność")
        earlier = published_work(1947, slug="wertepy", title="Wertepy")
        note.works.add(later, earlier, WorkFactory.create(status=Status.DRAFT))
        published_work(1954)

        # Act
        result = page(client, note)

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

    def test_us_ra_11_ac3_an_image_note_gives_its_image(self, client: Client) -> None:
        # Arrange
        note = published_note(
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="card.jpg"),
            image_alt="Karta z notesu",
        )

        # Act
        result = page(client, note)

        # Assert
        assert result["content"] == {
            "kind": "image",
            "image": note.image.url,
            "image_alt": "Karta z notesu",
            "file": "",
            "external_url": "",
            "document": None,
        }

    def test_us_ra_11_ac3_a_document_note_gives_its_file(self, client: Client) -> None:
        # Arrange
        note = published_note(
            content_kind=ContentKind.DOCUMENT,
            external_url="",
            file=ContentFile(b"%PDF-1.4", name="notes.pdf"),
        )

        # Act
        result = page(client, note)

        # Assert
        assert result["content"]["kind"] == "document"
        assert result["content"]["file"] == note.file.url
        assert result["content"]["image"] == ""

    def test_us_ra_11_ac3_an_external_media_note_gives_its_link(self, client: Client) -> None:
        # Arrange
        note = published_note(external_url="https://www.youtube.com/watch?v=abc")

        # Act
        result = page(client, note)

        # Assert
        assert result["content"]["kind"] == "external_media"
        assert result["content"]["external_url"] == "https://www.youtube.com/watch?v=abc"
        assert result["content"]["document"] is None

    def test_us_ra_11_ac3_a_text_note_gives_the_reader_its_document(self, client: Client) -> None:
        # Arrange
        note = text_note()

        # Act
        result = page(client, note)

        # Assert
        assert result["content"]["kind"] == "plain_text"
        assert result["content"]["document"] == note.document_id

    def test_us_ra_11_ac3_related_fragments_preview_as_fragment_cards(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 2
        tag = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        note = text_note()
        FragmentFactory.create(document=note.document).tags.add(tag)
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
        result = page(client, note)

        # Assert: the note's own fragments are not typescript fragments; no "all" link, so
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

    def test_us_ra_11_ac3_a_note_without_a_text_relates_by_its_own_tags(
        self, client: Client
    ) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        note = published_note()
        note.tags.add(tag)
        typescript = TypescriptFactory.create(work=published_work(1947), status=PUBLISHED)
        related = FragmentFactory.create(document=typescript.document)
        related.tags.add(tag)
        FragmentFactory.create(document=typescript.document).tags.add(
            TagFactory.create(status=PUBLISHED)
        )

        # Act
        result = page(client, note)

        # Assert
        assert [card["id"] for card in result["fragments"]["items"]] == [related.pk]

    def test_us_ra_11_ac4_tags_on_the_note_and_its_fragments(self, client: Client) -> None:
        # Arrange
        note = text_note()
        pamiec = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        wojna = TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED)
        note.tags.add(pamiec, TagFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=note.document).tags.add(wojna, pamiec)
        text_note().tags.add(TagFactory.create(title="Inny", status=PUBLISHED))
        TagFactory.create(title="Bez wystąpień", status=PUBLISHED)

        # Act
        result = page(client, note)

        # Assert: alphabetical, each once, draft tags never.
        assert result["tags"] == [
            {"slug": "pamiec", "title": "Pamięć"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_us_ra_11_ac4_a_note_without_a_text_has_only_its_own_tags(self, client: Client) -> None:
        # Arrange
        note = published_note()
        own = TagFactory.create(title="Nagranie", slug="nagranie", status=PUBLISHED)
        note.tags.add(own)
        TagFactory.create(title="Bez wystąpień", status=PUBLISHED)

        # Act
        result = page(client, note)

        # Assert
        assert result["tags"] == [{"slug": "nagranie", "title": "Nagranie"}]

    def test_r_06_a_draft_note_is_not_found(self, client: Client) -> None:
        # Arrange
        note = NoteFactory.create(status=Status.DRAFT)

        # Act
        response = client.get(reverse("note", args=[note.pk]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_note_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("note", args=[published_note().pk])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_note_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        note = text_note()
        institution = InstitutionFactory.create()

        def add_related() -> None:
            tag = TagFactory.create(status=PUBLISHED)
            note.tags.add(tag)
            FragmentFactory.create(document=note.document).tags.add(tag)
            work = published_work(1947)
            note.works.add(work)
            typescript = TypescriptFactory.create(
                work=work, status=PUBLISHED, institution=institution
            )
            FragmentFactory.create(document=typescript.document).tags.add(tag)

        for _ in range(2):
            add_related()
        page(client, note)
        with django_assert_num_queries(8):
            page(client, note)
        for _ in range(4):
            add_related()

        # Act & Assert
        with django_assert_num_queries(8):
            result = page(client, note)

        assert len(result["works"]) == 6
        assert result["fragments"]["total"] == 6


class TestNotePageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["NotePage"]["required"]) == sorted(
            ("id", "title", "description", "shelfmark", "content", "works", "fragments", "tags")
        )
        assert sorted(schemas["MediaContent"]["required"]) == sorted(
            ("kind", "image", "image_alt", "file", "external_url", "document")
        )
