"""Editor panel. Plain Django admin, set up so editors cannot break the data by accident."""

from collections.abc import Sequence
from typing import Any, ClassVar

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from archive.models import (
    ContextualMaterial,
    Document,
    Edition,
    Fragment,
    Institution,
    MaterialWorkLink,
    Note,
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
class WorkAdmin(admin.ModelAdmin[Work]):
    list_display = ("title", "genre", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title",)
    autocomplete_fields = ("tags",)
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("title",)}
    inlines = (EditionInline,)


@admin.register(Typescript)
class TypescriptAdmin(admin.ModelAdmin[Typescript]):
    list_display = ("title", "work", "shelfmark", "is_main", "status", "updated_at")
    list_filter = ("status", "is_main", "work")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("work", "institution", "tags")
    raw_id_fields = ("document",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin[Note]):
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


@admin.register(SecondaryText)
class SecondaryTextAdmin(admin.ModelAdmin[SecondaryText]):
    list_display = ("title", "kind", "author", "status", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("title", "author")
    autocomplete_fields = ("institution", "tags")
    raw_id_fields = ("document",)
    inlines = (SecondaryTextWorkLinkInline,)


class MaterialWorkLinkInline(admin.TabularInline[MaterialWorkLink, ContextualMaterial]):
    model = MaterialWorkLink
    extra = 0
    min_num = 1
    autocomplete_fields = ("work", "tags")


@admin.register(ContextualMaterial)
class ContextualMaterialAdmin(admin.ModelAdmin[ContextualMaterial]):
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

    def get_readonly_fields(
        self, request: HttpRequest, obj: Document | None = None
    ) -> tuple[str, ...]:
        """An OCR text changes only with a new OCR file, which also sets its page boundaries."""
        if obj is not None and obj.kind == Document.Kind.OCR:
            return ("text",)
        return ()


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin[Fragment]):
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
