"""Admin forms that need more than the model gives them."""

from functools import partial
from typing import Any

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from archive.models import (
    PDF_EXTENSION,
    TEXT_CONTENT_KINDS,
    Archival,
    ContextualMaterial,
    Document,
    Note,
)
from archive.uploads import load_ocr_upload

TEXT_EXTENSION = FileExtensionValidator(["txt"])


class TextUploadForm[M: Archival](forms.ModelForm[M]):
    """An archival item's form, where the editor uploads the item's text (US-WR-04).

    The item's `Document` is created and replaced here, never picked by ID: the admin using
    this form excludes the `document` field. An item without a text requires both files.
    Later, uploading both files together replaces the text in place, so its fragments are
    re-anchored, not lost. Leaving both empty keeps the text.

    `text_kind()` says which kind of text the item gets; here it is always an OCR text.
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
    # Where the form explains a missing or wrong text better than the model's error does.
    text_fields: tuple[str, ...] = upload_fields
    # The document loaded from the form, saved with the item.
    uploaded_document: Document | None = None
    # The stored scan the item no longer has, deleted once the save is committed.
    replaced_scan: str = ""

    def text_kind(self) -> str | None:
        """The kind of text the item holds once saved, or None for no text."""
        return Document.Kind.OCR

    def clean(self) -> dict[str, Any]:
        super().clean()
        if self.text_kind() == Document.Kind.OCR:
            self.take_ocr_upload()
        return self.cleaned_data

    def take_ocr_upload(self) -> None:
        """Load the scan and the OCR file. Both are required while the item has no text."""
        if any(self.has_error(name) for name in self.upload_fields):
            return
        scan, ocr_file = self.cleaned_data.get("scan"), self.cleaned_data.get("ocr_file")
        document = self.instance.document
        if scan is None and ocr_file is None:
            if document is None:
                for name in self.upload_fields:
                    required = self.fields[name].error_messages["required"]
                    self.add_error(name, ValidationError(required, code="required"))
            return
        if scan is None or ocr_file is None:
            self.add_error(
                "scan" if scan is None else "ocr_file",
                _("Upload the scan and the OCR file together, so their pages can be compared."),
            )
            return
        replaced_scan = (document.scan.name or "") if document is not None else ""
        try:
            self.uploaded_document = load_ocr_upload(document, scan, ocr_file)
        except ValidationError as error:
            self.add_error(None, error)
            return
        self.replaced_scan = replaced_scan
        self.instance.document = self.uploaded_document

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
            if not any(self.has_error(name) for name in self.text_fields):
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
                storage = Document.scan.field.storage
                transaction.on_commit(partial(storage.delete, self.replaced_scan))
            return super().save(commit)


class PlainTextForm[M: Archival](TextUploadForm[M]):
    """A `TextUploadForm` whose item can also hold a plain text, typed into `plain_text`.

    Subclasses say in `text_kind()` which kind the editor chose. Either kind keeps the item's
    `Document`, so a changed text re-anchors its fragments, whichever kind it was before.
    """

    plain_text = forms.CharField(
        label=_("plain text"),
        required=False,
        strip=False,
        widget=forms.Textarea,
        help_text=_("E.g. a letter transcription."),
    )

    # A form error above the form, such as `MediaContentForm`'s, also says more than the model.
    text_fields = (*TextUploadForm.upload_fields, "plain_text", NON_FIELD_ERRORS)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        document = self.instance.document
        if document is not None and document.kind == Document.Kind.PLAIN:
            self.fields["plain_text"].initial = document.text

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        kind = self.text_kind()
        if kind == Document.Kind.OCR:
            return cleaned_data
        for name in self.upload_fields:
            if cleaned_data.get(name) is not None:
                self.add_error(name, _("Leave this empty for this kind of content."))
        if kind == Document.Kind.PLAIN:
            self.take_plain_text()
        return cleaned_data

    def take_plain_text(self) -> None:
        # Browsers send a textarea's line breaks as CRLF; fragments count characters.
        text = self.cleaned_data.get("plain_text", "").replace("\r\n", "\n")
        if not text.strip():
            required = self.fields["plain_text"].error_messages["required"]
            self.add_error("plain_text", ValidationError(required, code="required"))
            return
        document = self.instance.document
        if document is not None and document.kind == Document.Kind.PLAIN and document.text == text:
            return
        document = document or Document()
        self.replaced_scan = document.scan.name or ""
        document.kind = Document.Kind.PLAIN
        document.scan = None
        document.text = text
        document.page_offsets = []
        self.uploaded_document = self.instance.document = document


class MediaContentForm[M: Note | ContextualMaterial](PlainTextForm[M]):
    """The form of a note or contextual material, whose content is one of five kinds
    (US-WR-05 AC2, US-WR-07 AC2).

    Choosing a content without a text deletes the item's document, unless its fragments would
    go with it.
    """

    # The text the item no longer has, deleted once the item is saved without it.
    removed_document: Document | None = None

    def text_kind(self) -> str | None:
        return TEXT_CONTENT_KINDS.get(self.cleaned_data.get("content_kind", ""))

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if "content_kind" in cleaned_data and self.text_kind() is None:
            self.drop_text()
        return cleaned_data

    def drop_text(self) -> None:
        """Drop the item's text, but never its fragments: the editor deletes those first."""
        document = self.instance.document
        if document is None:
            return
        count = document.fragments.count()
        if count:
            message = ngettext(
                "The text of this %(item)s has %(count)d tagged fragment.",
                "The text of this %(item)s has %(count)d tagged fragments.",
                count,
            ) % {"item": self.instance._meta.verbose_name, "count": count}
            self.add_error(
                None,
                f"{message} {_('Delete its fragments before choosing another kind of content.')}",
            )
            return
        self.removed_document = document
        self.replaced_scan = document.scan.name or ""
        self.instance.document = None

    def save(self, commit: bool = True) -> M:
        """Delete the dropped text after the item is saved without it."""
        item = super().save(commit)
        if self.removed_document is not None:
            transaction.on_commit(self.removed_document.delete)
        return item
