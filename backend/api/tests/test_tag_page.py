from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import ContentKind, Note, Status, Tag, Typescript, Work
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


def published_tag(**kwargs: Any) -> Tag:
    return TagFactory.create(status=PUBLISHED, **kwargs)


def published_work(year: int | None = 1947, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    if year is not None:
        EditionFactory.create(work=work, year=year)
    return work


def published_typescript(work: Work, **kwargs: Any) -> Typescript:
    document = DocumentFactory.create(ocr=True, text=TEXT, page_offsets=[0, 29, 56])
    options = {"status": PUBLISHED, "document": document, **kwargs}
    return TypescriptFactory.create(work=work, **options)


def text_note(work: Work, **kwargs: Any) -> Note:
    options = {
        "status": PUBLISHED,
        "content_kind": ContentKind.PLAIN_TEXT,
        "external_url": "",
        "document": DocumentFactory.create(text=TEXT),
        **kwargs,
    }
    note = NoteFactory.create(**options)
    note.works.add(work)
    return note


def page(client: Client, tag: Tag) -> dict[str, Any]:
    response = client.get(reverse("tag", args=[tag.slug]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestTagPageEndpoint:
    def test_us_ra_07_ac1_the_hero_has_occurrences_title_and_description(
        self, client: Client
    ) -> None:
        # Arrange: two fragments in one work, a note in another, one draft carrier.
        tag = published_tag(
            title="Dezerter", slug="dezerter", description="<p>Postać dezertera.</p>"
        )
        typescript = published_typescript(published_work(1947), is_main=True)
        FragmentFactory.create(document=typescript.document, start=0, end=8).tags.add(tag)
        FragmentFactory.create(document=typescript.document, start=9, end=15).tags.add(tag)
        note = NoteFactory.create(status=PUBLISHED)
        note.works.add(published_work(1954))
        note.tags.add(tag)
        NoteFactory.create().tags.add(tag)

        # Act
        result = page(client, tag)

        # Assert: the page counts the works from `works` ("w 2 utworach").
        assert result["slug"] == "dezerter"
        assert result["title"] == "Dezerter"
        assert result["description"] == "<p>Postać dezertera.</p>"
        assert result["occurrences"] == 3
        assert len(result["works"]) == 2

    def test_us_ra_07_ac2_works_by_first_edition_with_their_fragments_that_carry_the_tag(
        self, client: Client
    ) -> None:
        # Arrange
        tag = published_tag()
        late = published_work(1954, slug="czarny-potok", title="Czarny potok")
        early = published_work(1947, slug="wertepy", title="Wertepy")
        main = published_typescript(early, is_main=True)
        for start in (0, 9):
            FragmentFactory.create(document=main.document, start=start, end=start + 5).tags.add(tag)
        FragmentFactory.create(document=main.document, start=30, end=35)
        other = published_typescript(early)
        FragmentFactory.create(document=other.document).tags.add(tag)
        early.tags.add(tag)
        late.tags.add(tag)
        draft = WorkFactory.create()
        draft.tags.add(tag)

        # Act
        result = page(client, tag)

        # Assert: each work once; only the main typescript's fragments count (D19).
        assert result["works"] == [
            {"slug": "wertepy", "title": "Wertepy", "year": 1947, "fragment_count": 2},
            {"slug": "czarny-potok", "title": "Czarny potok", "year": 1954, "fragment_count": 0},
        ]

    def test_us_ra_07_ac3_every_visible_fragment_with_the_tag_by_work_then_position(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 1
        tag = published_tag(title="Dezerter", slug="dezerter")
        late = published_work(1954, title="Czarny potok")
        early = published_work(1947, title="Wertepy")
        late_main = published_typescript(late, is_main=True)
        early_main = published_typescript(
            early, is_main=True, institution=InstitutionFactory.create()
        )
        assert early_main.document is not None
        second = FragmentFactory.create(
            document=early_main.document, start=30, end=35, is_featured=True
        )
        first = FragmentFactory.create(
            document=early_main.document,
            start=0,
            end=8,
            location="rozdział I",
            shelfmark="1618.0009",
            description="Dezerter w stodole.",
        )
        third = FragmentFactory.create(document=late_main.document, start=9, end=15)
        note = text_note(early)
        note.works.add(late)
        in_note = FragmentFactory.create(document=note.document, start=0, end=8)
        for fragment in (second, first, third, in_note):
            fragment.tags.add(tag)
        first.tags.add(TagFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=early_main.document, start=56, end=63)
        hidden = published_typescript(early, status=Status.DRAFT)
        FragmentFactory.create(document=hidden.document).tags.add(tag)

        # Act
        result = page(client, tag)

        # Assert: every one, not a preview; the earliest work first, then position in its text.
        assert [item["id"] for item in result["fragments"]] == [
            first.pk,
            second.pk,
            in_note.pk,
            third.pk,
        ]
        assert result["fragments"][0] == {
            "id": first.pk,
            "url": f"/typescripts/{early_main.pk}?fragment={first.pk}",
            "source_type": "typescript",
            "work": "Wertepy",
            "number": 1,
            "location": "rozdział I",
            "quote": "Pierwsza",
            "scan": early_main.document.scan.url,
            "start_page": 1,
            "shelfmark": "ML, sygn. 1618.0009",
            "description": "Dezerter w stodole.",
            "tags": [{"slug": "dezerter", "title": "Dezerter"}],
        }
        assert result["fragments"][2]["url"] == f"/notes/{note.pk}?fragment={in_note.pk}"
        assert result["fragments"][2]["source_type"] == "note"
        assert result["fragments"][2]["work"] == "Wertepy, Czarny potok"
        assert result["fragments"][2]["scan"] == ""
        assert result["fragments"][2]["start_page"] is None

    def test_us_ra_07_ac3_notes_with_the_tag_on_the_note_or_on_a_fragment(
        self, client: Client
    ) -> None:
        # Arrange
        tag = published_tag(title="Dezerter", slug="dezerter")
        work = published_work()
        whole = NoteFactory.create(
            title="Notes 18 · karta 4",
            status=PUBLISHED,
            institution=InstitutionFactory.create(),
            shelfmark="1678.0104",
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="note.jpg"),
            image_alt="Karta z notesu",
        )
        whole.works.add(work)
        whole.tags.add(tag, published_tag(title="Wojna", slug="wojna"))
        whole.tags.add(TagFactory.create(status=Status.DRAFT))
        on_fragment = text_note(work, title="Brulion")
        FragmentFactory.create(document=on_fragment.document, start=0, end=8).tags.add(tag)
        FragmentFactory.create(document=on_fragment.document, start=9, end=15).tags.add(tag)
        NoteFactory.create(title="Szkic").tags.add(tag)
        NoteFactory.create(status=PUBLISHED)

        # Act
        result = page(client, tag)

        # Assert: each once, by title, with the note's own tags.
        assert [note["title"] for note in result["notes"]] == ["Brulion", "Notes 18 · karta 4"]
        card = result["notes"][1]
        assert card["url"] == whole.get_absolute_url()
        assert card["shelfmark"] == "ML, sygn. 1678.0104"
        assert card["image"].endswith(".jpg")
        assert card["image_alt"] == "Karta z notesu"
        assert card["tags"] == [
            {"slug": "dezerter", "title": "Dezerter"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_us_ra_07_ac4_related_tags_both_ways_published_only_by_name(
        self, client: Client
    ) -> None:
        # Arrange
        tag = published_tag()
        wojna = published_tag(title="Wojna", slug="wojna")
        las = published_tag(title="Las", slug="las")
        tag.related.add(wojna, TagFactory.create(status=Status.DRAFT))
        las.related.add(tag)
        published_tag().related.add(published_tag())

        # Act
        result = page(client, tag)

        # Assert
        assert result["related"] == [
            {"slug": "las", "title": "Las"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_us_ra_07_ac5_a_tag_refers_to_a_work_through_every_carrier(
        self, client: Client
    ) -> None:
        # Arrange: one work per way of referring to it.
        tag = published_tag()
        works = [published_work(1940 + n, title=f"Utwór {n}") for n in range(8)]
        works[0].tags.add(tag)
        typescript = published_typescript(works[1])
        typescript.tags.add(tag)
        FragmentFactory.create(document=published_typescript(works[2]).document).tags.add(tag)
        text_note(works[3]).tags.add(tag)
        FragmentFactory.create(document=text_note(works[4]).document).tags.add(tag)
        review = SecondaryTextFactory.create(status=PUBLISHED)
        review.tags.add(tag)
        SecondaryTextWorkLinkFactory.create(secondary_text=review, work=works[5])
        MaterialWorkLinkFactory.create(material__status=PUBLISHED, work=works[6]).tags.add(tag)
        SecondaryTextWorkLinkFactory.create(
            secondary_text__status=PUBLISHED, work=works[7]
        ).tags.add(tag)
        TypescriptFactory.create(work=published_work()).tags.add(tag)
        SecondaryTextWorkLinkFactory.create(work=published_work()).tags.add(tag)

        # Act
        result = page(client, tag)

        # Assert: drafts refer to nothing.
        assert [work["title"] for work in result["works"]] == [work.title for work in works]

    def test_us_ra_07_ac6_materials_with_the_tag_on_the_item_a_fragment_or_a_work_link(
        self, client: Client
    ) -> None:
        # Arrange
        tag = published_tag()
        work = published_work()
        whole = SecondaryTextFactory.create(title="Recenzja", status=PUBLISHED)
        whole.tags.add(tag, published_tag())
        SecondaryTextWorkLinkFactory.create(secondary_text=whole, work=work).tags.add(tag)
        on_fragment = SecondaryTextFactory.create(title="List", status=PUBLISHED)
        FragmentFactory.create(document=on_fragment.document).tags.add(tag)
        on_link = SecondaryTextFactory.create(title="Studium", status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=on_link, work=work).tags.add(tag)
        photo = ContextualMaterialFactory.create(
            title="Zdjęcie",
            status=PUBLISHED,
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="photo.jpg"),
            image_alt="Autor przy biurku",
        )
        MaterialWorkLinkFactory.create(material=photo, work=work).tags.add(tag)
        film = ContextualMaterialFactory.create(title="Film", status=PUBLISHED)
        film.tags.add(tag)
        SecondaryTextFactory.create(title="Szkic").tags.add(tag)
        to_draft = SecondaryTextFactory.create(title="Do szkicu", status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=to_draft, work=WorkFactory.create())
        to_draft.work_links.get().tags.add(tag)
        SecondaryTextFactory.create(status=PUBLISHED)

        # Act
        result = page(client, tag)

        # Assert: each once; a link to a draft work carries nothing.
        assert [item["title"] for item in result["materials"]["texts"]] == [
            "Film",
            "List",
            "Recenzja",
            "Studium",
        ]
        assert [item["title"] for item in result["materials"]["visuals"]] == ["Zdjęcie"]

    def test_r_06_a_draft_tag_is_not_found(self, client: Client) -> None:
        # Arrange
        tag = TagFactory.create(status=Status.DRAFT)

        # Act
        response = client.get(reverse("tag", args=[tag.slug]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_tag_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("tag", args=[published_tag().slug])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_tag_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        tag = published_tag()
        institution = InstitutionFactory.create()

        def add_related() -> None:
            work = published_work()
            main = published_typescript(work, is_main=True, institution=institution)
            FragmentFactory.create(document=main.document).tags.add(tag, published_tag())
            note = text_note(work, institution=institution)
            note.tags.add(tag, published_tag())
            FragmentFactory.create(document=note.document).tags.add(tag)
            text = SecondaryTextFactory.create(status=PUBLISHED)
            SecondaryTextWorkLinkFactory.create(secondary_text=text, work=work).tags.add(tag)
            FragmentFactory.create(document=text.document).tags.add(tag)
            material = ContextualMaterialFactory.create(status=PUBLISHED)
            MaterialWorkLinkFactory.create(material=material, work=work).tags.add(tag)
            tag.related.add(published_tag())

        add_related()
        page(client, tag)
        with django_assert_num_queries(13) as before:
            page(client, tag)
        for _ in range(4):
            add_related()

        # Act & Assert
        with django_assert_num_queries(len(before.captured_queries)):
            result = page(client, tag)

        assert len(result["fragments"]) == 15


class TestTagPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["TagPage"]["required"]) == sorted(
            (
                "slug",
                "title",
                "description",
                "occurrences",
                "works",
                "fragments",
                "notes",
                "related",
                "materials",
            )
        )
