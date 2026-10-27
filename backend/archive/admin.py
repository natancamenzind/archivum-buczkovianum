"""Editor panel. Plain Django admin, set up so editors cannot break the data by accident."""

from collections.abc import Sequence
from typing import Any, ClassVar

from django.contrib import admin
from django.db import models
from django.db.models import QuerySet
from django.forms import BaseInlineFormSet, ModelForm
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

from archive.forms import OcrOrPlainTextForm, TextUploadForm
from archive.models import (
    ContextualMaterial,
    Document,
    Edition,
    Fragment,
    Institution,
    MaterialWorkLink,
    Note,
    Publishable,
    SecondaryText,
    SecondaryTextWorkLink,
    SiteSettings,
    Tag,
    TeamMember,
    Typescript,
    Work,
)

# Bulk deletes skip each object's `delete()` and its side effects (architecture section 6).
admin.site.disable_action("delete_selected")


class SearchIndexedAdmin[M: Publishable | Fragment](admin.ModelAdmin[M]):
    def save_related(
        self, request: HttpRequest, form: ModelForm[M], formsets: Any, change: bool
    ) -> None:
        """Index again once tags, works and work links are saved: `save()` ran before them.

        Tags are indexed again too: their entries list the works they refer to.
        """
        super().save_related(request, form, formsets, change)
        form.instance.update_search_entry()
        Tag.update_search_entries()


class MediaContentAdmin[M: Note | ContextualMaterial](SearchIndexedAdmin[M]):
    # Django 6.0 makes https the default scheme for URLs typed without one; opt in now.
    formfield_overrides: ClassVar[dict[type[models.Field[Any, Any]], dict[str, Any]]] = {
        models.URLField: {"assume_scheme": "https"},
    }


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin[Institution]):
    list_display = ("abbreviation", "name")
    search_fields = ("abbreviation", "name")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin[Tag]):
    list_display = ("title", "kind", "status", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("title",)
    autocomplete_fields = ("related",)
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("title",)}

    def get_deleted_objects(
        self, objs: Sequence[Tag] | QuerySet[Tag], request: HttpRequest
    ) -> tuple[list[Any], dict[str, int], set[str], list[Any]]:
        """Refuse to delete a tag in use and list where it is used (US-WR-08 AC3)."""
        deleted, counts, permissions, protected = super().get_deleted_objects(objs, request)
        protected += [f"{item._meta.verbose_name}: {item}" for tag in objs for item in tag.usages()]
        return deleted, counts, permissions, protected


class EditionInline(admin.TabularInline[Edition, Work]):
    model = Edition
    extra = 0


@admin.register(Work)
class WorkAdmin(SearchIndexedAdmin[Work]):
    list_display = ("title", "genre", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title",)
    autocomplete_fields = ("tags",)
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("title",)}
    inlines = (EditionInline,)


class TextUploadAdmin[M: Typescript | SecondaryText](SearchIndexedAdmin[M]):
    """The admin of an item whose form uploads its text (`TextUploadForm`)."""

    readonly_fields = ("current_scan", "page_count")

    def save_model(self, request: HttpRequest, obj: M, form: Any, change: bool) -> None:
        """Save the uploaded text first: the item refers to it."""
        form.save_document()
        super().save_model(request, obj, form, change)

    @admin.display(description=_("current scan"))
    def current_scan(self, obj: M) -> SafeString | None:
        if obj.document is None or not obj.document.scan:
            return None
        scan = obj.document.scan
        return format_html('<a href="{}">{}</a>', scan.url, scan.name)

    @admin.display(description=_("pages"))
    def page_count(self, obj: M) -> int | None:
        return obj.document.page_count if obj.document else None


class TypescriptForm(TextUploadForm[Typescript]):
    class Meta:
        model = Typescript
        exclude = ("document",)


@admin.register(Typescript)
class TypescriptAdmin(TextUploadAdmin[Typescript]):
    list_display = ("title", "work", "shelfmark", "is_main", "status", "updated_at")
    list_filter = ("status", "is_main", "work")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("work", "institution", "tags")
    form = TypescriptForm


@admin.register(Note)
class NoteAdmin(MediaContentAdmin[Note]):
    list_display = ("title", "content_kind", "shelfmark", "status", "updated_at")
    list_filter = ("status", "content_kind", "works")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("works", "institution", "tags")
    raw_id_fields = ("document",)


class SecondaryTextWorkLinkInline(admin.TabularInline[SecondaryTextWorkLink, SecondaryText]):
    model = SecondaryTextWorkLink
    extra = 0
    min_num = 1
    autocomplete_fields = ("work", "tags")

    def get_formset(
        self, request: HttpRequest, obj: SecondaryText | None = None, **kwargs: Any
    ) -> type[BaseInlineFormSet[SecondaryTextWorkLink, SecondaryText, Any]]:
        """Require at least one work, also when every link is deleted (US-WR-06 AC2)."""
        return super().get_formset(request, obj, validate_min=True, **kwargs)


class SecondaryTextForm(OcrOrPlainTextForm[SecondaryText]):
    class Meta:
        model = SecondaryText
        exclude = ("document",)


@admin.register(SecondaryText)
class SecondaryTextAdmin(TextUploadAdmin[SecondaryText]):
    list_display = ("title", "kind", "author", "status", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("title", "author")
    autocomplete_fields = ("institution", "tags")
    form = SecondaryTextForm
    inlines = (SecondaryTextWorkLinkInline,)


class MaterialWorkLinkInline(admin.TabularInline[MaterialWorkLink, ContextualMaterial]):
    model = MaterialWorkLink
    extra = 0
    min_num = 1
    autocomplete_fields = ("work", "tags")


@admin.register(ContextualMaterial)
class ContextualMaterialAdmin(MediaContentAdmin[ContextualMaterial]):
    list_display = ("title", "content_kind", "shelfmark", "status", "updated_at")
    list_filter = ("status", "content_kind")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("institution", "tags")
    raw_id_fields = ("document",)
    inlines = (MaterialWorkLinkInline,)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin[Document]):
    list_display = ("__str__", "kind", "page_count", "updated_at")
    list_filter = ("kind",)
    list_select_related = tuple(Document.owner_accessors())

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        """Hide documents from the admin menu: an item's form uploads its text (US-WR-04).

        The admin stays registered for the `document` lookup of the forms steps 7 to 9 replace.
        """
        return {}

    def get_readonly_fields(
        self, request: HttpRequest, obj: Document | None = None
    ) -> tuple[str, ...]:
        """An OCR text changes only with a new OCR file, which also sets its page boundaries."""
        if obj is not None and obj.kind == Document.Kind.OCR:
            return ("text",)
        return ()


@admin.register(Fragment)
class FragmentAdmin(SearchIndexedAdmin[Fragment]):
    list_display = ("__str__", "document", "location", "is_featured", "needs_review")
    list_filter = ("needs_review", "is_featured")
    list_select_related = tuple(f"document__{owner}" for owner in Document.owner_accessors())
    search_fields = ("quote", "description")
    ordering = ("-needs_review", "document", "start")
    readonly_fields = ("document", "quote")
    autocomplete_fields = ("tags",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Fragments are created by selecting text in the tagger."""
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin[SiteSettings]):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: SiteSettings | None = None) -> bool:
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin[TeamMember]):
    list_display = ("name", "role", "group", "order")
    list_editable = ("order",)
    list_filter = ("group",)
