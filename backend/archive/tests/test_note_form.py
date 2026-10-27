"""The note form: every kind of content, entered on the note's own form (US-WR-05)."""

from typing import TYPE_CHECKING, Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.utils import ErrorDict
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoCaptureOnCommitCallbacks

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

from archive.models import ContentKind, Document, Fragment, Note, Status, Work
from archive.tests.factories import DocumentFactory, FragmentFactory, NoteFactory, WorkFactory
from archive.tests.files import ocr_file, scan_file
from search.models import EntityType
from search.query import search

ADD_URL = reverse("admin:archive_note_add")
REQUIRED = ["To pole jest wymagane."]


def change_url(note: Note) -> str:
    return reverse("admin:archive_note_change", args=[note.pk])


def form_data(*works: Work, **fields: Any) -> dict[str, Any]:
    """What the note form posts, without content unless given."""
    return {
        "title": "Notes 18 · karta 4",
        "status": Status.DRAFT,
        "description": "",
        "shelfmark": "",
        "works": [work.pk for work in works],
        **fields,
    }


def note_data(note: Note, **fields: Any) -> dict[str, Any]:
    """What the change form of `note` posts as it is, without its files."""
    stored = {
        "title": note.title,
        "status": note.status,
        "content_kind": note.content_kind,
        "external_url": note.external_url,
    }
    if note.document is not None and note.document.kind == Document.Kind.PLAIN:
        stored["plain_text"] = note.document.text
    return form_data(*note.works.all(), **{**stored, **fields})


def form_errors(response: "_MonkeyPatchedWSGIResponse") -> ErrorDict:
    assert response.status_code == 200
    errors: ErrorDict = response.context["adminform"].form.errors
    return errors


def note_with_text(**fields: Any) -> Note:
    """A note holding a plain text, linked to one work."""
    note = NoteFactory.create(
        content_kind=ContentKind.PLAIN_TEXT,
        external_url="",
        document=DocumentFactory.create(),
        **fields,
    )
    note.works.add(WorkFactory.create())
    return note


def note_with_ocr_text() -> Note:
    note = NoteFactory.create(
        content_kind=ContentKind.OCR_TEXT,
        external_url="",
        document=DocumentFactory.create(ocr=True),
    )
    note.works.add(WorkFactory.create())
    return note


def found(text: str) -> list[tuple[str, str]]:
    return [
        (hit.entry.entity_type, hit.entry.title)
        for group in search(text).groups
        for hit in group.hits
    ]


@pytest.mark.django_db
class TestNoteForm:
    def test_us_wr_05_ac1_form_has_title_description_shelfmark_and_content(
        self, admin_client: Client
    ) -> None:
        # Arrange & Act
        response = admin_client.get(ADD_URL)

        # Assert
        fields = response.context["adminform"].form.fields
        assert fields["title"].required
        assert not fields["description"].required
        assert not fields["shelfmark"].required
        assert {"content_kind", "image", "file", "external_url", "scan", "ocr_file"} <= set(fields)
        assert "plain_text" in fields
        assert "document" not in fields

    def test_us_wr_05_ac1_title_is_required(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work, title="", content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://a.pl"
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"title": REQUIRED}

    @pytest.mark.parametrize(
        ("content_kind", "field", "value"),
        [
            (
                ContentKind.IMAGE,
                "image",
                SimpleUploadedFile("karta.jpg", b"jpeg", content_type="image/jpeg"),
            ),
            (
                ContentKind.DOCUMENT,
                "file",
                SimpleUploadedFile("list.pdf", b"%PDF", content_type="application/pdf"),
            ),
            (ContentKind.EXTERNAL_MEDIA, "external_url", "https://example.com/nagranie"),
        ],
    )
    def test_us_wr_05_ac2_adds_a_note_with_media_content(
        self, admin_client: Client, content_kind: str, field: str, value: Any
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, content_kind=content_kind, image_alt="Karta 4", **{field: value})

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        note = Note.objects.get()
        assert note.content_kind == content_kind
        assert getattr(note, field)
        assert note.document is None

    def test_us_wr_05_ac2_adds_a_note_with_ocr_text(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.OCR_TEXT,
            scan=scan_file(2),
            ocr_file=ocr_file("Notes 18. ", "Karta 4."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        document = Note.objects.get().document
        assert document is not None
        assert (document.kind, document.text, document.page_count) == (
            Document.Kind.OCR,
            "Notes 18. Karta 4.",
            2,
        )

    def test_us_wr_05_ac2_ocr_text_rejects_page_count_mismatch_with_both_counts(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.OCR_TEXT,
            scan=scan_file(3),
            ocr_file=ocr_file("Jedna.", "Dwie."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"ocr_file": ["The scan has 3 pages, the OCR file has 2."]}
        assert not Note.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_05_ac2_ocr_text_requires_scan_and_ocr_file(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work, content_kind=ContentKind.OCR_TEXT))

        # Assert
        assert form_errors(response) == {"scan": REQUIRED, "ocr_file": REQUIRED}

    def test_us_wr_05_ac2_adds_a_note_with_plain_text(self, admin_client: Client) -> None:
        # Arrange: a browser sends a textarea's line breaks as CRLF
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=ContentKind.PLAIN_TEXT,
            plain_text="Drogi Panie,\r\ndziękuję za list.",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        document = Note.objects.get().document
        assert document is not None
        assert (document.kind, document.text, document.scan.name) == (
            Document.Kind.PLAIN,
            "Drogi Panie,\ndziękuję za list.",
            "",
        )

    def test_us_wr_05_ac2_plain_text_is_required(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work, content_kind=ContentKind.PLAIN_TEXT))

        # Assert
        assert form_errors(response) == {"plain_text": REQUIRED}
        assert not Document.objects.exists()

    def test_us_wr_05_ac2_change_form_shows_the_plain_text(self, admin_client: Client) -> None:
        # Arrange
        note = note_with_text()

        # Act
        response = admin_client.get(change_url(note))

        # Assert
        assert response.context["adminform"].form["plain_text"].value() == (
            "Czarny potok płynie przez las."
        )

    def test_us_wr_05_ac2_editing_plain_text_reanchors_fragments(
        self, admin_client: Client
    ) -> None:
        # Arrange: "Czarny potok płynie przez las."
        note = note_with_text()
        document = note.document
        assert document is not None
        moved = FragmentFactory.create(document=document, start=13, end=19)
        data = note_data(note, plain_text="Czarny potok. Nad lasem płynie.")

        # Act
        response = admin_client.post(change_url(note), data)

        # Assert
        assert response.status_code == 302
        note.refresh_from_db()
        assert note.document_id == document.pk
        moved.refresh_from_db()
        assert (moved.start, moved.needs_review) == (24, True)

    def test_us_wr_05_ac2_change_without_new_content_keeps_the_text(
        self, admin_client: Client
    ) -> None:
        # Arrange
        note = note_with_ocr_text()
        document = note.document
        assert document is not None

        # Act
        response = admin_client.post(change_url(note), note_data(note, title="Karta 5"))

        # Assert
        assert response.status_code == 302
        note.refresh_from_db()
        assert (note.title, note.document) == ("Karta 5", document)

    def test_us_wr_05_ac2_ocr_text_becomes_plain_text_in_the_same_document(
        self,
        admin_client: Client,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        note = note_with_ocr_text()
        document = note.document
        assert document is not None
        storage, old_scan = document.scan.storage, document.scan.name
        assert old_scan and storage.exists(old_scan)
        fragment = FragmentFactory.create(document=document, start=0, end=12)
        data = note_data(note, content_kind=ContentKind.PLAIN_TEXT, plain_text="Czarny potok.")

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(note), data)

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
        assert Fragment.objects.filter(pk=fragment.pk).exists()

    def test_us_wr_05_ac2_plain_text_becomes_ocr_text_with_an_upload(
        self, admin_client: Client
    ) -> None:
        # Arrange
        note = note_with_text()
        document = note.document
        assert document is not None
        data = note_data(note, content_kind=ContentKind.OCR_TEXT)

        # Act
        without_files = admin_client.post(change_url(note), data)
        with_files = admin_client.post(
            change_url(note), {**data, "scan": scan_file(1), "ocr_file": ocr_file("Skan.")}
        )

        # Assert
        assert form_errors(without_files) == {
            "__all__": ["Choose a text of kind “Scan + OCR text”."]
        }
        assert with_files.status_code == 302
        stored = Document.objects.get(pk=document.pk)
        assert (stored.kind, stored.text) == (Document.Kind.OCR, "Skan.")

    def test_us_wr_05_ac2_text_becomes_a_link_and_the_text_is_deleted(
        self,
        admin_client: Client,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        note = note_with_ocr_text()
        assert note.document is not None
        storage, scan = note.document.scan.storage, note.document.scan.name
        assert scan and storage.exists(scan)
        data = note_data(
            note, content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://a.pl/nagranie"
        )

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(note), data)

        # Assert
        assert response.status_code == 302
        note.refresh_from_db()
        assert note.document is None
        assert not Document.objects.exists()
        assert not storage.exists(scan)

    def test_us_wr_05_ac2_text_with_fragments_is_not_dropped(self, admin_client: Client) -> None:
        # Arrange
        note = note_with_text()
        assert note.document is not None
        FragmentFactory.create(document=note.document)
        data = note_data(
            note, content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://a.pl/nagranie"
        )

        # Act
        response = admin_client.post(change_url(note), data)

        # Assert
        assert form_errors(response) == {
            "__all__": [
                "The text of this note has 1 tagged fragment. "
                "Delete its fragments before choosing another kind of content."
            ]
        }
        note.refresh_from_db()
        assert note.document is not None

    @pytest.mark.parametrize("content_kind", [ContentKind.PLAIN_TEXT, ContentKind.EXTERNAL_MEDIA])
    def test_us_wr_05_ac2_files_for_another_kind_of_content_are_errors(
        self, admin_client: Client, content_kind: str
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            content_kind=content_kind,
            plain_text="Tekst.",
            external_url="https://a.pl" if content_kind == ContentKind.EXTERNAL_MEDIA else "",
            scan=scan_file(1),
            ocr_file=ocr_file("Tekst."),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        empty = ["Leave this empty for this kind of content."]
        assert form_errors(response) == {"scan": empty, "ocr_file": empty}

    def test_us_wr_05_ac2_saving_indexes_the_text(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            title="List do Buczkowskiego",
            status=Status.PUBLISHED,
            content_kind=ContentKind.PLAIN_TEXT,
            plain_text="Wertepy prowadzą przez bagna.",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        assert found("bagna") == [(EntityType.NOTE, "List do Buczkowskiego")]

    def test_us_wr_05_ac3_links_a_note_to_several_works(self, admin_client: Client) -> None:
        # Arrange
        works = WorkFactory.create_batch(2)
        data = form_data(
            *works, content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://a.pl"
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        assert set(Note.objects.get().works.all()) == set(works)

    def test_us_wr_05_ac3_a_note_needs_a_work(self, admin_client: Client) -> None:
        # Arrange
        data = form_data(content_kind=ContentKind.EXTERNAL_MEDIA, external_url="https://a.pl")

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"works": REQUIRED}
