"""Uploading a typescript's text: a scan and its OCR file (US-WR-04)."""

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
from archive.tests.files import ocr_file, scan_file
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
    def test_us_wr_04_ac1_loads_scan_and_pages_into_a_new_document(self) -> None:
        # Arrange
        scan, ocr = scan_file(2), ocr_file("Czarny potok. ", "Las.")

        # Act
        document = load_ocr_upload(None, scan, ocr)

        # Assert
        assert document.pk is None
        assert (document.kind, document.text) == (Document.Kind.OCR, "Czarny potok. Las.")
        assert document.page_offsets == [0, 14]
        assert document.scan.name == "scan.pdf"

    def test_us_wr_04_ac2_rejects_page_count_mismatch_with_both_counts(self) -> None:
        # Arrange
        scan, ocr = scan_file(12), ocr_file(*["Strona."] * 11)

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(None, scan, ocr)

        # Assert
        assert raised.value.message_dict == {"ocr_file": ["Skan ma 12 stron, plik OCR ma 11."]}

    @pytest.mark.parametrize(
        ("scan_pages", "expected"),
        [
            (1, "Skan ma 1 stronę, plik OCR ma 2."),
            (22, "Skan ma 22 strony, plik OCR ma 23."),
            (5, "Skan ma 5 stron, plik OCR ma 6."),
        ],
    )
    def test_us_wr_04_ac2_page_count_mismatch_uses_polish_plural_forms(
        self, scan_pages: int, expected: str
    ) -> None:
        # Arrange
        scan, ocr = scan_file(scan_pages), ocr_file(*["Strona."] * (scan_pages + 1))

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(None, scan, ocr)

        # Assert
        assert raised.value.message_dict == {"ocr_file": [expected]}

    def test_us_wr_04_ac2_loads_a_new_text_into_the_same_document(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None

        # Act
        loaded = load_ocr_upload(document, scan_file(1), ocr_file("Nowy tekst."))

        # Assert
        assert loaded is document
        assert document.text == "Nowy tekst."

    def test_us_wr_04_ac2_rejected_files_leave_the_document_unchanged(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        before = (document.scan.name, document.text, document.page_offsets)

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(document, scan_file(1), ocr_file("Jeden.", "Dwa."))

        # Assert
        assert "ocr_file" in raised.value.message_dict
        assert (document.scan.name, document.text, document.page_offsets) == before

    def test_us_wr_04_unreadable_pdf_and_non_utf8_text_are_errors(self) -> None:
        # Arrange
        scan = SimpleUploadedFile("scan.pdf", b"not a pdf")
        ocr = ocr_file("Zażółć gęślą jaźń.", encoding="cp1250")

        # Act
        with pytest.raises(ValidationError) as raised:
            load_ocr_upload(None, scan, ocr)

        # Assert
        assert raised.value.message_dict == {
            "scan": ["Skan nie jest czytelnym plikiem PDF."],
            "ocr_file": ["Plik OCR nie jest tekstem w UTF-8. Zapisz go w UTF-8 i wgraj ponownie."],
        }


@pytest.mark.django_db
class TestTypescriptForm:
    def test_us_wr_04_ac1_adds_a_typescript_with_scan_and_ocr_file(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, scan=scan_file(2), ocr_file=ocr_file("Czarny potok. ", "Las."))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        typescript = Typescript.objects.get(work=work)
        assert typescript.document is not None
        assert typescript.document.kind == Document.Kind.OCR
        assert typescript.document.text == "Czarny potok. Las."
        assert typescript.document.page_count == 2
        scan_name = typescript.document.scan.name
        assert scan_name is not None and scan_name.endswith(".pdf")

    def test_us_wr_04_ac1_requires_scan_and_ocr_file_on_create(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work))

        # Assert
        errors = form_errors(response)
        assert errors["scan"] == ["To pole jest wymagane."]
        assert errors["ocr_file"] == ["To pole jest wymagane."]
        assert "__all__" not in errors
        assert not Typescript.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_04_ac1_requires_both_files_on_create(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan=scan_file(1)))

        # Assert
        assert list(form_errors(response)) == ["ocr_file"]
        assert not Document.objects.exists()

    def test_us_wr_04_ac1_change_without_files_keeps_text(self, admin_client: Client) -> None:
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

    @pytest.mark.parametrize("uploaded", ["scan", "ocr_file"])
    def test_us_wr_04_ac2_change_with_one_file_asks_for_the_other(
        self, admin_client: Client, uploaded: str
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        files = {"scan": scan_file(1), "ocr_file": ocr_file("Nowy tekst.")}
        data = typescript_data(typescript, **{uploaded: files[uploaded]})

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        missing = "ocr_file" if uploaded == "scan" else "scan"
        assert form_errors(response) == {
            missing: ["Wgraj skan i plik OCR razem, żeby dało się porównać ich strony."]
        }
        typescript.refresh_from_db()
        assert typescript.document is not None
        assert typescript.document.text == "Czarny potok płynie przez las."

    def test_us_wr_04_ac2_rejects_page_count_mismatch_with_both_counts(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, scan=scan_file(12), ocr_file=ocr_file(*["Strona."] * 11))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"ocr_file": ["Skan ma 12 stron, plik OCR ma 11."]}
        assert not Typescript.objects.exists()
        assert not Document.objects.exists()

    def test_us_wr_04_ac2_replacing_text_reanchors_fragments(self, admin_client: Client) -> None:
        # Arrange: "Czarny potok płynie przez las."
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        in_place = FragmentFactory.create(document=document, start=0, end=12)
        moved = FragmentFactory.create(document=document, start=13, end=19)
        lost = FragmentFactory.create(document=document, start=26, end=30)
        new_text = ocr_file("Czarny potok. Nad lasem płynie.", "Koniec.")
        data = typescript_data(typescript, scan=scan_file(2), ocr_file=new_text)

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
        assert typescript.document.page_offsets == [0, 31]

    def test_us_wr_04_ac2_replacing_text_deletes_the_old_scan(
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
        data = typescript_data(typescript, scan=scan_file(1), ocr_file=ocr_file("Nowy tekst."))

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        new_name = Document.objects.get(pk=typescript.document.pk).scan.name
        assert new_name and new_name != old_name
        assert storage.exists(new_name)
        assert not storage.exists(old_name)

    def test_us_wr_04_ac2_rejected_upload_keeps_old_document(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        document = typescript.document
        assert document is not None
        fragment = FragmentFactory.create(document=document, start=0, end=12)
        data = typescript_data(
            typescript, scan=scan_file(3), ocr_file=ocr_file("Inny tekst.", "Druga strona.")
        )

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert form_errors(response) == {"ocr_file": ["Skan ma 3 strony, plik OCR ma 2."]}
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
        data = form_data(work, scan=scan, ocr_file=ocr_file("Tekst."))

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {"scan": ["Skan nie jest czytelnym plikiem PDF."]}

    def test_us_wr_04_non_utf8_ocr_file_is_a_form_error(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        ocr = ocr_file("Zażółć gęślą jaźń.", encoding="cp1250")
        data = form_data(work, scan=scan_file(1), ocr_file=ocr)

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert form_errors(response) == {
            "ocr_file": ["Plik OCR nie jest tekstem w UTF-8. Zapisz go w UTF-8 i wgraj ponownie."]
        }

    def test_us_wr_04_wrong_file_extensions_are_form_errors(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            scan=scan_file(1, name="scan.png"),
            ocr_file=ocr_file("Tekst.", name="scan.docx"),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert set(form_errors(response)) == {"scan", "ocr_file"}

    def test_us_wr_04_ac3_marking_main_unmarks_previous(self, admin_client: Client) -> None:
        # Arrange
        previous = TypescriptFactory.create(is_main=True)
        data = form_data(
            previous.work, is_main="on", scan=scan_file(1), ocr_file=ocr_file("Tekst.")
        )

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
        data = typescript_data(
            typescript, scan=scan_file(1), ocr_file=ocr_file("Wertepy prowadzą przez bagna.")
        )
        assert found("potok") == [(EntityType.TYPESCRIPT, "Maszynopis")]

        # Act
        response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        assert found("bagna") == [(EntityType.TYPESCRIPT, "Maszynopis")]
        assert found("potok") == []

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
        assert 'name="ocr_file"' in content
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
            work,
            title="Cała powieść",
            status=Status.PUBLISHED,
            scan=scan_file(len(pages)),
            ocr_file=ocr_file(*pages),
        )

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        typescript = Typescript.objects.get(work=work)
        assert typescript.document is not None
        assert typescript.document.page_count == len(pages)
        assert found("dezerter") == [(EntityType.TYPESCRIPT, "Cała powieść")]
