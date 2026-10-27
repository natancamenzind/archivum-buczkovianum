"""The secondary text form: its fields, its text as OCR or plain text, its works (US-WR-06)."""

from datetime import date
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoCaptureOnCommitCallbacks

from archive.models import Document, SecondaryText, Status
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    WorkFactory,
)
from archive.tests.files import ocr_file, scan_file
from archive.tests.test_uploads import form_errors, found
from search.models import EntityType

ADD_URL = reverse("admin:archive_secondarytext_add")
BOTH_TEXTS = "Upload a scan and its OCR file, or enter a plain text, not both."
NO_TEXT = "Upload a scan and its OCR file, or enter a plain text."


def change_url(secondary_text: SecondaryText) -> str:
    return reverse("admin:archive_secondarytext_change", args=[secondary_text.pk])


def form_data(*work_links: dict[str, Any], **fields: Any) -> dict[str, Any]:
    """What the secondary text form posts: its fields and the work links inline."""
    data: dict[str, Any] = {
        "title": "Recenzja Wertepów",
        "kind": SecondaryText.Kind.REVIEW,
        "status": Status.DRAFT,
        "description": "",
        "shelfmark": "",
        "author": "",
        "source": "",
        "letter_date": "",
        "sender": "",
        "recipient": "",
        "plain_text": "",
        "work_links-TOTAL_FORMS": len(work_links),
        "work_links-INITIAL_FORMS": sum("id" in link for link in work_links),
        "work_links-MIN_NUM_FORMS": 1,
        "work_links-MAX_NUM_FORMS": 1000,
        **fields,
    }
    for index, link in enumerate(work_links):
        for name, value in link.items():
            data[f"work_links-{index}-{name}"] = value
    return data


def secondary_text_data(secondary_text: SecondaryText, **fields: Any) -> dict[str, Any]:
    """What the change form of `secondary_text` posts as it is."""
    document = secondary_text.document
    plain = document.text if document and document.kind == Document.Kind.PLAIN else ""
    links = [
        {"id": link.pk, "secondary_text": secondary_text.pk, "work": link.work_id}
        for link in secondary_text.work_links.all()
    ]
    stored = {
        "title": secondary_text.title,
        "kind": secondary_text.kind,
        "status": secondary_text.status,
        "author": secondary_text.author,
        # A browser posts a textarea's line breaks as CRLF.
        "plain_text": plain.replace("\n", "\r\n"),
    }
    return form_data(*links, **{**stored, **fields})


@pytest.mark.django_db
class TestSecondaryTextForm:
    def test_us_wr_06_ac1_adds_a_letter_with_every_field_and_a_plain_text(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            {"work": work.pk},
            title="List do Iwaszkiewicza",
            kind=SecondaryText.Kind.LETTER,
            description="O Czarnym potoku.",
            shelfmark="1618",
            author="Leopold Buczkowski",
            source="Twórczość, Warszawa 1955, s. 3-4",
            letter_date="1955-03-01",
            sender="Leopold Buczkowski",
            recipient="Jarosław Iwaszkiewicz",
            plain_text="Drogi Panie,\r\npiszę z Konstancina.",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        letter = SecondaryText.objects.get()
        assert (letter.title, letter.kind, letter.description, letter.shelfmark) == (
            "List do Iwaszkiewicza",
            SecondaryText.Kind.LETTER,
            "O Czarnym potoku.",
            "1618",
        )
        assert (letter.author, letter.source) == (
            "Leopold Buczkowski",
            "Twórczość, Warszawa 1955, s. 3-4",
        )
        assert (letter.letter_date, letter.sender, letter.recipient) == (
            date(1955, 3, 1),
            "Leopold Buczkowski",
            "Jarosław Iwaszkiewicz",
        )
        assert letter.document is not None
        assert letter.document.kind == Document.Kind.PLAIN
        assert letter.document.text == "Drogi Panie,\npiszę z Konstancina."
        assert not letter.document.scan
        assert letter.document.page_offsets == []

    def test_us_wr_06_ac1_adds_a_secondary_text_with_scan_and_ocr_file(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            {"work": work.pk}, scan=scan_file(2), ocr_file=ocr_file("Recenzja. ", "Koniec.")
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        review = SecondaryText.objects.get()
        assert review.document is not None
        assert review.document.kind == Document.Kind.OCR
        assert review.document.text == "Recenzja. Koniec."
        assert review.document.page_count == 2

    def test_us_wr_06_ac1_requires_a_text_on_create(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data({"work": work.pk}, plain_text="  \r\n"))

        # Assert
        assert form_errors(response) == {"__all__": [NO_TEXT]}
        assert not SecondaryText.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_06_ac1_requires_title_and_kind(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data({"work": work.pk}, title="", kind="", plain_text="Tekst.")

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert set(form_errors(response)) == {"title", "kind"}
        assert not Document.objects.exists()

    @pytest.mark.parametrize("uploaded", ["scan", "ocr_file"])
    def test_us_wr_06_ac1_rejects_files_and_plain_text_together(
        self, admin_client: Client, uploaded: str
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        files = {"scan": scan_file(1), "ocr_file": ocr_file("Recenzja.")}
        data = form_data({"work": work.pk}, plain_text="Recenzja.", **{uploaded: files[uploaded]})

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"plain_text": [BOTH_TEXTS]}
        assert not Document.objects.exists()

    def test_us_wr_06_ac1_change_without_edits_keeps_the_plain_text(
        self, admin_client: Client
    ) -> None:
        # Arrange
        document = DocumentFactory.create(text="Pierwszy akapit.\nDrugi akapit.")
        secondary_text = SecondaryTextWorkLinkFactory.create(
            secondary_text__document=document
        ).secondary_text
        fragment = FragmentFactory.create(document=document, start=17, end=22)
        data = secondary_text_data(secondary_text, title="Nowy tytuł")

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get()
        assert stored.text == "Pierwszy akapit.\nDrugi akapit."
        assert SecondaryText.objects.get().title == "Nowy tytuł"
        fragment.refresh_from_db()
        assert (fragment.start, fragment.needs_review) == (17, False)

    def test_us_wr_06_ac1_editing_the_plain_text_reanchors_fragments(
        self, admin_client: Client
    ) -> None:
        # Arrange: "Czarny potok płynie przez las."
        secondary_text = SecondaryTextWorkLinkFactory.create().secondary_text
        document = secondary_text.document
        assert document is not None
        in_place = FragmentFactory.create(document=document, start=0, end=12)
        moved = FragmentFactory.create(document=document, start=13, end=19)
        data = secondary_text_data(secondary_text, plain_text="Czarny potok. Nad lasem płynie.")

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get()
        assert stored.pk == document.pk
        assert stored.text == "Czarny potok. Nad lasem płynie."
        for fragment in (in_place, moved):
            fragment.refresh_from_db()
        assert (in_place.start, in_place.needs_review) == (0, False)
        assert (moved.quote, moved.start, moved.needs_review) == ("płynie", 24, True)

    def test_us_wr_06_ac1_emptying_the_plain_text_is_an_error(self, admin_client: Client) -> None:
        # Arrange
        secondary_text = SecondaryTextWorkLinkFactory.create().secondary_text
        data = secondary_text_data(secondary_text, plain_text="")

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert form_errors(response) == {"plain_text": ["To pole jest wymagane."]}
        assert Document.objects.get().text == "Czarny potok płynie przez las."

    def test_us_wr_06_ac1_a_plain_text_replaces_the_ocr_text_and_its_scan(
        self,
        admin_client: Client,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        secondary_text = SecondaryTextWorkLinkFactory.create(
            secondary_text__document=DocumentFactory.create(ocr=True)
        ).secondary_text
        document = secondary_text.document
        assert document is not None
        fragment = FragmentFactory.create(document=document, start=0, end=12)
        storage = document.scan.storage
        old_scan = document.scan.name
        assert old_scan and storage.exists(old_scan)
        data = secondary_text_data(secondary_text, plain_text="Czarny potok wysechł.")

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get()
        assert stored.pk == document.pk
        assert (stored.kind, stored.text, stored.page_offsets) == (
            Document.Kind.PLAIN,
            "Czarny potok wysechł.",
            [],
        )
        assert not stored.scan
        assert not storage.exists(old_scan)
        fragment.refresh_from_db()
        assert (fragment.start, fragment.needs_review) == (0, False)

    def test_us_wr_06_ac1_ocr_files_replace_the_plain_text(self, admin_client: Client) -> None:
        # Arrange: the textarea posts the stored plain text back unchanged
        secondary_text = SecondaryTextWorkLinkFactory.create().secondary_text
        data = secondary_text_data(
            secondary_text, scan=scan_file(1), ocr_file=ocr_file("Czarny potok.")
        )

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 302
        stored = Document.objects.get()
        assert (stored.kind, stored.text, stored.page_offsets) == (
            Document.Kind.OCR,
            "Czarny potok.",
            [0],
        )
        assert stored.scan

    def test_us_wr_06_ac1_form_shows_the_text_and_no_document_lookup(
        self, admin_client: Client
    ) -> None:
        # Arrange
        secondary_text = SecondaryTextWorkLinkFactory.create().secondary_text

        # Act
        response = admin_client.get(change_url(secondary_text))

        # Assert
        content = response.content.decode()
        assert 'name="document"' not in content
        assert 'name="scan"' in content
        assert 'name="ocr_file"' in content
        assert "Czarny potok płynie przez las.</textarea>" in content

    def test_us_wr_06_ac1_change_form_shows_the_current_scan_and_page_count(
        self, admin_client: Client
    ) -> None:
        # Arrange
        secondary_text = SecondaryTextFactory.create(document=DocumentFactory.create(ocr=True))
        assert secondary_text.document is not None

        # Act
        response = admin_client.get(change_url(secondary_text))

        # Assert
        content = response.content.decode()
        assert f'href="{secondary_text.document.scan.url}"' in content
        assert '<div class="readonly">1</div>' in content

    def test_us_wr_06_ac1_saving_the_plain_text_updates_search_index(
        self, admin_client: Client
    ) -> None:
        # Arrange
        secondary_text = SecondaryTextWorkLinkFactory.create(
            secondary_text__title="Recenzja", secondary_text__status=Status.PUBLISHED
        ).secondary_text
        assert found("potok") == [(EntityType.SECONDARY_TEXT, "Recenzja")]
        data = secondary_text_data(secondary_text, plain_text="Wertepy prowadzą przez bagna.")

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 302
        assert found("bagna") == [(EntityType.SECONDARY_TEXT, "Recenzja")]
        assert found("potok") == []

    def test_us_wr_06_ac2_requires_a_work(self, admin_client: Client) -> None:
        # Act
        response = admin_client.post(ADD_URL, form_data(plain_text="Recenzja."))

        # Assert
        assert response.status_code == 200
        formset = response.context["inline_admin_formsets"][0].formset
        assert formset.non_form_errors() == ["Proszę wysłać co najmniej 1 formularz."]
        assert not SecondaryText.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_06_ac2_removing_every_work_is_refused_and_keeps_the_text(
        self, admin_client: Client
    ) -> None:
        # Arrange
        secondary_text = SecondaryTextWorkLinkFactory.create().secondary_text
        data = secondary_text_data(secondary_text, plain_text="Nowy tekst.")
        data["work_links-0-DELETE"] = "on"

        # Act
        response = admin_client.post(change_url(secondary_text), data)

        # Assert
        assert response.status_code == 200
        assert secondary_text.work_links.count() == 1
        assert Document.objects.get().text == "Czarny potok płynie przez las."

    def test_us_wr_06_ac2_links_several_works_each_with_its_own_tags(
        self, admin_client: Client
    ) -> None:
        # Arrange
        wertepy, potok = WorkFactory.create_batch(2)
        polemika, pochwala = TagFactory.create_batch(2)
        data = form_data(
            {"work": wertepy.pk, "tags": [polemika.pk]},
            {"work": potok.pk, "tags": [pochwala.pk]},
            plain_text="Recenzja.",
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        links = {
            link.work: list(link.tags.all())
            for link in SecondaryText.objects.get().work_links.all()
        }
        assert links == {wertepy: [polemika], potok: [pochwala]}
