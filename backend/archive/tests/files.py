"""Uploaded files built in memory for tests: no large fixtures in the repository."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfWriter


def scan_file(pages: int, name: str = "scan.pdf") -> SimpleUploadedFile:
    """A PDF of `pages` blank pages."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    content = io.BytesIO()
    writer.write(content)
    return SimpleUploadedFile(name, content.getvalue(), content_type="application/pdf")


def ocr_file(*pages: str, name: str = "scan.txt", encoding: str = "utf-8") -> SimpleUploadedFile:
    """Tesseract output: the pages, each followed by a form feed."""
    content = "".join(f"{page}\f" for page in pages).encode(encoding)
    return SimpleUploadedFile(name, content, content_type="text/plain")
