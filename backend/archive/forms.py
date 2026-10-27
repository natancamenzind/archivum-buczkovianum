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
    this form excludes the `document` field. A new item that needs a text requires both files.
    Later, uploading both files together replaces the text in place, so its fragments are
    re-anchored, not lost. Leaving both empty keeps the text.

    Plain text (`Document.Kind.PLAIN`) is not uploaded here yet (steps 7 and 8).
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
    # The document loaded from the files, saved with the item.
    uploaded_document: Document | None = None
    # The stored scan the upload replaces, deleted once the new one is committed.
    replaced_scan: str = ""

    def clean(self) -> dict[str, Any]:
        super().clean()
        cleaned_data = self.cleaned_data
        if any(self.has_error(name) for name in self.upload_fields):
            return cleaned_data
        scan, ocr_file = (cleaned_data.get(name) for name in self.upload_fields)
        if scan is None and ocr_file is None:
            if self.instance.document is None and self.instance.document_required:
                for name in self.upload_fields:
                    required = self.fields[name].error_messages["required"]
                    self.add_error(name, ValidationError(required, code="required"))
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

    def add_error(self, field: str | None, error: Any) -> None:
        """Show the model's errors about `document`, which is not on this form, above the form.

        They are left out when the upload fields already have errors that say more.
        """
        if (
            isinstance(error, ValidationError)
            and hasattr(error, "error_dict")
            and "document" in error.error_dict
            and "document" not in self.fields
        ):
            messages = error.error_dict.pop("document")
            if not any(self.has_error(name) for name in self.upload_fields):
                error.error_dict.setdefault(NON_FIELD_ERRORS, []).extend(messages)
            if not error.error_dict:
                return
        super().add_error(field, error)

    def save(self, commit: bool = True) -> M:
        """Save the uploaded document first, since the item refers to it.

        Saving a replaced text re-anchors its fragments and re-indexes the item. The admin
        saves the form and the item in one transaction, so a failure undoes both. The replaced
        scan is deleted only after that transaction commits.
        """
        with transaction.atomic():
            if self.uploaded_document is not None:
                self.uploaded_document.save()
                if self.replaced_scan:
                    storage = self.uploaded_document.scan.storage
                    transaction.on_commit(partial(storage.delete, self.replaced_scan))
            return super().save(commit)
