"""Uploading the text of an archival item: a scan with an OCR text layer (architecture section 4.4).

The functions here read the scan and load it into a `Document` without saving it.
`archive.forms.TextUploadForm` puts them on an item's admin form.
"""

import re
from collections.abc import Callable

import pymupdf
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils.translation import gettext_lazy as _

from archive.models import Document

TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
# A word the OCR program split with a soft hyphen at the end of a line, and the space after it.
SOFT_HYPHENATED = re.compile(r"\xad\n(\S*)[ \t]*\n?")
# Opens a PDF from a path or from `stream=` bytes. PyMuPDF leaves `Document.__init__`
# unannotated, so its type is stated here.
OPEN_PDF: Callable[..., pymupdf.Document] = pymupdf.Document


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


def load_ocr_upload(document: Document | None, scan: "File[bytes]") -> Document:
    """Read a scan's text layer, and load both into `document` or a new OCR document.

    Errors (`read_scan_pages()`) leave `document` unchanged. Nothing is saved: saving the
    document re-anchors its fragments and re-indexes its owner (`Document.save()`).
    """
    pages = read_scan_pages(scan)
    document = document or Document()
    document.kind = Document.Kind.OCR
    document.scan = scan
    document.set_ocr_pages(pages)
    return document
