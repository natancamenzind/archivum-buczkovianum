"""Uploading the text of an archival item: a scan and its OCR file (architecture section 4.4).

The functions here check the files and load them into a `Document` without saving it.
`archive.forms.TextUploadForm` puts them on an item's admin form.
"""

from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from archive.models import Document


def pdf_page_count(scan: "File[bytes]") -> int:
    """The number of pages of a PDF file. Raise a `ValidationError` if it cannot be read."""
    try:
        return len(PdfReader(scan).pages)
    except (PyPdfError, ValueError, KeyError, TypeError) as error:
        raise ValidationError(_("The scan is not a readable PDF file."), code="invalid") from error
    finally:
        scan.seek(0)


def read_ocr_file(ocr_file: "File[bytes]") -> str:
    """The text of an OCR file. Raise a `ValidationError` if it is not UTF-8."""
    try:
        return bytes(ocr_file.read()).decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError(
            _("The OCR file is not UTF-8 text. Save it as UTF-8 and upload it again."),
            code="invalid",
        ) from error
    finally:
        ocr_file.seek(0)


def load_ocr_upload(
    document: Document | None, scan: "File[bytes]", ocr_file: "File[bytes]"
) -> Document:
    """Check a scan and its OCR file, and load them into `document` or a new OCR document.

    The OCR file must have as many pages as the scan (US-WR-04 AC2). Errors are keyed by
    `scan` and `ocr_file`, and leave `document` unchanged. Nothing is saved: saving the
    document re-anchors its fragments and re-indexes its owner (`Document.save()`).
    """
    errors: dict[str, ValidationError] = {}
    scan_pages = raw = None
    try:
        scan_pages = pdf_page_count(scan)
    except ValidationError as error:
        errors["scan"] = error
    try:
        raw = read_ocr_file(ocr_file)
    except ValidationError as error:
        errors["ocr_file"] = error
    if errors:
        raise ValidationError(errors)
    assert scan_pages is not None and raw is not None
    loaded = Document(kind=Document.Kind.OCR)
    loaded.set_ocr_text(raw)
    if loaded.page_count != scan_pages:
        raise ValidationError(
            {
                "ocr_file": ValidationError(
                    ngettext(
                        "The scan has %(scan)d page, the OCR file has %(ocr)d.",
                        "The scan has %(scan)d pages, the OCR file has %(ocr)d.",
                        scan_pages,
                    ),
                    code="page_count",
                    params={"scan": scan_pages, "ocr": loaded.page_count},
                )
            }
        )
    document = document or Document()
    document.kind = Document.Kind.OCR
    document.scan = scan
    document.text = loaded.text
    document.page_offsets = loaded.page_offsets
    return document
