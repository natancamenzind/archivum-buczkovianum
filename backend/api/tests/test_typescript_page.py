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


def published_typescript(work: Work | None = None, **kwargs: Any) -> Typescript:
    document = DocumentFactory.create(ocr=True, text=TEXT, page_offsets=[0, 29, 56])
    options = {"status": PUBLISHED, "document": document, **kwargs}
    return TypescriptFactory.create(work=work or published_work(), **options)


def page(client: Client, typescript: Typescript) -> dict[str, Any]:
    response = client.get(reverse("typescript", args=[typescript.pk]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestTypescriptPageEndpoint:
    def test_us_ra_08_ac1_the_hero_has_title_description_shelfmark_and_year(
        self, client: Client
    ) -> None:
        # Arrange
        typescript = published_typescript(
            published_work(1947),
            title="Maszynopis „Wertepów”",
            description="<p>Pierwsza wersja.</p>",
            institution=InstitutionFactory.create(),
            shelfmark="1618",
        )

        # Act
        result = page(client, typescript)

        # Assert
        assert result["id"] == typescript.pk
        assert result["title"] == "Maszynopis „Wertepów”"
        assert result["description"] == "<p>Pierwsza wersja.</p>"
        assert result["shelfmark"] == "ML, sygn. 1618"
        assert result["work"]["year"] == 1947

    def test_us_ra_08_ac2_the_context_column_has_the_work_with_year_and_fragment_count(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work(1947, slug="wertepy", title="Wertepy")
        main = published_typescript(work, is_main=True)
        FragmentFactory.create_batch(3, document=main.document)
        other = published_typescript(work)

        # Act
        result = page(client, other)

        # Assert: the work's count is its main typescript's (D19), whichever page shows it.
        assert result["work"] == {
            "slug": "wertepy",
            "title": "Wertepy",
            "year": 1947,
            "fragment_count": 3,
        }

    def test_us_ra_08_ac2_a_draft_work_is_not_shown(self, client: Client) -> None:
        # Arrange
        typescript = published_typescript(WorkFactory.create(status=Status.DRAFT))

        # Act
        result = page(client, typescript)

        # Assert
        assert result["work"] is None

    def test_us_ra_08_ac2_the_work_s_typescripts_by_shelfmark_with_the_current_one(
        self, client: Client
    ) -> None:
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
        result = page(client, second)

        # Assert
        assert result["work_typescripts"] == [
            {"id": first.pk, "title": "Pierwsza wersja", "shelfmark": "ML, sygn. 999"},
            {"id": second.pk, "title": "Druga wersja", "shelfmark": "ML, sygn. 1619"},
        ]

    def test_us_ra_08_ac3_the_reader_gets_the_document_and_its_page_count(
        self, client: Client
    ) -> None:
        # Arrange
        typescript = published_typescript()

        # Act
        result = page(client, typescript)

        # Assert
        assert result["document"] == typescript.document_id
        assert result["page_count"] == 3

    def test_us_ra_08_ac3_the_fragments_preview_with_number_location_and_shelfmark(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 2
        typescript = published_typescript(institution=InstitutionFactory.create())
        document = typescript.document
        first = FragmentFactory.create(document=document, start=0, end=5, location="rozdział I")
        FragmentFactory.create(document=document, start=10, end=15)
        featured = FragmentFactory.create(
            document=document, start=30, end=35, shelfmark="1618.0019", is_featured=True
        )

        # Act
        result = page(client, typescript)

        # Assert: featured first, then text order (R-09); numbers count every fragment.
        assert result["fragments"] == {
            "items": [
                {
                    "id": featured.pk,
                    "number": 3,
                    "location": "",
                    "shelfmark": "ML, sygn. 1618.0019",
                },
                {"id": first.pk, "number": 1, "location": "rozdział I", "shelfmark": ""},
            ],
            "total": 3,
        }

    def test_us_ra_08_ac4_tags_on_the_typescript_and_its_fragments(self, client: Client) -> None:
        # Arrange
        typescript = published_typescript()
        wies = TagFactory.create(title="Wieś", slug="wies", status=PUBLISHED)
        wojna = TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED)
        draft = TagFactory.create(title="Szkic", status=Status.DRAFT)
        typescript.tags.add(wojna, draft)
        FragmentFactory.create(document=typescript.document).tags.add(wies, wojna)
        other = published_typescript()
        other.tags.add(TagFactory.create(title="Inny", status=PUBLISHED))

        # Act
        result = page(client, typescript)

        # Assert: alphabetical, each once, draft tags never (R-06).
        assert result["tags"] == [
            {"slug": "wies", "title": "Wieś"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_us_ra_08_ac5_contextual_materials_linked_to_its_work(self, client: Client) -> None:
        # Arrange
        work = published_work()
        typescript = published_typescript(work)
        institution = InstitutionFactory.create()
        review = SecondaryTextFactory.create(
            title="Recenzja",
            author="Jan Kowalski",
            source="Czytelnik, Warszawa 1948, s. 3",
            status=PUBLISHED,
        )
        SecondaryTextWorkLinkFactory.create(secondary_text=review, work=work)
        film = ContextualMaterialFactory.create(title="Film", status=PUBLISHED)
        MaterialWorkLinkFactory.create(material=film, work=work)
        photo = ContextualMaterialFactory.create(
            title="Zdjęcie",
            status=PUBLISHED,
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="photo.jpg"),
            image_alt="Autor przy biurku",
            institution=institution,
            shelfmark="1700",
        )
        MaterialWorkLinkFactory.create(material=photo, work=work)
        draft = SecondaryTextFactory.create(title="Szkic", status=Status.DRAFT)
        SecondaryTextWorkLinkFactory.create(secondary_text=draft, work=work)
        other = SecondaryTextFactory.create(title="Inny", status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=other, work=published_work())

        # Act
        result = page(client, typescript)

        # Assert: secondary texts and non-image materials by title; a material shows its title
        # only (D5).
        assert result["materials"]["texts"] == [
            {"url": film.get_absolute_url(), "author": "", "title": "Film", "publication": ""},
            {
                "url": review.get_absolute_url(),
                "author": "Jan Kowalski",
                "title": "Recenzja",
                "publication": "Czytelnik, Warszawa 1948, s. 3",
            },
        ]
        [visual] = result["materials"]["visuals"]
        assert visual["url"] == photo.get_absolute_url()
        assert visual["title"] == "Zdjęcie"
        assert visual["shelfmark"] == "ML, sygn. 1700"
        assert visual["image"].endswith(".jpg")
        assert visual["image_alt"] == "Autor przy biurku"

    def test_us_ra_08_ac5_a_visual_material_without_its_image_has_an_empty_one(
        self, client: Client
    ) -> None:
        # Arrange
        work = published_work()
        photo = ContextualMaterialFactory.create(
            status=PUBLISHED, content_kind=ContentKind.IMAGE, external_url=""
        )
        MaterialWorkLinkFactory.create(material=photo, work=work)

        # Act
        result = page(client, published_typescript(work))

        # Assert: the page shows the placeholder board (design/components/).
        assert result["materials"]["visuals"][0]["image"] == ""

    def test_us_ra_08_ac5_no_contextual_materials_under_a_draft_work(self, client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=Status.DRAFT)
        typescript = published_typescript(work)
        review = SecondaryTextFactory.create(status=PUBLISHED)
        SecondaryTextWorkLinkFactory.create(secondary_text=review, work=work)

        # Act
        result = page(client, typescript)

        # Assert
        assert result["materials"] == {"texts": [], "visuals": []}

    def test_r_06_a_draft_typescript_is_not_found(self, client: Client) -> None:
        # Arrange
        typescript = published_typescript(status=Status.DRAFT)

        # Act
        response = client.get(reverse("typescript", args=[typescript.pk]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_typescript_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("typescript", args=[published_typescript().pk])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_typescript_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        work = published_work()
        typescript = published_typescript(work, institution=InstitutionFactory.create())

        def add_related() -> None:
            published_typescript(work, institution=typescript.institution, shelfmark="1619")
            tag = TagFactory.create(status=PUBLISHED)
            FragmentFactory.create(document=typescript.document).tags.add(tag)
            text = SecondaryTextFactory.create(status=PUBLISHED, institution=typescript.institution)
            SecondaryTextWorkLinkFactory.create(secondary_text=text, work=work)
            material = ContextualMaterialFactory.create(status=PUBLISHED)
            MaterialWorkLinkFactory.create(material=material, work=work)

        add_related()
        page(client, typescript)
        with django_assert_num_queries(8):
            page(client, typescript)
        for _ in range(4):
            add_related()

        # Act & Assert
        with django_assert_num_queries(8):
            result = page(client, typescript)

        assert len(result["work_typescripts"]) == 6


class TestTypescriptPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["TypescriptPage"]["required"]) == sorted(
            (
                "id",
                "title",
                "description",
                "shelfmark",
                "document",
                "page_count",
                "work",
                "work_typescripts",
                "fragments",
                "tags",
                "materials",
            )
        )
        for name, fields in (
            ("FragmentRow", ("id", "number", "location", "shelfmark")),
            ("WorkSummary", ("slug", "title", "year", "fragment_count")),
            ("MaterialText", ("url", "author", "title", "publication")),
            ("VisualMaterial", ("url", "title", "shelfmark", "image", "image_alt")),
        ):
            assert sorted(schemas[name]["required"]) == sorted(fields)
