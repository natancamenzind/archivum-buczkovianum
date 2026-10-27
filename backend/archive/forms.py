"""Admin forms that need more than the model gives them."""

from functools import partial
from typing import Any

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from archive.models import PDF_EXTENSION, Archival, Document
from archive.uploads import load_ocr_upload

TEXT_EXTENSION = FileExtensionValidator(["txt"])


class TextUploadForm[M: Archival](forms.ModelForm[M]):
    """An archival item's form, where the editor uploads the item's text (US-WR-04).

    The item's `Document` is created and replaced here, never picked by ID: the admin using
    this form excludes the `document` field. The text is a scan with its OCR file or, on an
    `OcrOrPlainTextForm`, a plain text typed into the form. A new item that needs a text
    requires one of them. Later, a new text replaces the old one in the same `Document`, so
    its fragments are re-anchored, not lost. Leaving the files empty and the plain text as it
    is keeps the text.
    """

    scan = forms.FileField(
        label=_("scan"),
        required=False,
        validators=[PDF_EXTENSION],
        help_text=_("PDF file."),
    )
    ocr_file = forms.FileField(
        label=_("OCR file"),
        required=False,
        validators=[TEXT_EXTENSION],
        help_text=_(
            "UTF-8 .txt file, as Tesseract writes it: a form feed between pages. "
            "It must have as many pages as the scan."
        ),
    )

    upload_fields = ("scan", "ocr_file")
    # The document loaded from the files or the plain text, saved with the item.
    uploaded_document: Document | None = None
    # The stored scan the upload replaces, deleted once the new one is committed.
    replaced_scan: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.allows_plain_text:
            self.fields["plain_text"].initial = self.stored_plain_text

    @property
    def allows_plain_text(self) -> bool:
        return "plain_text" in self.fields

    @property
    def text_fields(self) -> list[str]:
        """The fields that set the text: the files, and the plain text where it is allowed."""
        return (
            [*self.upload_fields, "plain_text"] if self.allows_plain_text else [*self.upload_fields]
        )

    @property
    def stored_plain_text(self) -> str:
        document = self.instance.document
        return document.text if document and document.kind == Document.Kind.PLAIN else ""

    def clean_plain_text(self) -> str:
        """The text with a browser's CRLF line breaks as LF, the way it is stored.

        Only white space counts as no text.
        """
        text: str = self.cleaned_data["plain_text"]
        return text.replace("\r\n", "\n") if text.strip() else ""

    def clean(self) -> dict[str, Any]:
        super().clean()
        cleaned_data = self.cleaned_data
        if any(self.has_error(name) for name in self.text_fields):
            return cleaned_data
        scan, ocr_file = (cleaned_data.get(name) for name in self.upload_fields)
        plain_text = cleaned_data.get("plain_text", "")
        plain_text_changed = self.allows_plain_text and plain_text != self.stored_plain_text
        if scan is None and ocr_file is None:
            if plain_text_changed and plain_text:
                self.load_plain_text(plain_text)
            elif plain_text_changed:
                required = self.fields["plain_text"].error_messages["required"]
                self.add_error("plain_text", ValidationError(required, code="required"))
            elif self.instance.document is None and self.instance.document_required:
                if self.allows_plain_text:
                    self.add_error(
                        None, _("Upload a scan and its OCR file, or enter a plain text.")
                    )
                    return cleaned_data
                for name in self.upload_fields:
                    required = self.fields[name].error_messages["required"]
                    self.add_error(name, ValidationError(required, code="required"))
            return cleaned_data
        if plain_text_changed and plain_text:
            self.add_error(
                None, _("Upload a scan and its OCR file, or enter a plain text, not both.")
            )
            return cleaned_data
        if scan is None or ocr_file is None:
            self.add_error(
                "scan" if scan is None else "ocr_file",
                _("Upload the scan and the OCR file together, so their pages can be compared."),
            )
            return cleaned_data
        document = self.instance.document
        replaced_scan = (document.scan.name or "") if document is not None else ""
        try:
            self.uploaded_document = load_ocr_upload(document, scan, ocr_file)
        except ValidationError as error:
            self.add_error(None, error)
            return cleaned_data
        self.replaced_scan = replaced_scan
        self.instance.document = self.uploaded_document
        return cleaned_data

    def load_plain_text(self, text: str) -> None:
        """Put `text` into the item's document as a plain text, dropping any scan it had."""
        document = self.instance.document or Document()
        self.replaced_scan = document.scan.name or ""
        document.kind = Document.Kind.PLAIN
        document.scan = ""
        document.text = text
        document.page_offsets = []
        self.uploaded_document = self.instance.document = document

    def add_error(self, field: str | None, error: Any) -> None:
        """Show the model's errors about `document`, which is not on this form, above the form.

        They are left out when the text fields, or this form's own errors about the text,
        already say more.
        """
        if (
            isinstance(error, ValidationError)
            and hasattr(error, "error_dict")
            and "document" in error.error_dict
            and "document" not in self.fields
        ):
            messages = error.error_dict.pop("document")
            if not any(self.has_error(name) for name in (*self.text_fields, NON_FIELD_ERRORS)):
                error.error_dict.setdefault(NON_FIELD_ERRORS, []).extend(messages)
            if not error.error_dict:
                return
        super().add_error(field, error)

    def save_document(self) -> None:
        """Save the uploaded document, which the item refers to, before the item.

        Saving a replaced text re-anchors its fragments and re-indexes the item. The replaced
        scan is deleted only after the transaction commits.
        """
        if self.uploaded_document is None:
            return
        self.uploaded_document.save()
        if self.replaced_scan:
            storage = self.uploaded_document.scan.storage
            transaction.on_commit(partial(storage.delete, self.replaced_scan))

    def save(self, commit: bool = True) -> M:
        """Save the uploaded document and the item together, so a failure undoes both.

        With `commit=False` nothing is saved: the admin saves the item only once its inlines
        are valid too, and calls `save_document()` then (`TextUploadAdmin.save_model()`).
        """
        if not commit:
            return super().save(commit)
        with transaction.atomic():
            self.save_document()
            return super().save(commit)


class OcrOrPlainTextForm[M: Archival](TextUploadForm[M]):
    """A `TextUploadForm` that also takes the text as plain text (US-WR-06 AC1)."""

    plain_text = forms.CharField(
        label=_("plain text"),
        required=False,
        strip=False,
        widget=forms.Textarea,
        help_text=_("Or enter the text here instead of uploading a scan and an OCR file."),
    )
