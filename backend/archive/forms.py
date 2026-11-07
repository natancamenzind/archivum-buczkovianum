"""Admin forms that need more than the model gives them."""

from functools import partial
from typing import Any

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from archive.models import (
    PDF_EXTENSION,
    TEXT_CONTENT_KINDS,
    Archival,
    ContextualMaterial,
    Document,
    Note,
    SecondaryText,
)
from archive.uploads import load_ocr_upload


class TypedTextField(forms.CharField):
    """Text typed into a textarea, with the LF line breaks fragments count by: browsers send
    CRLF. The stored text then compares equal to an unchanged submission."""

    def to_python(self, value: Any) -> str:
        return str(super().to_python(value)).replace("\r\n", "\n")


class TextUploadForm[M: Archival](forms.ModelForm[M]):
    """An archival item's form, where the editor uploads the item's text (US-WR-04).

    The text is the scan's OCR text layer: one searchable PDF holds both. The item's `Document`
    is created and replaced here, never picked by ID: the admin using this form excludes the
    `document` field. An item without a text requires a scan. Later, uploading a new scan
    replaces the text in place, so its fragments are re-anchored, not lost. Leaving the field
    empty keeps the text.

    `text_kind()` says which kind of text the item gets; here it is always an OCR text.
    """

    scan = forms.FileField(
        label=_("scan"),
        required=False,
        validators=[PDF_EXTENSION],
        help_text=_(
            "A searchable PDF, as an OCR program saves it: the page images with the OCR text "
            "under them. The text is read from it."
        ),
    )

    # Where the form explains a missing or wrong text better than the model's error does.
    text_fields: tuple[str, ...] = ("scan",)
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
        """Load the scan and its text. A scan is required while the item has no text.

        The scan is read only when the rest of the form is valid: reading a long one takes
        seconds, and a rejected form comes back without its file anyway.
        """
        if self.has_error("scan"):
            return
        scan = self.cleaned_data.get("scan")
        document = self.instance.document
        if scan is None:
            if document is None:
                self.add_required_error("scan")
            return
        if self.errors:
            return
        replaced_scan = (document.scan.name or "") if document is not None else ""
        try:
            self.uploaded_document = load_ocr_upload(document, scan)
        except ValidationError as error:
            self.add_error("scan", error)
            return
        self.replaced_scan = replaced_scan
        self.instance.document = self.uploaded_document

    def add_required_error(self, name: str) -> None:
        required = self.fields[name].error_messages["required"]
        self.add_error(name, ValidationError(required, code="required"))

    def add_error(self, field: str | None, error: Any) -> None:
        """Show the model's errors about `document`, which is not on this form, above the form.

        They are left out when the upload fields already have errors that say more, or when a
        scan was uploaded but not read yet (`take_ocr_upload()`): it gives the item its text.
        """
        if (
            isinstance(error, ValidationError)
            and hasattr(error, "error_dict")
            and "document" in error.error_dict
            and "document" not in self.fields
        ):
            messages = error.error_dict.pop("document")
            if self.cleaned_data.get("scan") is None and not any(
                self.has_error(name) for name in (*self.text_fields, NON_FIELD_ERRORS)
            ):
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
            storage = Document.scan.field.storage
            transaction.on_commit(partial(storage.delete, self.replaced_scan))

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

    plain_text = TypedTextField(
        label=_("plain text"),
        required=False,
        strip=False,
        widget=forms.Textarea,
        help_text=_("E.g. a letter transcription."),
    )

    text_fields = ("scan", "plain_text")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        document = self.instance.document
        if document is not None and document.kind == Document.Kind.PLAIN:
            self.fields["plain_text"].initial = document.text

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        kind = self.text_kind()
        if kind == Document.Kind.PLAIN:
            self.take_plain_text()
        elif "plain_text" in self.changed_data and cleaned_data.get("plain_text"):
            self.add_error("plain_text", _("Leave this empty for this kind of content."))
        if kind != Document.Kind.OCR and cleaned_data.get("scan") is not None:
            self.add_error("scan", _("Leave this empty for this kind of content."))
        return cleaned_data

    def take_ocr_upload(self) -> None:
        """Ask for a scan, too, when the item's text is a plain text that becomes OCR."""
        document = self.instance.document
        scan = self.cleaned_data.get("scan")
        if document is not None and document.kind != Document.Kind.OCR and scan is None:
            self.add_required_error("scan")
            return
        super().take_ocr_upload()

    def take_plain_text(self) -> None:
        text = self.cleaned_data.get("plain_text", "")
        if not text.strip():
            self.add_required_error("plain_text")
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


class SecondaryTextForm(PlainTextForm[SecondaryText]):
    """OCR or plain text on the secondary text form (US-WR-06)."""

    plain_text = TypedTextField(
        label=_("plain text"),
        required=False,
        strip=False,
        widget=forms.Textarea,
        help_text=_("Or enter the text here instead of uploading a scan."),
    )

    @property
    def stored_plain_text(self) -> str:
        document = self.instance.document
        return document.text if document and document.kind == Document.Kind.PLAIN else ""

    def text_kind(self) -> str | None:
        return None

    def save(self, commit: bool = True) -> SecondaryText:
        """Save the text only once the admin has validated the work links too."""
        if not commit:
            return super(TextUploadForm, self).save(commit)
        with transaction.atomic():
            self.save_document()
            return super(TextUploadForm, self).save(commit)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super(PlainTextForm, self).clean()
        plain_text = cleaned_data.get("plain_text", "")
        if plain_text and not plain_text.strip():
            plain_text = ""
            cleaned_data["plain_text"] = ""
        if self.has_error("plain_text"):
            return cleaned_data
        if plain_text != self.stored_plain_text:
            uploading = cleaned_data.get("scan") is not None
            if plain_text and uploading:
                self.add_error(
                    "plain_text",
                    _("Upload a scan or enter a plain text, not both."),
                )
                return cleaned_data
            if plain_text:
                self.take_plain_text()
                return cleaned_data
            if not uploading:
                if self.instance.document is None:
                    self.add_error(
                        None,
                        _("Upload a scan or enter a plain text."),
                    )
                else:
                    self.add_required_error("plain_text")
                return cleaned_data
        if cleaned_data.get("scan") is not None or (
            self.instance.document is not None and self.instance.document.kind == Document.Kind.OCR
        ):
            self.take_ocr_upload()
        elif self.instance.document is None:
            self.add_error(
                None,
                _("Upload a scan or enter a plain text."),
            )
        return cleaned_data


class MediaContentForm[M: Note | ContextualMaterial](PlainTextForm[M]):
    """The form of a note or contextual material, whose content is one of five kinds
    (US-WR-05 AC2, US-WR-07 AC2).

    Choosing a content without a text drops the item's text: saving the item deletes it,
    unless it has fragments (`Archival`).
    """

    def text_kind(self) -> str | None:
        return TEXT_CONTENT_KINDS.get(self.cleaned_data.get("content_kind", ""))

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if "content_kind" in cleaned_data and self.text_kind() is None:
            self.drop_text()
        return cleaned_data

    def drop_text(self) -> None:
        document = self.instance.document
        if document is not None:
            self.replaced_scan = document.scan.name or ""
            self.instance.document = None
