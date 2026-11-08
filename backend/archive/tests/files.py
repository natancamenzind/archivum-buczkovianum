"""Uploaded files built in memory for tests: no large fixtures in the repository."""

import io
from pathlib import PurePath

from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
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


def standard_font(name: str) -> DictionaryObject:
    """A font every PDF reader has, such as Helvetica, encoded so that it writes Polish text.

    WinAnsiEncoding names 0xAD a hyphen, so it is renamed a soft hyphen, as OCR programs
    declare it.
    """
    differences = ArrayObject([NumberObject(0x01)])
    differences.extend(NameObject(f"/{glyph}") for glyph in POLISH_GLYPHS.values())
    differences.extend([NumberObject(0xAD), NameObject("/sfthyphen")])
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
            NameObject("/BaseFont"): NameObject(f"/{name}"),
            NameObject("/Encoding"): encoding,
        }
    )


def pdf_string(line: str) -> bytes:
    """`line` as a PDF string literal in `standard_font()`'s encoding."""
    encoded = b"".join(
        bytes([POLISH_CODES[char]]) if char in POLISH_CODES else char.encode("cp1252")
        for char in line
    )
    escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return b"(" + escaped + b")"


def page_content(text: str, word_by_word: bool) -> bytes:
    """The content stream that writes `text`: line by line, or each word on its own at its
    place on the page, as OCR programs write every word they recognised."""
    lines = text.splitlines()
    if not word_by_word:
        shown = b" T* ".join(pdf_string(line) + b" Tj" for line in lines)
        return b"BT /F1 11 Tf 14 TL 56 780 Td " + shown + b" ET" if shown else b""
    words = []
    for number, line in enumerate(lines):
        x = 56
        for word in line.split(" "):
            position = b"1 0 0 1 %d %d Tm " % (x, 780 - 8 * number)
            words.append(b"BT /F2 5 Tf " + position + pdf_string(word) + b" Tj ET")
            # Every Courier letter is 0.6 em wide: 3 points at 5 points. One letter's width
            # is left between words, as a space.
            x += 3 * (len(word) + 1)
    return b" ".join(words)


def searchable_pdf(*pages: str, word_by_word: bool = False) -> bytes:
    """A PDF whose pages carry these texts, line by line, as an OCR program's text layer does.

    An empty string is a page without text.
    """
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=595, height=842)
        fonts = {
            NameObject("/F1"): standard_font("Helvetica"),
            NameObject("/F2"): standard_font("Courier"),
        }
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject(fonts)}
        )
        content = ContentStream(None, writer)
        content.set_data(page_content(text, word_by_word))
        page.replace_contents(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def scan_file(
    *pages: str, name: str = "scan.pdf", word_by_word: bool = False
) -> SimpleUploadedFile:
    """A searchable PDF scan with these page texts (`searchable_pdf()`)."""
    content = searchable_pdf(*pages, word_by_word=word_by_word)
    return SimpleUploadedFile(name, content, content_type="application/pdf")


def temporary_upload(content: bytes, name: str = "scan.pdf") -> TemporaryUploadedFile:
    """`content` uploaded as Django keeps a large upload: in a temporary file on disk."""
    upload = TemporaryUploadedFile(name, "application/pdf", len(content), None)
    upload.write(content)
    upload.seek(0)
    return upload


def image_file(
    name: str, size: tuple[int, int] = (4, 2), exif: Image.Exif | None = None
) -> SimpleUploadedFile:
    """A small image in the format its name's extension gives, with `exif` if given."""
    image_format = Image.registered_extensions()[PurePath(name).suffix]
    output = io.BytesIO()
    Image.new("RGB", size, "sienna").save(output, format=image_format, exif=exif or Image.Exif())
    return SimpleUploadedFile(name, output.getvalue(), content_type=f"image/{image_format.lower()}")
