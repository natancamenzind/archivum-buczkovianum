"""Editor panel. Plain Django admin, set up so editors cannot break the data by accident."""

from collections.abc import Sequence
from typing import Any, ClassVar

from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files import File
from django.db import models
from django.db.models import QuerySet
from django.forms import BaseInlineFormSet, ModelForm
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from archive.forms import MediaContentForm, SecondaryTextForm, TextUploadForm
from archive.models import (
    PDF_EXTENSION,
    BibliographyEntry,
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
from archive.tagger import tagger_fragments, tagger_pages
from archive.uploads import direct_upload_enabled, presigned_scan_upload

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


class TaggerLinkMixin[M: Typescript | Note | SecondaryText | ContextualMaterial]:
    @admin.display(description=_("fragments"))
    def tag_fragments(self, obj: M) -> SafeString | str:
        document = obj.document
        if obj.pk is None or document is None or not document.offers_tagger():
            return "—"
        url = reverse("admin:archive_document_tagger", args=[obj.document_id])
        return format_html('<a class="button" href="{}">{}</a>', url, _("Tag fragments"))


class TextUploadAdmin[M: Typescript | Note | SecondaryText | ContextualMaterial](
    TaggerLinkMixin[M], SearchIndexedAdmin[M]
):
    """The admin of an item whose form uploads its text (`TextUploadForm`)."""

    readonly_fields = ("current_scan", "page_count")

    def get_readonly_fields(self, request: HttpRequest, obj: M | None = None) -> tuple[str, ...]:
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.pk is not None:
            fields.append("tag_fragments")
        return tuple(fields)

    @admin.display(description=_("current scan"))
    def current_scan(self, obj: M) -> SafeString | None:
        if obj.document is None or not obj.document.scan:
            return None
        scan = obj.document.scan
        return format_html('<a href="{}">{}</a>', scan.url, scan.name)

    @admin.display(description=_("pages"))
    def page_count(self, obj: M) -> int | None:
        if obj.document is None or obj.document.kind != Document.Kind.OCR:
            return None
        return obj.document.page_count


class MediaContentAdmin[M: Note | ContextualMaterial](TextUploadAdmin[M]):
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


class BibliographyEntryInline(admin.TabularInline[BibliographyEntry, Work]):
    model = BibliographyEntry
    extra = 0
    fields = ("text",)


@admin.register(Work)
class WorkAdmin(SearchIndexedAdmin[Work]):
    list_display = ("title", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title",)
    autocomplete_fields = ("tags",)
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("title",)}
    inlines = (EditionInline, BibliographyEntryInline)


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


class NoteForm(MediaContentForm[Note]):
    class Meta:
        model = Note
        exclude = ("document",)


@admin.register(Note)
class NoteAdmin(MediaContentAdmin[Note]):
    list_display = ("title", "content_kind", "shelfmark", "status", "updated_at")
    list_filter = ("status", "content_kind", "works")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("works", "institution", "tags")
    form = NoteForm


class WorkLinkInline[
    L: SecondaryTextWorkLink | MaterialWorkLink,
    I: SecondaryText | ContextualMaterial,
](admin.TabularInline[L, I]):
    extra = 0
    min_num = 1
    autocomplete_fields = ("work", "tags")

    def get_formset(
        self, request: HttpRequest, obj: I | None = None, **kwargs: Any
    ) -> type[BaseInlineFormSet[L, I, Any]]:
        """Require at least one work, also when every link is deleted (US-WR-06 AC2, US-WR-07
        AC3)."""
        return super().get_formset(request, obj, validate_min=True, **kwargs)


class SecondaryTextWorkLinkInline(WorkLinkInline[SecondaryTextWorkLink, SecondaryText]):
    model = SecondaryTextWorkLink


class SecondaryTextAdminForm(SecondaryTextForm):
    class Meta:
        model = SecondaryText
        exclude = ("document",)


@admin.register(SecondaryText)
class SecondaryTextAdmin(TextUploadAdmin[SecondaryText]):
    list_display = ("title", "kind", "author", "status", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("title", "author")
    autocomplete_fields = ("institution", "tags")
    form = SecondaryTextAdminForm
    inlines = (SecondaryTextWorkLinkInline,)
    formfield_overrides = MediaContentAdmin.formfield_overrides

    def save_model(
        self, request: HttpRequest, obj: SecondaryText, form: SecondaryTextAdminForm, change: bool
    ) -> None:
        """Save the uploaded text first: the item refers to it."""
        form.save_document()
        super().save_model(request, obj, form, change)


class MaterialWorkLinkInline(WorkLinkInline[MaterialWorkLink, ContextualMaterial]):
    model = MaterialWorkLink


class ContextualMaterialForm(MediaContentForm[ContextualMaterial]):
    class Meta:
        model = ContextualMaterial
        exclude = ("document",)


@admin.register(ContextualMaterial)
class ContextualMaterialAdmin(MediaContentAdmin[ContextualMaterial]):
    list_display = ("title", "content_kind", "shelfmark", "status", "updated_at")
    list_filter = ("status", "content_kind")
    search_fields = ("title", "shelfmark")
    autocomplete_fields = ("institution", "tags")
    form = ContextualMaterialForm
    inlines = (MaterialWorkLinkInline,)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin[Document]):
    list_display = ("__str__", "kind", "page_count", "updated_at")
    list_filter = ("kind",)
    list_select_related = tuple(Document.owner_accessors())

    def get_urls(self) -> list[Any]:
        return [
            path(
                "<int:object_id>/tagger/",
                self.admin_site.admin_view(self.tagger_view),
                name="archive_document_tagger",
            ),
            path(
                "scan-upload/",
                self.admin_site.admin_view(require_POST(self.scan_upload_view)),
                name="archive_document_scan_upload",
            ),
            *super().get_urls(),
        ]

    def tagger_view(self, request: HttpRequest, object_id: int) -> HttpResponse:
        document = get_object_or_404(
            Document.objects.select_related(*Document.owner_accessors()),
            pk=object_id,
        )
        if not document.offers_tagger():
            raise Http404
        fragments = list(tagger_fragments(document))
        context = {
            **self.admin_site.each_context(request),
            "title": _("Tag fragments"),
            "document": document,
            "owner": document.owner,
            "fragments": fragments,
            "pages": tagger_pages(document, fragments),
            "tags": Tag.objects.order_by("title"),
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/archive/document/tagger.html", context)

    def scan_upload_view(self, request: HttpRequest) -> HttpResponse:
        """Sign the upload of the scan named `filename` from the browser straight to S3
        (`archive.uploads.presigned_scan_upload()`, ARC-64)."""
        if not direct_upload_enabled():
            raise Http404
        if not self.has_add_permission(request):
            raise PermissionDenied
        filename = request.POST.get("filename", "")
        try:
            PDF_EXTENSION(File(None, filename))
        except ValidationError as error:
            return JsonResponse({"error": " ".join(error.messages)}, status=400)
        return JsonResponse(presigned_scan_upload(filename))

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        """Hide documents from the admin menu: an item's form uploads its text (US-WR-04).

        The admin stays registered for the `document` lookup of the forms steps 7 to 9 replace.
        """
        return {}

    def get_readonly_fields(
        self, request: HttpRequest, obj: Document | None = None
    ) -> tuple[str, ...]:
        """An OCR text changes only with a new scan, whose text layer also sets its pages."""
        if obj is not None and obj.kind == Document.Kind.OCR:
            return ("text",)
        return ()


@admin.register(Fragment)
class FragmentAdmin(SearchIndexedAdmin[Fragment]):
    list_display = (
        "__str__",
        "document",
        "works",
        "shelfmark",
        "is_featured",
        "needs_review",
    )
    list_filter = ("needs_review", "is_featured")
    list_select_related = (
        *(f"document__{owner}__institution" for owner in Document.owner_accessors()),
        "document__typescript__work",
    )
    search_fields = ("quote",)
    ordering = ("-needs_review", "document", "start")
    readonly_fields = ("document", "works", "shelfmark", "quote")
    autocomplete_fields = ("tags",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Fragment]:
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "document__note__works",
                "document__secondarytext__works",
                "document__contextualmaterial__works",
            )
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Fragments are created by selecting text in the tagger."""
        return False

    @admin.display(description=_("shelfmark"))
    def shelfmark(self, obj: Fragment) -> str:
        """From the document's owner and the scan page the fragment starts on (ARC-11)."""
        return obj.shelfmark_display

    @admin.display(description=_("works"))
    def works(self, obj: Fragment) -> str | None:
        """The works of the fragment's typescript, note, secondary text or contextual material."""
        owner = obj.document.owner
        if isinstance(owner, Typescript):
            return str(owner.work)
        if isinstance(owner, Note | SecondaryText | ContextualMaterial):
            return ", ".join(sorted(str(work) for work in owner.works.all())) or None
        return None


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
