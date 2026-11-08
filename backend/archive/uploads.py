"""Uploading the text of an archival item: a scan with an OCR text layer (architecture section 4.4).

The functions here read the scan and load it into a `Document` without saving it.
`archive.forms.TextUploadForm` puts them on an item's admin form.

With S3 storage, the editor's browser sends the scan straight to the bucket
(`presigned_scan_upload()`), and the form posts only its key (`StoredScan`). The scan then
crosses the editor's connection once, and never passes through the app server's request (ARC-64).
"""

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Protocol, runtime_checkable

import pymupdf
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import storages
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils.translation import gettext_lazy as _

from archive.models import Document

TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
# A word the OCR program split with a soft hyphen at the end of a line, and the space after it.
SOFT_HYPHENATED = re.compile(r"\xad\n(\S*)[ \t]*\n?")
# Opens a PDF from a path or from `stream=` bytes. PyMuPDF leaves `Document.__init__`
# unannotated, so its type is stated here.
OPEN_PDF: Callable[..., pymupdf.Document] = pymupdf.Document

# Where the browser uploads a scan: a folder of its own under scans/, so names never collide.
STORED_SCAN_NAME = re.compile(r"scans/[0-9a-f]{32}/[^/]+\.pdf")
# The largest object one S3 POST upload takes.
MAX_SCAN_SIZE = 5 * 1024**3
# How long the browser has to start sending the scan.
UPLOAD_EXPIRES_IN = 3600


@runtime_checkable
class S3Bucket(Protocol):
    """What signing an upload needs of django-storages' `S3Storage`, which ships no types."""

    bucket_name: str
    connection: Any


@dataclass(frozen=True)
class StoredScan:
    """A scan the browser already uploaded to storage, under `name`."""

    name: str


def s3_bucket() -> S3Bucket | None:
    """The S3 storage scans go to, or None for another storage.

    Scans go to the default storage. Its instance is checked, not the lazy `default_storage`
    the field holds: a protocol check does not see through that proxy.
    """
    storage = storages["default"]
    return storage if isinstance(storage, S3Bucket) else None


def direct_upload_enabled() -> bool:
    """Whether the browser uploads scans to storage itself: only S3 takes such uploads."""
    return s3_bucket() is not None


def presigned_scan_upload(filename: str) -> dict[str, Any]:
    """Where and how the browser posts the scan `filename` to S3: `url` and form `fields`, and
    the `name` the form then posts in place of the file.

    The signature allows only a PDF of up to `MAX_SCAN_SIZE`, under this one name.
    """
    bucket = s3_bucket()
    assert bucket is not None
    valid_name = Document.scan.field.storage.get_valid_name(PurePath(filename).name)
    name = f"scans/{uuid.uuid4().hex}/{valid_name}"
    post: dict[str, Any] = bucket.connection.meta.client.generate_presigned_post(
        Bucket=bucket.bucket_name,
        Key=name,
        Fields={"Content-Type": "application/pdf"},
        Conditions=[
            {"Content-Type": "application/pdf"},
            ["content-length-range", 1, MAX_SCAN_SIZE],
        ],
        ExpiresIn=UPLOAD_EXPIRES_IN,
    )
    return {"url": post["url"], "fields": post["fields"], "name": name}


def stored_scan(name: str) -> StoredScan:
    """The scan the browser uploaded under `name`.

    Raise a `ValidationError` unless `name` is where `presigned_scan_upload()` puts a scan, the
    scan is there, and no document has it yet.
    """
    storage = Document.scan.field.storage
    if not STORED_SCAN_NAME.fullmatch(name) or Document.objects.filter(scan=name).exists():
        raise ValidationError(_("The uploaded scan is not valid."), code="invalid")
    if not storage.exists(name):
        raise ValidationError(
            _("The scan did not finish uploading. Choose the file again."), code="missing"
        )
    return StoredScan(name)


def page_text(raw: str) -> str:
    """The text of one scan page, as the archive stores it.

    Trailing spaces are dropped, and a word split with a soft hyphen at a line end is joined
    on the first line, so search finds it. A page with text ends with a line break, so its
    last word never runs into the next page's first.
    """
    text, joined = TRAILING_SPACE.sub("", raw), 1
    # A word split over three lines is joined in two passes.
    while joined:
        text, joined = SOFT_HYPHENATED.subn(r"\1\n", text)
    text = text.strip("\n")
    return f"{text}\n" if text.strip() else ""


def open_pdf(scan: "File[bytes]") -> pymupdf.Document:
    """Open a large upload from the temporary file Django keeps it in, not from a copy of its
    contents in memory: the server has little memory, and scans run to tens of megabytes."""
    if isinstance(scan, TemporaryUploadedFile):
        return OPEN_PDF(scan.temporary_file_path(), filetype="pdf")
    return OPEN_PDF(stream=scan.read(), filetype="pdf")


def read_scan_pages(scan: "File[bytes]") -> list[str]:
    """The text of each page of a PDF's text layer (`page_text()`).

    MuPDF reads it: a book-length scan takes under a second, where pure-Python readers took
    half a minute on the server (ARC-56). Raise a `ValidationError` if the PDF cannot be read
    or has no text on any page.
    """
    try:
        with open_pdf(scan) as pdf:
            pages = [page_text(page.get_text()) for page in pdf]
    except (pymupdf.FileDataError, pymupdf.mupdf.FzErrorBase) as error:
        raise ValidationError(_("The scan is not a readable PDF file."), code="invalid") from error
    finally:
        scan.seek(0)
    if not any(pages):
        raise ValidationError(
            _(
                "The scan has no OCR text. Save it from the OCR program as a searchable PDF, "
                "with the text under the page images, and upload it again."
            ),
            code="no_text",
        )
    return pages


def read_stored_scan_pages(scan: StoredScan) -> list[str]:
    """The page texts of a scan in storage (`read_scan_pages()`), read from a temporary copy on
    disk: the server has too little memory for a book-length scan."""
    storage = Document.scan.field.storage
    with storage.open(scan.name) as stored:
        copy = TemporaryUploadedFile(scan.name, "application/pdf", stored.size, None)
        with copy:
            for chunk in stored.chunks():
                copy.write(chunk)
            copy.seek(0)
            return read_scan_pages(copy)


def load_ocr_upload(document: Document | None, scan: "File[bytes] | StoredScan") -> Document:
    """Read a scan's text layer, and load both into `document` or a new OCR document.

    A `StoredScan` is already in storage, so the document takes its name and saving uploads
    nothing. Errors (`read_scan_pages()`) leave `document` unchanged. Nothing is saved: saving
    the document re-anchors its fragments and re-indexes its owner (`Document.save()`).
    """
    pages = read_stored_scan_pages(scan) if isinstance(scan, StoredScan) else read_scan_pages(scan)
    document = document or Document()
    document.kind = Document.Kind.OCR
    document.scan = scan.name if isinstance(scan, StoredScan) else scan
    document.set_ocr_pages(pages)
    return document
