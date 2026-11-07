"""Uploading a typescript's text: a searchable PDF scan, which carries its OCR text (US-WR-04)."""

import random
from typing import TYPE_CHECKING, Any

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.utils import ErrorDict
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoCaptureOnCommitCallbacks

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

from archive.models import Document, Fragment, Status, Typescript, Work
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    TypescriptFactory,
    WorkFactory,
)
from archive.tests.files import SCAN_WITHOUT_TEXT, scan_file
from archive.uploads import load_ocr_upload
from search.models import EntityType
from search.query import search

ADD_URL = reverse("admin:archive_typescript_add")


def change_url(typescript: Typescript) -> str:
    return reverse("admin:archive_typescript_change", args=[typescript.pk])


def form_data(work: Work, **fields: Any) -> dict[str, Any]:
    """What the typescript form posts, without files unless given."""
    return {
        "title": "Pierwsza wersja",
        "work": work.pk,
        "status": Status.DRAFT,
        "description": "",
        "shelfmark": "",
        **fields,
    }


def typescript_data(typescript: Typescript, **fields: Any) -> dict[str, Any]:
    """What the change form of `typescript` posts as it is."""
    stored = {
        "title": typescript.title,
        "status": typescript.status,
        "description": typescript.description,
        "shelfmark": typescript.shelfmark,
    }
    if typescript.is_main:
        stored["is_main"] = "on"
    return form_data(typescript.work, **{**stored, **fields})


def form_errors(response: "_MonkeyPatchedWSGIResponse") -> ErrorDict:
    assert response.status_code == 200
    errors: ErrorDict = response.context["adminform"].form.errors
    return errors


def found(text: str) -> list[tuple[str, str]]:
    """The typescripts and fragments a search finds."""
    return [
        (hit.entry.entity_type, hit.entry.title)
        for group in search(text).groups
        for hit in group.hits
    ]


def novel(words: int, seed: int = 16) -> list[str]:
    """Pages of Polish-like prose: a Zipf-distributed vocabulary of made-up words."""
    rng = random.Random(seed)
    syllables = [
        "ba",
        "be",
        "bi",
        "bo",
        "by",
        "cha",
        "cze",
        "dro",
        "dzie",
        "ga",
        "gro",
        "ja",
        "ka",
        "kło",
        "ko",
        "la",
        "le",
        "ło",
        "ma",
        "mu",
        "na",
        "nie",
        "no",
        "pa",
        "po",
        "prze",
        "ra",
        "rzy",
        "sa",
        "sie",
        "sko",
        "sta",
        "sza",
        "ście",
        "ta",
        "to",
        "tro",
        "wa",
        "wie",
        "wo",
        "za",
        "ze",
        "zło",
        "żo",
    ]
    vocabulary = sorted(
        {"".join(rng.choices(syllables, k=rng.randint(1, 5))) for _ in range(60_000)}
    )
    rng.shuffle(vocabulary)
    weights = [1 / rank for rank in range(1, len(vocabulary) + 1)]
    text = rng.choices(vocabulary, weights=weights, k=words)
    return [" ".join(text[start : start + 300]) for start in range(0, words, 300)]


@pytest.mark.django_db
class TestLoadOcrUpload:
    def test_us_wr_04_ac1_loads_scan_and_page_texts_into_a_new_document(self) -> None:
        # Arrange
        scan = scan_file("Czarny potok.", "Las.")

        # Act
        document = load_ocr_upload(None, scan)

        # Assert
        assert document.pk is None
        assert (document.kind, document.text) == (Document.Kind.OCR, "Czarny potok.\nLas.\n")
        assert document.page_offsets == [0, 14]
        assert document.scan.name == "scan.pdf"

    def test_us_wr_04_ac2_rejects_a_scan_without_text(self) -> None:
        # Arrange: a PDF of page images only, never run through OCR
        scan = scan_file("", "")

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(None, scan)

        # Assert
        assert raised.value.messages == [SCAN_WITHOUT_TEXT]

    def test_us_wr_04_ac2_a_page_without_text_keeps_its_place(self) -> None:
        # Arrange: a blank page between two pages of text
        scan = scan_file("Jeden.", "", "Trzy.")

        # Act
        document = load_ocr_upload(None, scan)

        # Assert
        assert document.text == "Jeden.\nTrzy.\n"
        assert document.page_offsets == [0, 7, 7]
        assert [document.page_number(0), document.page_number(7)] == [1, 3]

    def test_us_wr_04_ac2_joins_words_split_at_a_line_end(self) -> None:
        # Arrange: OCR programs mark a word split at a line end with a soft hyphen
        scan = scan_file("Zoba\xad\nczyli ją   \npotem. Prze\xad\nświad\xad\nczony był.")

        # Act
        document = load_ocr_upload(None, scan)

        # Assert
        assert document.text == "Zobaczyli\nją\npotem. Przeświadczony\nbył.\n"

    def test_us_wr_04_ac1_loads_a_new_text_into_the_same_document(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None

        # Act
        loaded = load_ocr_upload(document, scan_file("Nowy tekst."))

        # Assert
        assert loaded is document
        assert document.text == "Nowy tekst.\n"

    def test_us_wr_04_ac2_rejected_scan_leaves_the_document_unchanged(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        before = (document.scan.name, document.text, document.page_offsets)

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(document, scan_file(""))

        # Assert
        assert raised.value.messages == [SCAN_WITHOUT_TEXT]
        assert (document.scan.name, document.text, document.page_offsets) == before

    def test_us_wr_04_unreadable_pdf_is_an_error(self) -> None:
        # Arrange
        scan = SimpleUploadedFile("scan.pdf", b"not a pdf")

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(None, scan)

        # Assert
        assert raised.value.messages == ["Skan nie jest czytelnym plikiem PDF."]


@pytest.mark.django_db
class TestTypescriptForm:
    def test_us_wr_04_ac1_adds_a_typescript_with_a_searchable_scan(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, scan=scan_file("Czarny potok.", "Las."))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        typescript = Typescript.objects.get(work=work)
        assert typescript.document is not None
        assert typescript.document.kind == Document.Kind.OCR
        assert typescript.document.text == "Czarny potok.\nLas.\n"
        assert typescript.document.page_count == 2
        scan_name = typescript.document.scan.name
        assert scan_name is not None and scan_name.endswith(".pdf")

    def test_us_wr_04_ac1_requires_a_scan_on_create(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work))

        # Assert
        assert form_errors(response) == {"scan": ["To pole jest wymagane."]}
        assert not Typescript.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_04_ac1_change_without_a_scan_keeps_text(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        data = typescript_data(typescript, title="Druga wersja")

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        typescript.refresh_from_db()
        assert typescript.title == "Druga wersja"
        assert typescript.document == document
        assert typescript.document.text == document.text

    def test_us_wr_04_ac2_rejects_a_scan_without_text(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, scan=scan_file("", "", ""))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"scan": [SCAN_WITHOUT_TEXT]}
        assert not Typescript.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_04_ac2_scan_is_read_only_when_the_rest_of_the_form_is_valid(
        self, admin_client: Client
    ) -> None:
        # Arrange: reading a long scan takes seconds, and a rejected form loses its file anyway
        work = WorkFactory.create()
        data = form_data(work, title="", scan=scan_file("", ""))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert list(form_errors(response)) == ["title"]

    def test_us_wr_04_ac1_replacing_the_scan_reanchors_fragments(
        self, admin_client: Client
    ) -> None:
        # Arrange: "Czarny potok płynie przez las."
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        in_place = FragmentFactory.create(document=document, start=0, end=12)
        moved = FragmentFactory.create(document=document, start=13, end=19)
        lost = FragmentFactory.create(document=document, start=26, end=30)
        scan = scan_file("Czarny potok. Nad lasem płynie.", "Koniec.")
        data = typescript_data(typescript, scan=scan)

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        typescript.refresh_from_db()
        assert typescript.document_id == document.pk
        assert Fragment.objects.filter(document=document).count() == 3
        for fragment in (in_place, moved, lost):
            fragment.refresh_from_db()
        assert (in_place.start, in_place.end, in_place.needs_review) == (0, 12, False)
        assert (moved.quote, moved.start, moved.needs_review) == ("płynie", 24, True)
        assert (lost.quote, lost.start, lost.needs_review) == ("las.", 26, True)
        assert typescript.document is not None
        assert typescript.document.page_offsets == [0, 32]

    def test_us_wr_04_ac1_replacing_the_scan_deletes_the_old_one(
        self,
        admin_client: Client,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        assert typescript.document is not None
        storage = typescript.document.scan.storage
        old_name = typescript.document.scan.name
        assert old_name and storage.exists(old_name)
        data = typescript_data(typescript, scan=scan_file("Nowy tekst."))

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        new_name = Document.objects.get(pk=typescript.document.pk).scan.name
        assert new_name and new_name != old_name
        assert storage.exists(new_name)
        assert not storage.exists(old_name)

    def test_us_wr_04_ac2_rejected_scan_keeps_old_document(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        fragment = FragmentFactory.create(document=document, start=0, end=12)
        data = typescript_data(typescript, scan=scan_file("", ""))

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert form_errors(response) == {"scan": [SCAN_WITHOUT_TEXT]}
        stored = Document.objects.get(pk=document.pk)
        assert (stored.scan.name, stored.text, stored.page_offsets) == (
            document.scan.name,
            document.text,
            document.page_offsets,
        )
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (0, 12, False)

    def test_us_wr_04_model_error_about_the_text_shows_above_the_form(
        self, admin_client: Client
    ) -> None:
        # Arrange: a typescript left holding a plain text, which the model rejects
        typescript = TypescriptFactory.create(document=DocumentFactory.create())

        # Act
        response = admin_client.post(change_url(typescript), typescript_data(typescript))

        # Assert
        assert form_errors(response) == {"__all__": ["Wybierz tekst rodzaju „Skan + tekst OCR”."]}

    def test_us_wr_04_unreadable_pdf_is_a_form_error(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        scan = SimpleUploadedFile("scan.pdf", b"%PDF-1.4 not really")

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan=scan))

        # Assert
        assert form_errors(response) == {"scan": ["Skan nie jest czytelnym plikiem PDF."]}

    def test_us_wr_04_wrong_file_extension_is_a_form_error(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, scan=scan_file("Tekst.", name="scan.png"))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert set(form_errors(response)) == {"scan"}

    def test_us_wr_04_ac3_marking_main_unmarks_previous(self, admin_client: Client) -> None:
        # Arrange
        previous = TypescriptFactory.create(is_main=True)
        data = form_data(previous.work, is_main="on", scan=scan_file("Tekst."))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        previous.refresh_from_db()
        assert not previous.is_main
        assert Typescript.objects.get(work=previous.work, is_main=True).pk != previous.pk

    def test_us_wr_04_ac4_save_updates_search_index(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=Status.PUBLISHED, title="Maszynopis")
        data = typescript_data(typescript, scan=scan_file("Wertepy prowadzą przez bagna."))
        assert found("potok") == [(EntityType.TYPESCRIPT, "Maszynopis")]

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        assert found("bagna") == [(EntityType.TYPESCRIPT, "Maszynopis")]
        assert found("potok") == []

    def test_us_wr_04_ac4_search_finds_a_word_split_at_a_line_end(
        self, admin_client: Client
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=Status.PUBLISHED, title="Maszynopis")
        data = typescript_data(typescript, scan=scan_file("Przez wer\xad\ntepy."))

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        assert found("wertepy") == [(EntityType.TYPESCRIPT, "Maszynopis")]

    def test_us_wr_04_change_form_shows_the_current_scan_and_page_count(
        self, admin_client: Client
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        assert typescript.document is not None

        # Act
        response = admin_client.get(change_url(typescript))

        # Assert
        content = response.content.decode()
        assert f'href="{typescript.document.scan.url}"' in content
        assert 'name="document"' not in content
        assert 'name="scan"' in content
        assert 'name="ocr_file"' not in content
        assert 'name="plain_text"' not in content
        assert '<div class="readonly">1</div>' in content

    def test_us_wr_04_document_admin_is_missing_from_the_index(self, admin_client: Client) -> None:
        # Arrange & Act
        response = admin_client.get(reverse("admin:index"))
        # The Document admin stays registered for the raw_id lookup used until steps 7-9.
        lookup = reverse("admin:archive_document_changelist")

        # Assert
        content = response.content.decode()
        assert "archive_document" not in content
        assert reverse("admin:archive_typescript_changelist") in content
        assert admin_client.get(lookup).status_code == 200

    def test_us_wr_04_full_length_text_is_saved_and_searchable(self, admin_client: Client) -> None:
        # Arrange: a whole novel, about 1.5 MB, and a word only on its last page (#16).
        pages = [*novel(words=220_000), "Na końcu stoi samotny dezerter."]
        assert len("".join(pages).encode()) > 1_000_000
        work = WorkFactory.create()
        data = form_data(
            work, title="Cała powieść", status=Status.PUBLISHED, scan=scan_file(*pages)
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        typescript = Typescript.objects.get(work=work)
        assert typescript.document is not None
        assert typescript.document.page_count == len(pages)
        assert found("dezerter") == [(EntityType.TYPESCRIPT, "Cała powieść")]
