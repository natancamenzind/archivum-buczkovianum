from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import ContentKind, ContextualMaterial, Status, Work
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    MaterialWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def published_work(year: int, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, **kwargs)
    EditionFactory.create(work=work, year=year)
    return work


def published_material(**kwargs: Any) -> ContextualMaterial:
    return ContextualMaterialFactory.create(status=PUBLISHED, **kwargs)


def text_material(**kwargs: Any) -> ContextualMaterial:
    return published_material(
        content_kind=ContentKind.OCR_TEXT,
        external_url="",
        document=DocumentFactory.create(),
        **kwargs,
    )


def page(client: Client, material: ContextualMaterial) -> dict[str, Any]:
    response = client.get(reverse("material", args=[material.pk]))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestMaterialPageEndpoint:
    def test_us_ra_12_ac1_the_hero_has_kind_shelfmark_title_and_description(
        self, client: Client
    ) -> None:
        # Arrange
        material = published_material(
            title="Wycinek z „Odrodzenia”",
            description="<p>Recenzja z 1947 roku.</p>",
            institution=InstitutionFactory.create(abbreviation="ML"),
            shelfmark="1700",
        )

        # Act
        result = page(client, material)

        # Assert: the type line's kind is the content's kind.
        assert result["id"] == material.pk
        assert result["title"] == "Wycinek z „Odrodzenia”"
        assert result["description"] == "<p>Recenzja z 1947 roku.</p>"
        assert result["shelfmark"] == "ML, sygn. 1700"
        assert result["content"]["kind"] == "external_media"

    def test_us_ra_12_ac1_a_material_without_a_shelfmark_has_none(self, client: Client) -> None:
        # Arrange
        material = published_material()

        # Act
        result = page(client, material)

        # Assert
        assert (result["shelfmark"], result["description"]) == ("", "")

    def test_us_ra_12_ac2_related_works_by_first_edition(self, client: Client) -> None:
        # Arrange
        material = published_material()
        later = published_work(1966, slug="pierwsza-swietnosc", title="Pierwsza świetność")
        earlier = published_work(1947, slug="wertepy", title="Wertepy")
        for work in (later, earlier, WorkFactory.create(status=Status.DRAFT)):
            MaterialWorkLinkFactory.create(material=material, work=work)
        published_work(1954)

        # Act
        result = page(client, material)

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

    def test_us_ra_12_ac3_an_image_material_gives_its_image(self, client: Client) -> None:
        # Arrange
        material = published_material(
            content_kind=ContentKind.IMAGE,
            external_url="",
            image=ContentFile(b"image", name="photo.jpg"),
            image_alt="Buczkowski w Konstancinie",
        )

        # Act
        result = page(client, material)

        # Assert
        assert result["content"] == {
            "kind": "image",
            "image": material.image.url,
            "image_alt": "Buczkowski w Konstancinie",
            "file": "",
            "external_url": "",
            "document": None,
        }

    def test_us_ra_12_ac3_a_document_material_gives_its_file(self, client: Client) -> None:
        # Arrange
        material = published_material(
            content_kind=ContentKind.DOCUMENT,
            external_url="",
            file=ContentFile(b"%PDF-1.4", name="clipping.pdf"),
        )

        # Act
        result = page(client, material)

        # Assert
        assert result["content"]["kind"] == "document"
        assert result["content"]["file"] == material.file.url

    def test_us_ra_12_ac3_an_external_media_material_gives_its_link(self, client: Client) -> None:
        # Arrange
        material = published_material(external_url="https://vimeo.com/76979871")

        # Act
        result = page(client, material)

        # Assert
        assert result["content"]["kind"] == "external_media"
        assert result["content"]["external_url"] == "https://vimeo.com/76979871"

    def test_us_ra_12_ac3_a_text_material_gives_the_reader_its_document(
        self, client: Client
    ) -> None:
        # Arrange
        material = text_material()

        # Act
        result = page(client, material)

        # Assert
        assert result["content"]["kind"] == "ocr_text"
        assert result["content"]["document"] == material.document_id

    def test_us_ra_12_ac3_related_fragments_preview_as_fragment_cards(
        self, client: Client, settings: Settings
    ) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 2
        tag = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        material = text_material()
        FragmentFactory.create(document=material.document).tags.add(tag)
        work = published_work(1947, title="Wertepy")
        typescript = TypescriptFactory.create(
            work=work, status=PUBLISHED, institution=InstitutionFactory.create()
        )
        fragments = [
            FragmentFactory.create(document=typescript.document, start=start, end=start + 5)
            for start in (0, 6, 12)
        ]
        for fragment in fragments:
            fragment.tags.add(tag)
        FragmentFactory.create(document=typescript.document).tags.add(
            TagFactory.create(status=PUBLISHED)
        )

        # Act
        result = page(client, material)

        # Assert: the material's own fragment is not a typescript fragment; no "all" link, so
        # only the total (US-RA-10 AC3).
        assert result["fragments"]["total"] == 3
        first, second = result["fragments"]["items"]
        assert (first["id"], second["id"]) == (fragments[0].pk, fragments[1].pk)
        assert first["url"] == f"/typescripts/{typescript.pk}?fragment={fragments[0].pk}"
        assert first["work"] == "Wertepy"
        assert first["tags"] == [{"slug": "pamiec", "title": "Pamięć"}]

    def test_us_ra_12_ac4_tags_on_the_material_its_fragments_and_its_work_links(
        self, client: Client
    ) -> None:
        # Arrange
        material = text_material()
        pamiec = TagFactory.create(title="Pamięć", slug="pamiec", status=PUBLISHED)
        wojna = TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED)
        las = TagFactory.create(title="Las", slug="las", status=PUBLISHED)
        material.tags.add(pamiec, TagFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=material.document).tags.add(wojna, pamiec)
        link = MaterialWorkLinkFactory.create(material=material, work=published_work(1947))
        link.tags.add(las, TagFactory.create(status=Status.DRAFT))
        hidden = MaterialWorkLinkFactory.create(
            material=material, work=WorkFactory.create(status=Status.DRAFT)
        )
        hidden.tags.add(TagFactory.create(title="Ukryty", status=PUBLISHED))
        text_material().tags.add(TagFactory.create(title="Inny", status=PUBLISHED))
        TagFactory.create(title="Bez wystąpień", status=PUBLISHED)

        # Act
        result = page(client, material)

        # Assert: alphabetical, each once; draft tags never, nor those of a link to a draft work.
        assert result["tags"] == [
            {"slug": "las", "title": "Las"},
            {"slug": "pamiec", "title": "Pamięć"},
            {"slug": "wojna", "title": "Wojna"},
        ]

    def test_us_ra_12_ac4_a_material_without_a_text_has_its_own_and_link_tags(
        self, client: Client
    ) -> None:
        # Arrange
        material = published_material()
        material.tags.add(TagFactory.create(title="Film", slug="film", status=PUBLISHED))
        link = MaterialWorkLinkFactory.create(material=material, work=published_work(1947))
        link.tags.add(TagFactory.create(title="Las", slug="las", status=PUBLISHED))

        # Act
        result = page(client, material)

        # Assert
        assert result["tags"] == [
            {"slug": "film", "title": "Film"},
            {"slug": "las", "title": "Las"},
        ]

    def test_r_06_a_draft_material_is_not_found(self, client: Client) -> None:
        # Arrange
        material = ContextualMaterialFactory.create(status=Status.DRAFT)

        # Act
        response = client.get(reverse("material", args=[material.pk]))

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_material_page_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("material", args=[published_material().pk])

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_material_page_query_count_does_not_grow(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        material = text_material()
        institution = InstitutionFactory.create()

        def add_related() -> None:
            tag = TagFactory.create(status=PUBLISHED)
            material.tags.add(tag)
            FragmentFactory.create(document=material.document).tags.add(tag)
            work = published_work(1947)
            MaterialWorkLinkFactory.create(material=material, work=work).tags.add(tag)
            typescript = TypescriptFactory.create(
                work=work, status=PUBLISHED, institution=institution
            )
            FragmentFactory.create(document=typescript.document).tags.add(tag)

        for _ in range(2):
            add_related()
        page(client, material)
        with django_assert_num_queries(8):
            page(client, material)
        for _ in range(4):
            add_related()

        # Act & Assert
        with django_assert_num_queries(8):
            result = page(client, material)

        assert len(result["works"]) == 6
        assert result["fragments"]["total"] == 6


class TestMaterialPageSchema:
    def test_schema_marks_every_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["MaterialPage"]["required"]) == sorted(
            ("id", "title", "description", "shelfmark", "content", "works", "fragments", "tags")
        )
