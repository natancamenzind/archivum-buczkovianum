"""Uploading the text of an archival item: a scan with an OCR text layer (architecture section 4.4).

The functions here read the scan and load it into a `Document` without saving it.
`archive.forms.TextUploadForm` puts them on an item's admin form.
"""

import re

from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from archive.models import Document

TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
# A word the OCR program split with a soft hyphen at the end of a line, and the space after it.
SOFT_HYPHENATED = re.compile(r"\xad\n(\S*)[ \t]*\n?")


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


def read_scan_pages(scan: "File[bytes]") -> list[str]:
    """The text of each page of a PDF's text layer (`page_text()`).

    Raise a `ValidationError` if the PDF cannot be read or has no text on any page.
    """
    try:
        pages = [page_text(page.extract_text()) for page in PdfReader(scan).pages]
    except (PyPdfError, ValueError, KeyError, TypeError) as error:
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
