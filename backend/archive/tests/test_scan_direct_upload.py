"""Uploading a scan from the browser straight to storage, which the form then reads (ARC-64)."""

import base64
import json
import uuid
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoCaptureOnCommitCallbacks
from pytest_django.fixtures import Settings

from archive.models import Document, Typescript
from archive.tests.factories import DocumentFactory, TypescriptFactory, WorkFactory
from archive.tests.files import SCAN_WITHOUT_TEXT, scan_file, searchable_pdf
from archive.tests.test_uploads import ADD_URL, change_url, form_data, form_errors
from archive.uploads import MAX_SCAN_SIZE, STORED_SCAN_NAME

SIGN_URL = reverse("admin:archive_document_scan_upload")
INVALID_KEY = "Wgrany skan jest nieprawidłowy."
MISSING_SCAN = "Skan nie został wgrany do końca. Wybierz plik ponownie."


def uploaded_scan(content: bytes, filename: str = "skan.pdf") -> str:
    """Store `content` as the browser's upload does, and return the name the form posts."""
    name = f"scans/{uuid.uuid4().hex}/{filename}"
    assert default_storage.save(name, ContentFile(content)) == name
    return name


def stored_scans(media_root: Path) -> list[str]:
    return sorted(str(path.relative_to(media_root)) for path in media_root.rglob("*.pdf"))


@pytest.fixture
def s3_storage(settings: Settings) -> None:
    """Media on S3, as on the server. Signing an upload needs no connection to S3."""
    settings.AWS_STORAGE_BUCKET_NAME = "archive"
    settings.AWS_S3_REGION_NAME = "eu-north-1"
    settings.AWS_ACCESS_KEY_ID = "test-key"
    settings.AWS_SECRET_ACCESS_KEY = "test-secret"
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    }


@pytest.mark.django_db
class TestStoredScanForm:
    def test_arc_64_saves_the_scan_the_browser_uploaded_without_copying_it(
        self, admin_client: Client, settings: Settings
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        name = uploaded_scan(searchable_pdf("Czarny potok.", "Las."))

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan_key=name))

        # Assert
        assert response.status_code == 302
        document = Typescript.objects.get(work=work).document
        assert document is not None
        assert document.kind == Document.Kind.OCR
        assert document.text == "Czarny potok.\nLas.\n"
        assert document.page_count == 2
        assert document.scan.name == name
        assert stored_scans(settings.MEDIA_ROOT) == [name]

    def test_arc_64_replacing_the_scan_deletes_the_old_one(
        self,
        admin_client: Client,
        settings: Settings,
        django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        assert typescript.document is not None
        old_name = typescript.document.scan.name
        name = uploaded_scan(searchable_pdf("Nowy tekst."))
        data = form_data(typescript.work, title=typescript.title, scan_key=name)

        # Act
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(change_url(typescript), data)

        # Assert
        assert response.status_code == 302
        typescript.refresh_from_db()
        assert typescript.document is not None
        assert typescript.document.text == "Nowy tekst.\n"
        assert stored_scans(settings.MEDIA_ROOT) == [name]
        assert old_name not in stored_scans(settings.MEDIA_ROOT)

    def test_arc_64_a_file_posted_with_the_form_wins_over_the_key(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        name = uploaded_scan(searchable_pdf("Z magazynu."))
        data = form_data(work, scan=scan_file("Z formularza."), scan_key=name)

        # Act
        response = admin_client.post(ADD_URL, data)

        # Assert
        assert response.status_code == 302
        document = Typescript.objects.get(work=work).document
        assert document is not None
        assert document.text == "Z formularza.\n"

    @pytest.mark.parametrize(
        "name",
        ["scans/skan.pdf", f"scans/{'0' * 32}/../skan.pdf", f"scans/{'0' * 32}/skan.txt"],
    )
    def test_arc_64_rejects_a_name_outside_the_upload_folders(
        self, admin_client: Client, name: str
    ) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan_key=name))

        # Assert
        assert form_errors(response) == {"scan": [INVALID_KEY]}
        assert not Typescript.objects.exists()

    def test_arc_64_rejects_the_scan_of_another_document(self, admin_client: Client) -> None:
        # Arrange
        name = uploaded_scan(searchable_pdf("Cudzy tekst."))
        TypescriptFactory.create(document=DocumentFactory.create(ocr=True, scan=name))
        work = WorkFactory.create()

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan_key=name))

        # Assert
        assert form_errors(response) == {"scan": [INVALID_KEY]}
        assert not Typescript.objects.filter(work=work).exists()

    def test_arc_64_a_scan_missing_from_storage_is_an_error(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        name = f"scans/{uuid.uuid4().hex}/skan.pdf"

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan_key=name))

        # Assert
        assert form_errors(response) == {"scan": [MISSING_SCAN]}
        assert f'name="scan_key" value="{name}"' not in response.content.decode()

    def test_arc_64_rejected_uploaded_scan_is_deleted(
        self, admin_client: Client, settings: Settings
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        name = uploaded_scan(searchable_pdf(""))

        # Act
        response = admin_client.post(ADD_URL, form_data(work, scan_key=name))

        # Assert
        assert form_errors(response) == {"scan": [SCAN_WITHOUT_TEXT]}
        assert stored_scans(settings.MEDIA_ROOT) == []
        assert f'value="{name}"' not in response.content.decode()

    def test_arc_64_form_with_other_errors_keeps_the_uploaded_scan(
        self, admin_client: Client, settings: Settings
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        name = uploaded_scan(searchable_pdf("Czarny potok."))

        # Act
        response = admin_client.post(ADD_URL, form_data(work, title="", scan_key=name))

        # Assert
        assert form_errors(response) == {"title": ["To pole jest wymagane."]}
        assert f'name="scan_key" value="{name}"' in response.content.decode()
        assert stored_scans(settings.MEDIA_ROOT) == [name]


@pytest.mark.django_db
class TestSignScanUpload:
    @pytest.mark.usefixtures("s3_storage")
    def test_arc_64_signs_a_pdf_upload_to_its_own_folder(self, admin_client: Client) -> None:
        # Act
        response = admin_client.post(SIGN_URL, {"filename": "Czarny potok 1.pdf"})

        # Assert
        assert response.status_code == 200
        upload = response.json()
        assert STORED_SCAN_NAME.fullmatch(upload["name"])
        assert upload["name"].endswith("/Czarny_potok_1.pdf")
        assert upload["url"] == "https://archive.s3.amazonaws.com/"
        assert upload["fields"]["key"] == upload["name"]
        policy = json.loads(base64.b64decode(upload["fields"]["policy"]))
        assert {"Content-Type": "application/pdf"} in policy["conditions"]
        assert ["content-length-range", 1, MAX_SCAN_SIZE] in policy["conditions"]

    @pytest.mark.usefixtures("s3_storage")
    def test_arc_64_change_form_uploads_the_scan_from_the_browser(
        self, admin_client: Client
    ) -> None:
        # Act
        response = admin_client.get(ADD_URL)

        # Assert
        content = response.content.decode()
        assert f'data-direct-upload="{SIGN_URL}"' in content
        assert 'name="scan_key"' in content
        assert "archive/scan_upload.js" in content

    def test_arc_64_without_s3_the_form_posts_the_file(self, admin_client: Client) -> None:
        # Act
        response = admin_client.get(ADD_URL)

        # Assert
        assert "data-direct-upload" not in response.content.decode()

    def test_arc_64_without_s3_there_is_nothing_to_sign(self, admin_client: Client) -> None:
        # Act
        response = admin_client.post(SIGN_URL, {"filename": "skan.pdf"})

        # Assert
        assert response.status_code == 404

    @pytest.mark.usefixtures("s3_storage")
    def test_arc_64_signs_only_a_pdf(self, admin_client: Client) -> None:
        # Act
        response = admin_client.post(SIGN_URL, {"filename": "skan.docx"})

        # Assert
        assert response.status_code == 400
        assert "pdf" in response.json()["error"]

    @pytest.mark.usefixtures("s3_storage")
    def test_arc_64_signs_only_with_a_post(self, admin_client: Client) -> None:
        # Act
        response = admin_client.get(SIGN_URL)

        # Assert
        assert response.status_code == 405

    @pytest.mark.usefixtures("s3_storage")
    def test_arc_64_staff_without_rights_to_documents_cannot_sign(self, client: Client) -> None:
        # Arrange
        user = User.objects.create_user(username="guest", password="secret", is_staff=True)
        client.force_login(user)

        # Act
        response = client.post(SIGN_URL, {"filename": "skan.pdf"})

        # Assert
        assert response.status_code == 403
