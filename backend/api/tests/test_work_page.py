from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import ContentKind, Status, Typescript, Work
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED
TEXT = "Pierwsza strona maszynopisu. Druga strona maszynopisu. Trzecia strona."


def published_work(year: int | None = 1947, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    if year is not None:
        EditionFactory.create(work=work, year=year)
    return work


def published_typescript(work: Work, **kwargs: Any) -> Typescript:
    document = DocumentFactory.create(ocr=True, text=TEXT, page_offsets=[0, 29, 56])
    options = {"status": PUBLISHED, "document": document, **kwargs}
    return TypescriptFactory.create(work=work, **options)


def page(client: Client, work: Work) -> dict[str, Any]:
    response = client.get(reverse("work", args=[work.slug]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestWorkPageEndpoint:
    def test_us_ra_04_ac1_the_hero_has_year_of_first_edition_title_and_description(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work(
            1957, slug="wertepy", title="Wertepy", genre="powieść", description="<p>Powieść.</p>"
        )
        EditionFactory.create(work=work, year=1947)

        # Act
        result = page(client, work)

        # Assert
        assert result["slug"] == "wertepy"
        assert result["title"] == "Wertepy"
        assert result["description"] == "<p>Powieść.</p>"
        assert result["year"] == 1947

    def test_us_ra_04_ac1_a_work_without_editions_has_no_year(self, client: Client) -> None:
        # Arrange
        work = published_work(None)

        # Act
        result = page(client, work)

        # Assert
        assert result["year"] is None
        assert result["editions"] == []

    def test_us_ra_04_ac2_editions_by_year_with_publisher_and_place(self, client: Client) -> None:
        # Arrange
        work = published_work(None)
        EditionFactory.create(
            work=work, year=1973, publisher="Wydawnictwo Literackie", place="Kraków"
        )
        EditionFactory.create(work=work, year=1947, publisher="Gebethner i Wolff", place="Warszawa")

        # Act
        result = page(client, work)

        # Assert: the earliest comes first; the page labels it "pierwsze wydanie".
        assert result["editions"] == [
            {"year": 1947, "publisher": "Gebethner i Wolff", "place": "Warszawa"},
            {"year": 1973, "publisher": "Wydawnictwo Literackie", "place": "Kraków"},
        ]

    def test_us_ra_04_ac3_fragments_preview_of_the_main_typescript_as_fragment_cards(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 2
        work = published_work(title="Wertepy")
        main = published_typescript(
            work, is_main=True, institution=InstitutionFactory.create(), shelfmark="1618"
        )
        document = main.document
        assert document is not None
        epidemia = TagFactory.create(title="Epidemia", slug="epidemia", status=PUBLISHED)
        first = FragmentFactory.create(
            document=document,
            start=0,
            end=8,
            location="rozdział I",
            shelfmark="1618.0009",
            description="Grzybniak leczy chorych.",
        )
        first.tags.add(epidemia, TagFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=document, start=9, end=15)
        featured = FragmentFactory.create(document=document, start=30, end=35, is_featured=True)
        other = published_typescript(work)
        FragmentFactory.create(document=other.document)

        # Act
        result = page(client, work)

        # Assert: featured first, then text order (R-09); only the main typescript counts (D19).
        assert result["main_typescript"] == main.pk
        assert result["fragments"]["total"] == 3
        assert [item["id"] for item in result["fragments"]["items"]] == [featured.pk, first.pk]
        assert result["fragments"]["items"][1] == {
            "id": first.pk,
            "url": f"/typescripts/{main.pk}?fragment={first.pk}",
            "source_type": "typescript",
            "work": "Wertepy",
            "number": 1,
            "location": "rozdział I",
            "quote": "Pierwsza",
            "scan": document.scan.url,
            "start_page": 1,
            "shelfmark": "ML, sygn. 1618.0009",
            "description": "Grzybniak leczy chorych.",
            "tags": [{"slug": "epidemia", "title": "Epidemia"}],
        }
        assert result["fragments"]["items"][0]["start_page"] == 2

    def test_us_ra_04_ac3_no_fragments_without_a_published_main_typescript(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work()
        draft = published_typescript(work, is_main=True, status=Status.DRAFT)
        FragmentFactory.create(document=draft.document)
        other = published_typescript(work)
        FragmentFactory.create(document=other.document)

        # Act
        result = page(client, work)

        # Assert
        assert result["main_typescript"] is None
        assert result["fragments"] == {"items": [], "total": 0}

    def test_us_ra_04_ac3_typescripts_by_shelfmark_as_numbers(self, client: Client) -> None:
        # Arrange
        work = published_work()
        institution = InstitutionFactory.create()
        second = published_typescript(
            work, title="Druga wersja", institution=institution, shelfmark="1619"
        )
        first = published_typescript(
            work, title="Pierwsza wersja", institution=institution, shelfmark="999"
        )
        TypescriptFactory.create(work=work, title="Szkic", status=Status.DRAFT)
        published_typescript(published_work(), title="Inny utwór")

        # Act
        result = page(client, work)

        # Assert
        assert result["typescripts"] == [
            {"id": first.pk, "title": "Pierwsza wersja", "shelfmark": "ML, sygn. 999"},
            {"id": second.pk, "title": "Druga wersja", "shelfmark": "ML, sygn. 1619"},
        ]

    def test_us_ra_04_ac3_notes_as_note_cards(self, client: Client) -> None:
        # Arrange
        work = published_work()
        dezerter = TagFactory.create(title="Dezerter", slug="dezerter", status=PUBLISHED)
        note = NoteFactory.create(
            title="Notes 18 · karta 4",
            description="<p>Notatka o dezerterze.</p>",
            status=PUBLISHED,
            institution=InstitutionFactory.create(),
            shelfmark="1678.0104",
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="note.jpg"),
            image_alt="Karta z notesu",
        )
        note.works.add(work)
        note.tags.add(dezerter, TagFactory.create(status=Status.DRAFT))
        recording = NoteFactory.create(title="Nagranie", status=PUBLISHED)
        recording.works.add(work)
        NoteFactory.create(title="Szkic", status=Status.DRAFT).works.add(work)
        NoteFactory.create(status=PUBLISHED).works.add(published_work())

        # Act
        result = page(client, work)

        # Assert: by title; a note that is not an image has no image (the page shows the
        # placeholder).
        [recording_card, note_card] = result["notes"]
        assert recording_card == {
            "url": recording.get_absolute_url(),
            "title": "Nagranie",
            "shelfmark": "",
            "description": "",
            "image": "",
            "image_alt": "",
            "tags": [],
        }
        assert note_card["url"] == note.get_absolute_url()
        assert note_card["title"] == "Notes 18 · karta 4"
        assert note_card["shelfmark"] == "ML, sygn. 1678.0104"
        assert note_card["description"] == "<p>Notatka o dezerterze.</p>"
        assert note_card["image"].endswith(".jpg")
        assert note_card["image_alt"] == "Karta z notesu"
        assert note_card["tags"] == [{"slug": "dezerter", "title": "Dezerter"}]

    def test_us_ra_04_ac4_every_published_tag_that_refers_to_the_work(self, client: Client) -> None:
        # Arrange: one tag through each way of referring to a work (US-RA-07 AC5).
        work = published_work()
        tags = [
            TagFactory.create(title=f"Tag {n}", slug=f"tag-{n}", status=PUBLISHED) for n in range(8)
        ]
        work.tags.add(tags[0])
        typescript = published_typescript(work)
        typescript.tags.add(tags[1])
        FragmentFactory.create(document=typescript.document).tags.add(tags[2])
        note = NoteFactory.create(
            status=PUBLISHED,
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(),
        )
        note.works.add(work)
        FragmentFactory.create(document=note.document).tags.add(tags[3])
        review = SecondaryTextFactory.create(status=PUBLISHED)
        review.tags.add(tags[4])
        SecondaryTextWorkLinkFactory.create(secondary_text=review, work=work)
        material = ContextualMaterialFactory.create(status=PUBLISHED)
        material.tags.add(tags[5])
        MaterialWorkLinkFactory.create(material=material, work=work).tags.add(tags[6])
        SecondaryTextWorkLinkFactory.create(work=work, secondary_text__status=PUBLISHED).tags.add(
            tags[7]
        )

        # Act
        result = page(client, work)

        # Assert: relation tags included (US-RA-05), each once, by name.
        assert result["tags"] == [{"slug": tag.slug, "title": tag.title} for tag in tags]

    def test_us_ra_04_ac4_drafts_and_other_works_bring_no_tags(self, client: Client) -> None:
        # Arrange
        work = published_work()
        work.tags.add(TagFactory.create(status=Status.DRAFT))
        TypescriptFactory.create(work=work).tags.add(TagFactory.create(status=PUBLISHED))
        draft_note = NoteFactory.create()
        draft_note.works.add(work)
        draft_note.tags.add(TagFactory.create(status=PUBLISHED))
        SecondaryTextWorkLinkFactory.create(work=work).tags.add(TagFactory.create(status=PUBLISHED))
        published_work().tags.add(TagFactory.create(status=PUBLISHED))

        # Act
        result = page(client, work)

        # Assert
        assert result["tags"] == []

    def test_us_ra_05_ac1_tags_on_a_work_link_appear_in_the_tag_column(
        self, client: Client
    ) -> None:
        # Arrange: the linked items carry no tags of their own; only the links do.
        work = published_work()
        reception = TagFactory.create(title="Recepcja", slug="recepcja", status=PUBLISHED)
        polemic = TagFactory.create(title="Polemika", slug="polemika", status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(work=work, secondary_text__status=PUBLISHED).tags.add(
            reception, polemic
        )
        MaterialWorkLinkFactory.create(work=work, material__status=PUBLISHED).tags.add(reception)

        # Act
        result = page(client, work)

        # Assert: each tag once, by name, with the slug its tag page uses.
        assert result["tags"] == [
            {"slug": "polemika", "title": "Polemika"},
            {"slug": "recepcja", "title": "Recepcja"},
        ]
        assert reception.get_absolute_url() == "/tags/recepcja"

    def test_us_ra_05_ac1_links_to_drafts_or_other_works_bring_no_tags(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work()
        SecondaryTextWorkLinkFactory.create(work=work).tags.add(TagFactory.create(status=PUBLISHED))
        MaterialWorkLinkFactory.create(work=work).tags.add(TagFactory.create(status=PUBLISHED))
        SecondaryTextWorkLinkFactory.create(work=work, secondary_text__status=PUBLISHED).tags.add(
            TagFactory.create(status=Status.DRAFT)
        )
        MaterialWorkLinkFactory.create(work=published_work(), material__status=PUBLISHED).tags.add(
            TagFactory.create(status=PUBLISHED)
        )

        # Act
        result = page(client, work)

        # Assert
        assert result["tags"] == []

    def test_us_ra_04_ac5_contextual_materials_linked_to_the_work(self, client: Client) -> None:
        # Arrange
        work = published_work()
        review = SecondaryTextFactory.create(title="Recenzja", status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=review, work=work)
        photo = ContextualMaterialFactory.create(
            title="Zdjęcie",
            status=PUBLISHED,
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="photo.jpg"),
            image_alt="Autor przy biurku",
        )
        MaterialWorkLinkFactory.create(material=photo, work=work)
        draft = SecondaryTextFactory.create(status=Status.DRAFT)
        SecondaryTextWorkLinkFactory.create(secondary_text=draft, work=work)
        other = SecondaryTextFactory.create(status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=other, work=published_work())

        # Act
        result = page(client, work)

        # Assert
        assert [item["title"] for item in result["materials"]["texts"]] == ["Recenzja"]
        assert [item["title"] for item in result["materials"]["visuals"]] == ["Zdjęcie"]

    def test_r_06_a_draft_work_is_not_found(self, client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=Status.DRAFT)

        # Act
        response = client.get(reverse("work", args=[work.slug]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_work_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("work", args=[published_work().slug])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_work_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        work = published_work()
        institution = InstitutionFactory.create()
        main = published_typescript(work, is_main=True, institution=institution)

        def add_related() -> None:
            EditionFactory.create(work=work, year=1960)
            published_typescript(work, institution=institution)
            tag = TagFactory.create(status=PUBLISHED)
            FragmentFactory.create(document=main.document).tags.add(tag)
            note = NoteFactory.create(status=PUBLISHED, institution=institution)
            note.works.add(work)
            note.tags.add(tag)
            text = SecondaryTextFactory.create(status=PUBLISHED)
            SecondaryTextWorkLinkFactory.create(secondary_text=text, work=work).tags.add(tag)
            MaterialWorkLinkFactory.create(material__status=PUBLISHED, work=work)

        # The preview's fragments name their works with a query each, up to PREVIEW_LIMIT.
        add_related()
        add_related()
        page(client, work)
        with django_assert_num_queries(14) as before:
            page(client, work)
        for _ in range(4):
            add_related()

        # Act & Assert
        with django_assert_num_queries(len(before.captured_queries)):
            result = page(client, work)

        assert len(result["notes"]) == 6


class TestWorkPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        for name, fields in (
            (
                "WorkPage",
                (
                    "slug",
                    "title",
                    "description",
                    "year",
                    "editions",
                    "main_typescript",
                    "fragments",
                    "typescripts",
                    "notes",
                    "tags",
                    "materials",
                ),
            ),
            ("Edition", ("year", "publisher", "place")),
            (
                "FragmentCard",
                (
                    "id",
                    "url",
                    "source_type",
                    "work",
                    "number",
                    "location",
                    "quote",
                    "scan",
                    "start_page",
                    "shelfmark",
                    "description",
                    "tags",
                ),
            ),
            (
                "NoteCard",
                ("url", "title", "shelfmark", "description", "image", "image_alt", "tags"),
            ),
        ):
            assert sorted(schemas[name]["required"]) == sorted(fields)
