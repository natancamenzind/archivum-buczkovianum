"""Uploaded files built in memory for tests: no large fixtures in the repository."""

import io
from pathlib import PurePath

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    ContentStream,
    DictionaryObject,
    NameObject,
    NumberObject,
)

# Polish letters missing from WinAnsiEncoding, at control codes from 1: text never uses them.
POLISH_GLYPHS = {
    "ą": "aogonek",
    "ć": "cacute",
    "ę": "eogonek",
    "ł": "lslash",
    "ń": "nacute",
    "ś": "sacute",
    "ź": "zacute",
    "ż": "zdotaccent",
    "Ą": "Aogonek",
    "Ć": "Cacute",
    "Ę": "Eogonek",
    "Ł": "Lslash",
    "Ń": "Nacute",
    "Ś": "Sacute",
    "Ź": "Zacute",
    "Ż": "Zdotaccent",
}
POLISH_CODES = {letter: 0x01 + index for index, letter in enumerate(POLISH_GLYPHS)}

# The editor panel's error for a scan with no OCR text (`archive.uploads.read_scan_pages`).
SCAN_WITHOUT_TEXT = (
    "Skan nie ma tekstu OCR. Zapisz go w programie do OCR jako przeszukiwalny PDF, "
    "z tekstem pod obrazami stron, i wgraj ponownie."
)


def helvetica() -> DictionaryObject:
    """Helvetica, which every PDF reader has, encoded so that it writes Polish text."""
    differences = ArrayObject([NumberObject(0x01)])
    differences.extend(NameObject(f"/{glyph}") for glyph in POLISH_GLYPHS.values())
    encoding = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Encoding"),
            NameObject("/BaseEncoding"): NameObject("/WinAnsiEncoding"),
            NameObject("/Differences"): differences,
        }
    )
    return DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): encoding,
        }
    )


def pdf_string(line: str) -> bytes:
    """`line` as a PDF string literal in `helvetica()`'s encoding."""
    encoded = b"".join(
        bytes([POLISH_CODES[char]]) if char in POLISH_CODES else char.encode("cp1252")
        for char in line
    )
    escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return b"(" + escaped + b")"


def searchable_pdf(*pages: str) -> bytes:
    """A PDF whose pages carry these texts, line by line, as an OCR program's text layer does.

    An empty string is a page without text.
    """
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): helvetica()})}
        )
        lines = b" T* ".join(pdf_string(line) + b" Tj" for line in text.splitlines())
        content = ContentStream(None, writer)
        content.set_data(b"BT /F1 11 Tf 14 TL 56 780 Td " + lines + b" ET" if lines else b"")
        page.replace_contents(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def scan_file(*pages: str, name: str = "scan.pdf") -> SimpleUploadedFile:
    """A searchable PDF scan with these page texts (`searchable_pdf()`)."""
    return SimpleUploadedFile(name, searchable_pdf(*pages), content_type="application/pdf")


IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def image_file(name: str, size: tuple[int, int] = (4, 2)) -> SimpleUploadedFile:
    """A small image in the format its name's extension gives."""
    image_format = IMAGE_FORMATS[PurePath(name).suffix]
    output = io.BytesIO()
    Image.new("RGB", size, "sienna").save(output, format=image_format)
    return SimpleUploadedFile(name, output.getvalue(), content_type=f"image/{image_format.lower()}")
