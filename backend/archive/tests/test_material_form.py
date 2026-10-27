"""The contextual material form: its fields, its content and its work links (US-WR-07)."""

from typing import TYPE_CHECKING, Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.utils import ErrorDict
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoCaptureOnCommitCallbacks

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

from archive.models import ContentKind, ContextualMaterial, Document, Fragment, Status, Work
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    FragmentFactory,
    InstitutionFactory,
    MaterialWorkLinkFactory,
    TagFactory,
    WorkFactory,
)
from archive.tests.files import ocr_file, scan_file
from search.models import EntityType
from search.query import search

ADD_URL = reverse("admin:archive_contextualmaterial_add")
LINKS = "work_links"


def change_url(material: ContextualMaterial) -> str:
    return reverse("admin:archive_contextualmaterial_change", args=[material.pk])


def links_data(*works: Work, initial: int = 0, ids: tuple[int, ...] = ()) -> dict[str, Any]:
    """The work links inline: one row per work, the first `initial` rows already stored."""
    data: dict[str, Any] = {
        f"{LINKS}-TOTAL_FORMS": len(works),
        f"{LINKS}-INITIAL_FORMS": initial,
        f"{LINKS}-MIN_NUM_FORMS": 1,
        f"{LINKS}-MAX_NUM_FORMS": 1000,
    }
    for index, work in enumerate(works):
        data[f"{LINKS}-{index}-work"] = work.pk
        if index < len(ids):
            data[f"{LINKS}-{index}-id"] = ids[index]
    return data


def form_data(*works: Work, **fields: Any) -> dict[str, Any]:
    """What the add form posts: a material linked to `works`, without content unless given."""
    return {
        "title": "Zdjęcie z Podola",
        "status": Status.DRAFT,
        "description": "",
        "shelfmark": "",
        "content_kind": "",
        "image_alt": "",
        "external_url": "",
        "plain_text": "",
        **links_data(*works),
        **fields,
    }


def material_data(material: ContextualMaterial, **fields: Any) -> dict[str, Any]:
    """What the change form of `material` posts as it is."""
    links = list(material.work_links.all())
    document = material.document
    stored = {
        "title": material.title,
        "status": material.status,
        "description": material.description,
        "shelfmark": material.shelfmark,
        "content_kind": material.content_kind,
        "image_alt": material.image_alt,
        "external_url": material.external_url,
        "plain_text": document.text if document and document.kind == Document.Kind.PLAIN else "",
        **links_data(
            *(link.work for link in links), initial=len(links), ids=tuple(link.pk for link in links)
        ),
    }
    return {**stored, **fields}


def form_errors(response: "_MonkeyPatchedWSGIResponse") -> ErrorDict:
    assert response.status_code == 200
    errors: ErrorDict = response.context["adminform"].form.errors
    return errors


def found(text: str) -> list[tuple[str, str]]:
    return [
        (hit.entry.entity_type, hit.entry.title)
        for group in search(text).groups
        for hit in group.hits
    ]


def image_file() -> SimpleUploadedFile:
    return SimpleUploadedFile("zdjecie.jpg", b"\xff\xd8\xff", content_type="image/jpeg")


@pytest.mark.django_db
class TestContextualMaterialForm:
    def test_us_wr_07_ac1_adds_a_material_with_its_fields(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        institution = InstitutionFactory.create()
        data = form_data(
            work,
            description="Fotografia wsi.",
            shelfmark="1702",
            institution=institution.pk,
            content_kind=ContentKind.EXTERNAL_MEDIA,
            external_url="https://example.com/film",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        material = ContextualMaterial.objects.get()
        assert (material.title, material.description, material.shelfmark) == (
            "Zdjęcie z Podola",
            "Fotografia wsi.",
            "1702",
        )
        assert material.institution == institution

    def test_us_wr_07_ac1_title_is_required_and_the_rest_is_optional(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, title="")

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        errors = form_errors(response)
        assert set(errors) == {"title", "content_kind"}
        assert not ContextualMaterial.objects.exists()

    def test_us_wr_07_ac2_image(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work, content_kind=ContentKind.IMAGE, image=image_file(), image_alt="Chata"
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        material = ContextualMaterial.objects.get()
        assert material.image.name and material.image.name.endswith(".jpg")
        assert material.document is None

    def test_us_wr_07_ac2_document_file(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, content_kind=ContentKind.DOCUMENT, file=scan_file(1))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        material = ContextualMaterial.objects.get()
        assert material.file.name and material.file.name.endswith(".pdf")

    def test_us_wr_07_ac2_external_link(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work, content_kind=ContentKind.EXTERNAL_MEDIA, external_url="youtube.com/watch?v=1"
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        assert ContextualMaterial.objects.get().external_url == "https://youtube.com/watch?v=1"

    def test_us_wr_07_ac2_ocr_text_from_scan_and_ocr_file(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.OCR_TEXT,
            scan=scan_file(2),
            ocr_file=ocr_file("Wieś. ", "Pole."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        document = ContextualMaterial.objects.get().document
        assert document is not None
        assert (document.kind, document.text, document.page_count) == (
            Document.Kind.OCR,
            "Wieś. Pole.",
            2,
        )

    def test_us_wr_07_ac2_ocr_text_requires_both_files(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, content_kind=ContentKind.OCR_TEXT)

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {
            "scan": ["To pole jest wymagane."],
            "ocr_file": ["To pole jest wymagane."],
        }
        assert not Document.objects.exists()

    def test_us_wr_07_ac2_ocr_text_checks_page_counts(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.OCR_TEXT,
            scan=scan_file(3),
            ocr_file=ocr_file("Jedna strona."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"ocr_file": ["Skan ma 3 strony, plik OCR ma 1."]}
        assert not ContextualMaterial.objects.exists()

    def test_us_wr_07_ac2_plain_text_entered_on_the_form(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work, content_kind=ContentKind.PLAIN_TEXT, plain_text="Drogi Panie,\r\nlist."
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        document = ContextualMaterial.objects.get().document
        assert document is not None
        assert (document.kind, document.text, document.scan.name) == (
            Document.Kind.PLAIN,
            "Drogi Panie,\nlist.",
            "",
        )

    def test_us_wr_07_ac2_plain_text_is_required_for_plain_text_content(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, content_kind=ContentKind.PLAIN_TEXT, plain_text="  ")

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"plain_text": ["To pole jest wymagane."]}
        assert not Document.objects.exists()

    def test_us_wr_07_ac2_text_given_for_another_kind_of_content_is_an_error(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.EXTERNAL_MEDIA,
            external_url="https://example.com/film",
            plain_text="Tekst.",
            scan=scan_file(1),
            ocr_file=ocr_file("Tekst."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        leave_empty = ["Przy tym rodzaju treści zostaw to pole puste."]
        assert form_errors(response) == {
            "plain_text": leave_empty,
            "scan": leave_empty,
            "ocr_file": leave_empty,
        }
        assert not Document.objects.exists()

    def test_us_wr_07_ac2_change_form_shows_the_plain_text(self, admin_client: Client) -> None:
        # Arrange
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(text="Drogi Panie."),
        )

        # Act
        response = admin_client.get(change_url(material))

        # Assert
        content = response.content.decode()
        assert 'name="document"' not in content
        assert "Drogi Panie.</textarea>" in content

    def test_us_wr_07_ac2_editing_plain_text_reanchors_fragments(
        self, admin_client: Client
    ) -> None:
        # Arrange: "Czarny potok płynie przez las."
        document = DocumentFactory.create()
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        in_place = FragmentFactory.create(document=document, start=0, end=12)
        moved = FragmentFactory.create(document=document, start=13, end=19)
        data = material_data(material, plain_text="Czarny potok. Nad lasem płynie.")

        # Act
        response = admin_client.post(change_url(material), data)

        # Assert
        assert response.status_code == 302
        material.refresh_from_db()
        assert material.document_id == document.pk
        in_place.refresh_from_db()
        moved.refresh_from_db()
        assert (in_place.start, in_place.needs_review) == (0, False)
        assert (moved.start, moved.needs_review) == (24, True)

    def test_us_wr_07_ac2_switching_ocr_text_to_plain_text_keeps_fragments(
        self,
        admin_client: Client,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        document = DocumentFactory.create(ocr=True)
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.OCR_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        fragment = FragmentFactory.create(document=document, start=0, end=12)
        storage, old_scan = document.scan.storage, document.scan.name
        assert old_scan and storage.exists(old_scan)
        data = material_data(
            material, content_kind=ContentKind.PLAIN_TEXT, plain_text="Czarny potok."
        )

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(material), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get(pk=document.pk)
        assert (stored.kind, stored.text, stored.scan.name, stored.page_offsets) == (
            Document.Kind.PLAIN,
            "Czarny potok.",
            "",
            [],
        )
        assert not storage.exists(old_scan)
        assert Fragment.objects.get(pk=fragment.pk).document_id == document.pk

    def test_us_wr_07_ac2_switching_plain_text_to_ocr_text(self, admin_client: Client) -> None:
        # Arrange
        document = DocumentFactory.create()
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        data = material_data(
            material,
            content_kind=ContentKind.OCR_TEXT,
            plain_text="",
            scan=scan_file(1),
            ocr_file=ocr_file("Nowy tekst."),
        )

        # Act
        response = admin_client.post(change_url(material), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get(pk=document.pk)
        assert (stored.kind, stored.text) == (Document.Kind.OCR, "Nowy tekst.")

    def test_us_wr_07_ac2_switching_plain_text_to_ocr_text_requires_files(
        self, admin_client: Client
    ) -> None:
        # Arrange
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=DocumentFactory.create()
        )
        MaterialWorkLinkFactory.create(material=material)
        data = material_data(material, content_kind=ContentKind.OCR_TEXT, plain_text="")

        # Act
        response = admin_client.post(change_url(material), data)

        # Assert
        assert set(form_errors(response)) == {"scan", "ocr_file"}

    def test_us_wr_07_ac2_text_becomes_a_link_and_the_text_is_deleted(
        self, admin_client: Client
    ) -> None:
        # Arrange
        document = DocumentFactory.create()
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        data = material_data(
            material,
            content_kind=ContentKind.EXTERNAL_MEDIA,
            external_url="https://example.com/film",
            plain_text="",
        )

        # Act
        response = admin_client.post(change_url(material), data)

        # Assert
        assert response.status_code == 302
        material.refresh_from_db()
        assert material.document is None
        assert not Document.objects.exists()

    def test_us_wr_07_ac2_text_with_fragments_is_not_dropped(self, admin_client: Client) -> None:
        # Arrange
        document = DocumentFactory.create()
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        FragmentFactory.create(document=document)
        data = material_data(
            material,
            content_kind=ContentKind.EXTERNAL_MEDIA,
            external_url="https://example.com/film",
            plain_text="",
        )

        # Act
        response = admin_client.post(change_url(material), data)

        # Assert
        assert form_errors(response) == {
            "__all__": ["Tekst tego bytu ma 1 otagowany fragment. Usuń go przed usunięciem tekstu."]
        }
        material.refresh_from_db()
        assert material.document is not None

    def test_us_wr_07_ac2_plain_text_is_searchable(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=Status.PUBLISHED)
        data = form_data(
            work,
            title="List do redakcji",
            status=Status.PUBLISHED,
            content_kind=ContentKind.PLAIN_TEXT,
            plain_text="Piszę o bagnach Podola.",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        assert (EntityType.MATERIAL, "List do redakcji") in found("bagnach")

    def test_us_wr_07_ac3_linked_to_one_or_more_works(self, admin_client: Client) -> None:
        # Arrange
        first, second = WorkFactory.create_batch(2)
        data = form_data(
            first, second, content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://e.com"
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        material = ContextualMaterial.objects.get()
        assert set(material.works.all()) == {first, second}

    def test_us_wr_07_ac3_needs_at_least_one_work(self, admin_client: Client) -> None:
        # Arrange
        data = form_data(content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://e.com")

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 200
        assert not ContextualMaterial.objects.exists()

    def test_us_wr_07_ac3_each_work_link_can_be_tagged(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        tag = TagFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.EXTERNAL_MEDIA,
            external_url="https://e.com",
            **{f"{LINKS}-0-tags": [tag.pk]},
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        link = ContextualMaterial.objects.get().work_links.get()
        assert list(link.tags.all()) == [tag]

    def test_us_wr_07_ac2_change_form_shows_the_current_scan(self, admin_client: Client) -> None:
        # Arrange
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.OCR_TEXT,
            external_url="",
            document=DocumentFactory.create(ocr=True),
        )
        assert material.document is not None

        # Act
        response = admin_client.get(change_url(material))

        # Assert
        content = response.content.decode()
        assert f'href="{material.document.scan.url}"' in content
        assert '<div class="readonly">1</div>' in content
        assert "</textarea>" in content and "Czarny potok" not in content

    def test_us_wr_07_ac2_change_without_edits_keeps_the_text(self, admin_client: Client) -> None:
        # Arrange
        document = DocumentFactory.create()
        material = ContextualMaterialFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, external_url="", document=document
        )
        MaterialWorkLinkFactory.create(material=material)
        fragment = FragmentFactory.create(document=document, start=0, end=12)

        # Act
        response = admin_client.post(change_url(material), material_data(material, title="Inny"))

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get(pk=document.pk)
        assert (stored.text, stored.updated_at) == (document.text, document.updated_at)
        fragment.refresh_from_db()
        assert not fragment.needs_review
