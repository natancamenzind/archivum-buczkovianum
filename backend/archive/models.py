"""Domain model of the archive (docs/architecture.md, section 4).

Editors work only in Django admin, so every rule that keeps the data consistent lives here:
in field definitions, database constraints, `clean()` and `save()`. There are no signals.
"""

from bisect import bisect_right
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Self, cast

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Exists, Expression, F, Func, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.fields.files import FieldFile
from django.db.models.functions import Collate
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django_prose_editor.fields import ProseEditorField, create_sanitizer
from django_stubs_ext import StrOrPromise

from archive.images import to_webp, validate_image
from search.models import EntityType, IndexedContent, SearchEntry, Weight, html_to_text

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser, User

IMAGE_EXTENSIONS = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
PDF_EXTENSION = FileExtensionValidator(["pdf"])
# Polish alphabetical order: "Ł" after "L", "Ż" last, case ignored. ICU ships with PostgreSQL.
POLISH_COLLATION = "pl-x-icu"

# The rich text editor's toolbar (architecture section 5). The same list is the allowlist that
# sanitizes the HTML on the server. Headings start at h3: the page title and section titles above
# a description are h1 and h2.
RICH_TEXT_EXTENSIONS: dict[str, Any] = {
    "Bold": True,
    "Italic": True,
    "Link": {"enableTarget": False},
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,
    "Heading": {"levels": [3, 4]},
}


def blank_if_empty(html: str) -> str:
    """An emptied editor still holds empty paragraphs. Store nothing instead (R-02)."""
    return html if html_to_text(html) else ""


def rich_text_field(**kwargs: Any) -> "models.TextField[str, str]":
    """A rich text field (architecture section 5): HTML, sanitized by `BaseModel.save()`."""
    field = ProseEditorField(
        extensions=RICH_TEXT_EXTENSIONS,
        # Applied last to first.
        sanitize=[blank_if_empty, create_sanitizer],
        blank=True,
        **kwargs,
    )
    return cast("models.TextField[str, str]", field)


def fragment_shelfmark(unit: str, page: int | None) -> str:
    """The number part of a fragment's shelfmark, e.g. "1618.19" (ARC-11): its owner's, a dot and
    the scan page; no page for a plain text, and nothing without the owner's."""
    return f"{unit}.{page}" if unit and page else unit


def fragment_url(owner_url: str, fragment_id: int) -> str:
    """The page of a fragment's source, scrolled to the fragment (R-11)."""
    return f"{owner_url}?fragment={fragment_id}"


def format_shelfmark(institution: "Institution | None", number: str) -> str:
    """Display form of a shelfmark, e.g. "ML, sygn. 1618" (US-WR-14 AC2)."""
    if not number:
        return ""
    if institution is None:
        return f"sygn. {number}"
    return f"{institution.abbreviation}, sygn. {number}"


# --- Shared behaviour -------------------------------------------------------------------


class BaseModel(models.Model):
    """Base of every model: timestamps, a text alternative for every image (R-12), and images
    stored as WebP (ARC-29).

    Any file field `X` with a companion `X_alt` field must have `X_alt` filled when `X` is set.
    An image field is a file field validated by `IMAGE_EXTENSIONS`.
    """

    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Sanitize rich text on every save, not only in forms: the site renders it as HTML.
        Convert new images to WebP."""
        for field in self._meta.concrete_fields:
            if isinstance(field, ProseEditorField):
                setattr(self, field.attname, field.sanitize(getattr(self, field.attname)))
        for upload in self.new_images().values():
            upload.file = to_webp(upload.file)
            upload.name = upload.file.name
        super().save(*args, **kwargs)

    def new_images(self) -> "dict[str, FieldFile]":
        """The image fields given a file that is not stored yet, by field name."""
        return {
            field.name: upload
            for field in self._meta.concrete_fields
            if isinstance(field, models.FileField)
            and IMAGE_EXTENSIONS in field.validators
            and (upload := getattr(self, field.attname))
            and not upload._committed
        }

    def clean(self) -> None:
        super().clean()
        errors: dict[str, ValidationError | StrOrPromise] = {}
        for name, upload in self.new_images().items():
            try:
                validate_image(upload.file)
            except ValidationError as error:
                errors[name] = error
        for field in self._meta.get_fields():
            alt_name = f"{field.name}_alt"
            if (
                isinstance(field, models.FileField)
                and hasattr(self, alt_name)
                and getattr(self, field.name)
                and not getattr(self, alt_name).strip()
            ):
                errors[alt_name] = _("Describe the image for readers who cannot see it.")
        if errors:
            raise ValidationError(errors)


class Status(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")


def count_of(queryset: "models.QuerySet[Any]") -> Subquery:
    """The number of rows in `queryset`, as a subquery that may refer to the outer query."""
    rows = queryset.order_by().annotate(rows=Func(F("pk"), function="COUNT")).values("rows")
    return Subquery(rows, output_field=models.IntegerField())


@dataclass(frozen=True)
class Preview[M: models.Model]:
    """The first items of a section, with the count of all of them: "2 z 24" (R-09)."""

    items: list[M]
    total: int


def preview[M: models.Model](
    queryset: "models.QuerySet[M]", limit: int | None = None
) -> Preview[M]:
    """The first `limit` items of an ordered queryset, `PREVIEW_LIMIT` by default (architecture
    section 4.5)."""
    limit = settings.PREVIEW_LIMIT if limit is None else limit
    return Preview(items=list(queryset[:limit]), total=queryset.count())


def published_q(prefix: str = "") -> Q:
    """What the public may see (R-06): `prefix` leads to a published entity.

    Drafts are never listed, even for editors.
    """
    return Q(**{f"{prefix}status": Status.PUBLISHED})


class PublishableQuerySet[M: "Publishable"](models.QuerySet[M]):
    def published(self) -> Self:
        return self.filter(published_q())

    def viewable_by(self, user: "User | AnonymousUser") -> Self:
        """What an entity page may show (R-06): published entities, and drafts for staff, who
        preview them (US-WR-13). Lists, previews and related items never take drafts."""
        return self if user.is_staff else self.published()


class Publishable(BaseModel):
    """A public entity with its own page. Only published entities are public (R-06)."""

    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_("Only published items are visible to the public."),
    )
    title = models.CharField(_("title"), max_length=255)
    header_image = models.FileField(
        _("header image"),
        upload_to="headers/",
        blank=True,
        validators=[IMAGE_EXTENSIONS],
        help_text=_("Optional. Shown behind the title at the top of the page."),
    )
    header_image_alt = models.CharField(
        _("header image text alternative"), max_length=255, blank=True
    )

    search_type: ClassVar[EntityType]
    # Defined by every concrete model.
    get_absolute_url: Callable[[], str]
    indexed_content: Callable[[], IndexedContent]

    class Meta:
        abstract = True
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.update_search_entry()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        with transaction.atomic():
            SearchEntry.remove(self.search_type, self.pk)
            result = super().delete(*args, **kwargs)
            Tag.update_search_entries()
        return result

    @property
    def is_draft(self) -> bool:
        return self.status == Status.DRAFT

    def is_viewable_by(self, user: "User | AnonymousUser") -> bool:
        """Whether `user` may see this entity's page (`PublishableQuerySet.viewable_by()`)."""
        return not self.is_draft or user.is_staff

    @property
    def description_text(self) -> str:
        """The description without its HTML, for the search index and the page's meta
        description. Empty for an entity without a description."""
        return ""

    def update_search_entry(self) -> None:
        """Index a published entity, unindex a draft (architecture section 6).

        The fragments of an item's text follow it, since their visibility does.
        """
        content = self.indexed_content() if self.status == Status.PUBLISHED else None
        if content is None:
            SearchEntry.remove(self.search_type, self.pk)
        else:
            SearchEntry.write(self.search_type, self.pk, content)
        if isinstance(self, Archival):
            self.update_fragment_entries(content)


class Described(Publishable):
    """A public entity with a description: every one but the note (ARC-35)."""

    description = rich_text_field(verbose_name=_("description"))

    class Meta(Publishable.Meta):
        abstract = True

    @property
    def description_text(self) -> str:
        return html_to_text(self.description)


class Taggable(models.Model):
    """Tags on the whole item (US-WR-10)."""

    tags: "models.ManyToManyField[Tag, Any]" = models.ManyToManyField(
        "Tag", verbose_name=_("tags"), blank=True, related_name="%(class)ss"
    )

    class Meta:
        abstract = True

    def published_tags(self) -> "TagQuerySet":
        """The tags shown with this item. Draft tags never are (R-06)."""
        return Tag.objects.published().filter(pk__in=self.tags.values("pk"))

    def published_tag_names(self) -> list[str]:
        """What the search entry holds of the tags this carries (D18)."""
        return list(self.published_tags().values_list("title", flat=True))


class Archival(models.Model):
    """An item held by an institution under a shelfmark, optionally with a text (`Document`)."""

    document_required = False
    # The field linking this kind of item to its works, and its reverse name from `Work`.
    work_field: ClassVar[str] = "works"
    works_lookup: ClassVar[str]
    _indexed_document_id: int | None = None

    institution = models.ForeignKey(
        "Institution",
        verbose_name=_("institution"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)ss",
    )
    shelfmark = models.CharField(
        _("shelfmark"),
        max_length=50,
        blank=True,
        help_text=_("Number only, e.g. 1618. The institution is chosen separately."),
    )
    document = models.OneToOneField(
        "Document",
        verbose_name=_("text"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s",
        help_text=_("The scan and OCR text, or the plain text, of this item."),
    )

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Delete the text the item no longer holds, which has no meaning on its own."""
        dropped = self.dropped_document_id
        if dropped is not None:
            self.refuse_dropping_text(dropped)
        with transaction.atomic():
            super().save(*args, **kwargs)
            if dropped is not None:
                for document in Document.objects.filter(pk=dropped):
                    document.delete()

    def clean(self) -> None:
        super().clean()
        dropped = self.dropped_document_id
        if dropped is not None:
            self.refuse_dropping_text(dropped)
        if self.document is None:
            if self.document_required:
                raise ValidationError({"document": _("This item needs a text.")})
            return
        if self.document.owner not in (None, self):
            raise ValidationError({"document": _("This text already belongs to another item.")})
        kind = self.required_document_kind()
        if kind and self.document.kind != kind:
            raise ValidationError(
                {"document": _("Choose a text of kind “%s”.") % Document.Kind(kind).label}
            )

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Delete the item together with its document, which has no meaning on its own."""
        document = self.document
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            if document is not None:
                document.delete()
        return result

    @property
    def dropped_document_id(self) -> int | None:
        """The stored text the item no longer holds, if it was given another one or none."""
        dropped = self._indexed_document_id
        return dropped if dropped not in (None, self.document_id) else None

    def refuse_dropping_text(self, document_id: int) -> None:
        """Refuse to drop a text that still has tagged fragments (US-WR-09 AC4)."""
        count = Fragment.objects.filter(document_id=document_id).count()
        if count:
            raise ValidationError(
                {
                    "document": ngettext(
                        "The text this item holds has %(count)d tagged fragment. "
                        "Delete them before removing the text.",
                        "The text this item holds has %(count)d tagged fragments. "
                        "Delete them before removing the text.",
                        count,
                    )
                    % {"count": count}
                }
            )

    @property
    def shelfmark_display(self) -> str:
        return format_shelfmark(self.institution, self.shelfmark)

    def required_document_kind(self) -> str | None:
        """The kind of `Document` this item's text must be, or None for any kind."""
        return None

    def related_works(self) -> "WorkQuerySet":
        """The published works this item relates to, by first edition (R-03)."""
        return Work.objects.published().filter(**{self.works_lookup: self}).with_year()

    def carried_tags(self, *, with_work_links: bool = False) -> "TagQuerySet":
        """The published tags on this item and on the fragments of its text, by name (R-06);
        with `with_work_links`, also those on its links to published works."""
        assert isinstance(self, Taggable)
        fragments = (
            Fragment.objects.filter(document_id=self.document_id)
            if self.document_id
            else Fragment.objects.none()
        )
        carried = Q(pk__in=self.tags.values("pk")) | Q(pk__in=fragments.values("tags"))
        if with_work_links and isinstance(self, SecondaryText | ContextualMaterial):
            links = self.work_links.filter(published_q("work__"))
            carried |= Q(pk__in=links.values("tags"))
        return Tag.objects.published().filter(carried).order_by("title")

    def indexed_content(self) -> IndexedContent:
        """Title, description and the whole text of a typescript, note, secondary text or
        contextual material."""
        assert isinstance(self, Publishable) and isinstance(self, Taggable)
        text = self.document.text if self.document else ""
        work_ids, decades = search_filters(self.related_works())
        return IndexedContent(
            title=self.title,
            url=self.get_absolute_url(),
            texts=[
                (self.title, Weight.TITLE),
                (self.description_text, Weight.DESCRIPTION),
                (text, Weight.TEXT),
            ],
            tags=self.published_tag_names(),
            work_ids=work_ids,
            decades=decades,
            has_scan=bool(self.document and self.document.scan),
            has_text=bool(text),
        )

    def update_fragment_entries(self, owner: IndexedContent | None) -> None:
        """Index the fragments of this item's text while the item is published (D4).

        `owner` is the item's own entry, or None for a draft. The fragments of a text the item
        no longer has leave the index: that text has no owner now.
        """
        if self.dropped_document_id is not None:
            SearchEntry.remove_fragments(
                Fragment.objects.filter(document_id=self.dropped_document_id)
            )
        self._indexed_document_id = self.document_id
        if self.document is None:
            return
        fragments = self.document.fragments.all()
        if owner is None:
            SearchEntry.remove_fragments(fragments)
            return
        # One query for every fragment's tags, not one per fragment.
        for fragment in fragments.prefetch_related(Prefetch("tags", Tag.objects.published())):
            fragment.write_search_entry(owner, [tag.title for tag in fragment.tags.all()])

    @classmethod
    def from_db(
        cls, db: str | None, field_names: Collection[str], values: Collection[Any], **kwargs: Any
    ) -> Self:
        """Remember the stored text, to unindex its fragments if the item gets another one."""
        item = super().from_db(db, field_names, values, **kwargs)
        item._indexed_document_id = item.__dict__.get("document_id")
        return item


class ContentKind(models.TextChoices):
    IMAGE = "image", _("Image")
    DOCUMENT = "document", _("Document file")
    EXTERNAL_MEDIA = "external_media", _("External audio or video link")
    OCR_TEXT = "ocr_text", _("OCR text (searchable PDF scan)")
    PLAIN_TEXT = "plain_text", _("Plain text")


# The field that holds each kind of content.
CONTENT_FIELDS: dict[str, str] = {
    ContentKind.IMAGE: "image",
    ContentKind.DOCUMENT: "file",
    ContentKind.EXTERNAL_MEDIA: "external_url",
    ContentKind.OCR_TEXT: "document",
    ContentKind.PLAIN_TEXT: "document",
}


class MediaContent(Archival):
    """Content of a note or contextual material: exactly one kind (US-WR-05 AC2, US-WR-07 AC2)."""

    content_kind = models.CharField(_("content kind"), max_length=20, choices=ContentKind.choices)
    image = models.FileField(
        _("image"), upload_to="content/", blank=True, validators=[IMAGE_EXTENSIONS]
    )
    image_alt = models.CharField(_("image text alternative"), max_length=255, blank=True)
    file = models.FileField(_("document file"), upload_to="content/", blank=True)
    external_url = models.URLField(_("external audio or video link"), blank=True)

    class Meta:
        abstract = True

    def required_document_kind(self) -> str | None:
        return TEXT_CONTENT_KINDS.get(self.content_kind)

    def clean(self) -> None:
        super().clean()
        chosen = CONTENT_FIELDS.get(self.content_kind)
        if chosen is None:
            return
        errors = {}
        for field in set(CONTENT_FIELDS.values()):
            filled = bool(getattr(self, field))
            if field == chosen and not filled:
                errors[field] = _("Required for this kind of content.")
            if field != chosen and filled:
                errors[field] = _("Leave this empty for this kind of content.")
        if errors:
            raise ValidationError(errors)


# --- Entities ---------------------------------------------------------------------------


class Institution(BaseModel):
    abbreviation = models.CharField(
        _("abbreviation"), max_length=20, unique=True, help_text=_("E.g. ML.")
    )
    name = models.CharField(_("full name"), max_length=255, help_text=_("E.g. Muzeum Literatury."))

    class Meta:
        ordering = ("abbreviation",)
        verbose_name = _("institution")
        verbose_name_plural = _("institutions")

    def __str__(self) -> str:
        return self.abbreviation


class TagQuerySet(PublishableQuerySet["Tag"]):
    def with_occurrences(self) -> Self:
        """Annotate `occurrences`: the visible fragments, published items and visible work links
        carrying the tag (glossary, "Occurrence").

        It ignores the tag's own status: public callers chain `published()` first.
        """
        carriers: list[models.QuerySet[Any]] = [
            Fragment.objects.visible(),
            Work.objects.published(),
            *(item.objects.published() for item in ITEM_MODELS),
            *(link.objects.visible() for link in LINK_MODELS),
        ]
        occurrences: Expression = Value(0)
        for carrier in carriers:
            occurrences += count_of(carrier.filter(tags=OuterRef("pk")))
        return self.annotate(occurrences=occurrences)

    def in_use(self) -> Self:
        """Tags with at least one occurrence, the most frequent first (US-RA-15 AC8)."""
        return (
            self.with_occurrences()
            .filter(occurrences__gt=0)
            .order_by(F("occurrences").desc(), "title")
        )

    def referring_to(self, work: "Work") -> Self:
        """The tags that refer to `work` (US-RA-04 AC4), the inverse of
        `WorkQuerySet.referred_to_by()`: on the work, on a published item related to it, on a
        visible fragment of such an item, or on a visible work link."""
        referring = Q(works=work)
        for item in ITEM_MODELS:
            related: PublishableQuerySet[Any] = item.objects.published().filter(
                **{item.work_field: work}
            )
            fragments = Fragment.objects.filter(document__in=related.values("document"))
            referring |= Q(pk__in=related.values("tags")) | Q(pk__in=fragments.values("tags"))
        for link in LINK_MODELS:
            referring |= Q(pk__in=link.objects.visible().filter(work=work).values("tags"))
        return self.filter(referring)


class Tag(Described):
    class Kind(models.TextChoices):
        KEYWORD = "keyword", _("Buczkowski's keyword")
        INTERPRETATION = "interpretation", _("Interpretation")

    title = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.SlugField(
        _("slug"), max_length=255, unique=True, help_text=_("Part of the page address.")
    )
    kind = models.CharField(
        _("kind"),
        max_length=20,
        choices=Kind.choices,
        help_text=_("Only for filtering in the editor panel. Never public."),
    )
    related = models.ManyToManyField(
        "self", verbose_name=_("related tags"), blank=True, help_text=_("Works both ways.")
    )

    objects = TagQuerySet.as_manager()
    # Set only by `TagQuerySet.with_occurrences()`.
    occurrences: int

    search_type = EntityType.TAG

    class Meta(Publishable.Meta):
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Index again what carries the tag: its entry holds the tag's name while it is
        published (D18)."""
        with transaction.atomic():
            super().save(*args, **kwargs)
            for model in (Work, *ITEM_MODELS, Fragment):
                for carrier in model.objects.filter(tags=self):
                    carrier.update_search_entry()

    def get_absolute_url(self) -> str:
        return f"/tagi/{self.slug}"

    def indexed_content(self) -> IndexedContent:
        work_ids, decades = search_filters(Work.objects.referred_to_by(self))
        return IndexedContent(
            title=self.title,
            url=self.get_absolute_url(),
            texts=[(self.title, Weight.TITLE), (self.description_text, Weight.QUOTE)],
            work_ids=work_ids,
            decades=decades,
        )

    @classmethod
    def update_search_entries(cls) -> None:
        """Index every published tag again. A tag's entry lists the works it refers to through
        whatever carries it, so a change to any tagged item, link or work can change it."""
        for tag in cls.objects.published():
            tag.update_search_entry()

    def usages(self, limit: int = 20) -> list[models.Model]:
        """Up to `limit` items carrying this tag. A tag in use cannot be deleted (US-WR-08 AC3)."""
        items: list[models.Model] = []
        for relation in self._meta.related_objects:
            if len(items) >= limit:
                break
            if relation.many_to_many and relation.field.name == "tags":
                manager = getattr(self, relation.get_accessor_name() or "")
                items += manager.all()[: limit - len(items)]
        return items

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        usages = self.usages()
        if usages:
            raise models.ProtectedError(
                _("The tag is in use: %s") % ", ".join(str(item) for item in usages),
                set(usages),
            )
        return super().delete(*args, **kwargs)


def search_filters(works: "WorkQuerySet") -> tuple[list[int], list[int]]:
    """The published works among `works`, and the decades of their first editions (e.g. 1940),
    as the search filters store them (US-RA-16 AC2)."""
    years = {work.pk: work.year for work in works.published().with_year()}
    return list(years), sorted({year // 10 * 10 for year in years.values() if year is not None})


def first_edition_year(work: str = "pk") -> Subquery:
    """The year of a work: its earliest edition (architecture section 4.2).

    `work` names the field of the outer query that holds the work's id.
    """
    years = Edition.objects.filter(work=OuterRef(work)).order_by("year").values("year")
    return Subquery(years[:1])


class WorkQuerySet(PublishableQuerySet["Work"]):
    def with_year(self) -> Self:
        """Annotate the year of the first edition and order by it, as everywhere on the site."""
        return self.annotate(year=first_edition_year()).order_by(
            F("year").asc(nulls_last=True), "title"
        )

    def with_fragment_count(self, tag: "Tag | None" = None) -> Self:
        """Annotate `fragment_count`: the visible fragments of the work's main typescript (D19),
        only those carrying `tag` if one is given (US-RA-07 AC2).

        A work without a main typescript, or with a draft one, counts 0.
        """
        fragments = Fragment.objects.visible().filter(
            document__typescript__work=OuterRef("pk"), document__typescript__is_main=True
        )
        if tag is not None:
            fragments = fragments.filter(tags=tag)
        return self.annotate(fragment_count=count_of(fragments))

    def with_bibliography(self) -> Self:
        """The works with at least one bibliography entry (US-RA-21 AC4)."""
        return self.filter(Exists(BibliographyEntry.objects.filter(work=OuterRef("pk"))))

    def referred_to_by(self, tag: "Tag") -> Self:
        """The works a tag refers to (US-RA-07 AC5): the tag is on the work, on a published item
        related to it, on a visible fragment of such an item, or on a visible work link."""
        carrying = Q(tags=tag) | Q(document__fragments__tags=tag)
        referred = Q(tags=tag)
        for item in ITEM_MODELS:
            items = item.objects.published().filter(carrying)
            referred |= Q(pk__in=items.values(item.work_field))
        for link in LINK_MODELS:
            referred |= Q(pk__in=link.objects.visible().filter(tags=tag).values("work"))
        return self.filter(referred)


class Work(Described, Taggable):
    slug = models.SlugField(
        _("slug"), max_length=255, unique=True, help_text=_("Part of the page address.")
    )
    cover_image = models.FileField(
        _("cover image"), upload_to="works/", blank=True, validators=[IMAGE_EXTENSIONS]
    )
    cover_image_alt = models.CharField(
        _("cover image text alternative"), max_length=255, blank=True
    )

    objects = WorkQuerySet.as_manager()
    # Set only by `WorkQuerySet.with_year()`.
    year: int | None
    # Set only by `WorkQuerySet.with_fragment_count()`.
    fragment_count: int

    search_type = EntityType.WORK

    class Meta(Publishable.Meta):
        verbose_name = _("work")
        verbose_name_plural = _("works")

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.update_related_search_entries(self.related_items())

    def get_absolute_url(self) -> str:
        return f"/utwory/{self.slug}"

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        items = self.related_items()
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            self.update_related_search_entries(items)
        return result

    def bibliography_preview(self) -> "Preview[BibliographyEntry]":
        """The first entries of the bibliography and their count: "5 z 12" (US-RA-21 AC1)."""
        return preview(self.bibliography.all(), settings.BIBLIOGRAPHY_PREVIEW_LIMIT)

    def related_items(self) -> list[Publishable]:
        return [item for model in ITEM_MODELS for item in getattr(self, model.works_lookup).all()]

    def update_search_entries(self) -> None:
        """Index the work and what relates to it again, e.g. after its year changed."""
        self.update_search_entry()
        self.update_related_search_entries(self.related_items())

    def update_related_search_entries(self, items: list[Publishable]) -> None:
        """Index again what relates to this work. The search filters hold its id while it is
        published, and the decade of its first edition."""
        for item in items:
            item.update_search_entry()
        Tag.update_search_entries()

    def indexed_content(self) -> IndexedContent:
        return IndexedContent(
            title=self.title,
            url=self.get_absolute_url(),
            texts=[(self.title, Weight.TITLE), (self.description_text, Weight.DESCRIPTION)],
            tags=self.published_tag_names(),
            work_ids=[self.pk],
            decades=search_filters(Work.objects.filter(pk=self.pk))[1],
        )


class Edition(BaseModel):
    work = models.ForeignKey(
        Work, verbose_name=_("work"), on_delete=models.CASCADE, related_name="editions"
    )
    publisher = models.CharField(_("publisher"), max_length=255)
    place = models.CharField(_("place"), max_length=255)
    year = models.PositiveSmallIntegerField(_("year"))

    class Meta:
        ordering = ("year",)
        verbose_name = _("edition")
        verbose_name_plural = _("editions")

    def __str__(self) -> str:
        return f"{self.publisher}, {self.place} {self.year}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """The work's year may change, and with it the decades in the search index."""
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.work.update_search_entries()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            self.work.update_search_entries()
        return result


class BibliographyEntry(BaseModel):
    """One line of a work's bibliography (US-WR-15)."""

    work = models.ForeignKey(
        Work, verbose_name=_("work"), on_delete=models.CASCADE, related_name="bibliography"
    )
    text = models.CharField(
        _("entry"),
        max_length=1000,
        help_text=_("One line, e.g. Author, Title, Publisher, place year, p. pages."),
    )

    class Meta:
        # Alphabetical, i.e. by the author's surname each entry starts with (US-WR-15 AC2).
        ordering = (Collate("text", POLISH_COLLATION), "pk")
        verbose_name = _("bibliography entry")
        verbose_name_plural = _("bibliography")

    def __str__(self) -> str:
        return self.text

    def save(self, *args: Any, **kwargs: Any) -> None:
        """An entry is one line (US-WR-15 AC1): line breaks become spaces."""
        self.text = " ".join(self.text.split())
        super().save(*args, **kwargs)


class Typescript(Described, Taggable, Archival):
    document_required = True
    work_field = "work"
    works_lookup = "typescripts"
    search_type = EntityType.TYPESCRIPT

    work = models.ForeignKey(
        Work, verbose_name=_("work"), on_delete=models.PROTECT, related_name="typescripts"
    )
    is_main = models.BooleanField(
        _("main typescript"),
        default=False,
        help_text=_("One per work. Marking this one unmarks the previous one."),
    )

    objects = PublishableQuerySet["Typescript"].as_manager()

    class Meta:
        ordering = ("shelfmark", "title")
        verbose_name = _("typescript")
        verbose_name_plural = _("typescripts")
        constraints = (
            models.UniqueConstraint(
                fields=["work"], condition=Q(is_main=True), name="one_main_typescript_per_work"
            ),
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            if self.is_main:
                previous = Typescript.objects.filter(work_id=self.work_id, is_main=True)
                for other in previous.exclude(pk=self.pk):
                    other.is_main = False
                    other.save(update_fields=["is_main", "updated_at"])
            super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return f"/maszynopisy/{self.pk}"

    def validate_constraints(self, exclude: Collection[str] | None = None) -> None:
        """Skip "one main typescript per work" here: `save()` unmarks the previous one first."""
        super().validate_constraints(exclude={*(exclude or ()), "is_main"})

    def required_document_kind(self) -> str | None:
        return Document.Kind.OCR


class Note(Publishable, Taggable, MediaContent):
    works_lookup = "notes"
    search_type = EntityType.NOTE

    works = models.ManyToManyField(Work, verbose_name=_("works"), related_name="notes")

    objects = PublishableQuerySet["Note"].as_manager()

    class Meta(Publishable.Meta):
        verbose_name = _("note")
        verbose_name_plural = _("notes")

    def get_absolute_url(self) -> str:
        return f"/zapiski/{self.pk}"


class SecondaryText(Described, Taggable, Archival):
    class Kind(models.TextChoices):
        LETTER = "letter", _("Letter")
        REVIEW = "review", _("Review")
        STUDY = "study", _("Study")
        RECORDING = "recording", _("Recording")
        OTHER = "other", _("Other")

    document_required = True
    works_lookup = "secondary_texts"
    search_type = EntityType.SECONDARY_TEXT

    kind = models.CharField(_("kind"), max_length=20, choices=Kind.choices)
    author = models.CharField(_("author"), max_length=255, blank=True)
    source = models.CharField(
        _("source"),
        max_length=500,
        blank=True,
        help_text=_("Publisher, place, year, pages, as one line."),
    )
    letter_date = models.DateField(_("date"), null=True, blank=True, help_text=_("For letters."))
    sender = models.CharField(_("sender"), max_length=255, blank=True, help_text=_("For letters."))
    recipient = models.CharField(
        _("recipient"), max_length=255, blank=True, help_text=_("For letters.")
    )
    external_url = models.URLField(
        _("external audio or video link"),
        blank=True,
        help_text=_("A recording of the text, e.g. on archive.org."),
    )
    works = models.ManyToManyField(
        Work,
        verbose_name=_("works"),
        through="SecondaryTextWorkLink",
        related_name="secondary_texts",
    )

    objects = PublishableQuerySet["SecondaryText"].as_manager()

    class Meta(Publishable.Meta):
        verbose_name = _("secondary text")
        verbose_name_plural = _("secondary texts")

    def get_absolute_url(self) -> str:
        return f"/teksty-sekundarne/{self.pk}"


class ContextualMaterial(Described, Taggable, MediaContent):
    works_lookup = "materials"
    search_type = EntityType.MATERIAL

    works = models.ManyToManyField(
        Work, verbose_name=_("works"), through="MaterialWorkLink", related_name="materials"
    )

    objects = PublishableQuerySet["ContextualMaterial"].as_manager()

    class Meta(Publishable.Meta):
        verbose_name = _("contextual material")
        verbose_name_plural = _("contextual materials")

    def get_absolute_url(self) -> str:
        return f"/materialy/{self.pk}"


# Every kind of archival item, in the order the tag page lists their fragments within a work.
ITEM_MODELS = (Typescript, Note, SecondaryText, ContextualMaterial)


class WorkLinkQuerySet[L: "SecondaryTextWorkLink | MaterialWorkLink"](models.QuerySet[L]):
    def visible(self) -> Self:
        """Links whose work and linked item are both published."""
        return self.filter(published_q("work__"), published_q(f"{self.model.item_field}__"))


class SecondaryTextWorkLink(BaseModel, Taggable):
    """A secondary text's link to a work. Its tags appear on the work page (US-RA-05)."""

    secondary_text = models.ForeignKey(
        SecondaryText,
        verbose_name=_("secondary text"),
        on_delete=models.CASCADE,
        related_name="work_links",
    )
    work = models.ForeignKey(
        Work, verbose_name=_("work"), on_delete=models.CASCADE, related_name="secondary_text_links"
    )

    item_field = "secondary_text"
    objects = WorkLinkQuerySet["SecondaryTextWorkLink"].as_manager()

    class Meta:
        verbose_name = _("link to a work")
        verbose_name_plural = _("links to works")
        constraints = (
            models.UniqueConstraint(
                fields=["secondary_text", "work"], name="unique_secondary_text_work"
            ),
        )

    def __str__(self) -> str:
        return f"{self.secondary_text} ↔ {self.work}"


class MaterialWorkLink(BaseModel, Taggable):
    """A contextual material's link to a work. Its tags appear on the work page (US-RA-05)."""

    material = models.ForeignKey(
        ContextualMaterial,
        verbose_name=_("contextual material"),
        on_delete=models.CASCADE,
        related_name="work_links",
    )
    work = models.ForeignKey(
        Work, verbose_name=_("work"), on_delete=models.CASCADE, related_name="material_links"
    )

    item_field = "material"
    objects = WorkLinkQuerySet["MaterialWorkLink"].as_manager()

    class Meta:
        verbose_name = _("link to a work")
        verbose_name_plural = _("links to works")
        constraints = (
            models.UniqueConstraint(fields=["material", "work"], name="unique_material_work"),
        )

    def __str__(self) -> str:
        return f"{self.material} ↔ {self.work}"


# The links of items to works, which carry their own tags (US-RA-05).
LINK_MODELS = (SecondaryTextWorkLink, MaterialWorkLink)


# --- Texts and fragments (architecture section 4.4) -------------------------------------


class Document(BaseModel):
    """The text of an archival item: a scan with its OCR text, or a plain text."""

    class Kind(models.TextChoices):
        OCR = "ocr", _("Scan + OCR text")
        PLAIN = "plain", _("Plain text")

    kind = models.CharField(_("kind"), max_length=10, choices=Kind.choices)
    scan = models.FileField(
        _("scan"),
        upload_to="scans/",
        blank=True,
        validators=[PDF_EXTENSION],
        help_text=_("PDF file."),
    )
    text = models.TextField(_("text"), blank=True)
    page_offsets = ArrayField(models.PositiveIntegerField(), default=list, editable=False)

    _saved_text: str | None = None
    _saved_page_offsets: list[int] | None = None

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("document")
        verbose_name_plural = _("documents")

    def __str__(self) -> str:
        owner = self.owner
        return str(owner) if owner else f"{self.get_kind_display()} #{self.pk}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        text_changed = self._saved_text not in (None, self.text)
        with transaction.atomic():
            super().save(*args, **kwargs)
            if text_changed:
                for fragment in self.fragments.all():
                    fragment.reanchor(self.text)
            owner = self.owner
            # An owner not saved yet, as on the form that adds it, indexes itself when saved.
            if isinstance(owner, Publishable) and owner.pk is not None:
                owner.update_search_entry()
        self._saved_text = self.text
        self._saved_page_offsets = list(self.page_offsets)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Unindex the fragments first: the database deletes them without `Fragment.delete()`."""
        with transaction.atomic():
            SearchEntry.remove_fragments(self.fragments.all())
            return super().delete(*args, **kwargs)

    @classmethod
    def from_db(
        cls, db: str | None, field_names: Collection[str], values: Collection[Any], **kwargs: Any
    ) -> Self:
        """Remember the stored text, to tell later whether it changed."""
        document = super().from_db(db, field_names, values, **kwargs)
        document._saved_text = document.__dict__.get("text")
        document._saved_page_offsets = document.__dict__.get("page_offsets")
        return document

    @classmethod
    def owner_accessors(cls) -> list[str]:
        """Names of the reverse links from a document to every kind of `Archival` item."""
        return [
            relation.get_accessor_name() or ""
            for relation in cls._meta.related_objects
            if relation.one_to_one and issubclass(relation.related_model, Archival)
        ]

    @property
    def owner(self) -> Archival | None:
        """The typescript, note, secondary text or contextual material holding this text."""
        for accessor in self.owner_accessors():
            try:
                owner: Archival = getattr(self, accessor)
            except ObjectDoesNotExist:
                continue
            return owner
        return None

    def offers_tagger(self) -> bool:
        """Whether US-WR-09 AC1 allows tagging this document's text."""
        owner = self.owner
        if owner is None:
            return False
        if isinstance(owner, Typescript):
            return owner.is_main
        return isinstance(owner, (Note, SecondaryText, ContextualMaterial))

    def set_ocr_pages(self, pages: Sequence[str]) -> None:
        """Load the text of each scan page, read from the scan's text layer (`archive.uploads`).

        A page without text still gets its offset, so there is one offset per scan page.
        """
        offsets, position = [], 0
        for page in pages:
            offsets.append(position)
            position += len(page)
        self.text = "".join(pages)
        self.page_offsets = offsets

    @property
    def page_count(self) -> int:
        return len(self.page_offsets)

    def page_number(self, offset: int) -> int | None:
        """1-based scan page on which the character at `offset` lies, or None without a scan."""
        if not self.page_offsets:
            return None
        return bisect_right(self.page_offsets, offset)

    def clean(self) -> None:
        super().clean()
        if self.kind == self.Kind.OCR and not self.scan:
            raise ValidationError({"scan": _("An OCR text needs its scan.")})
        if self.kind == self.Kind.PLAIN and self.scan:
            raise ValidationError({"scan": _("A plain text has no scan.")})
        if (
            self.kind == self.Kind.OCR
            and self._saved_text not in (None, self.text)
            and self._saved_page_offsets == self.page_offsets
        ):
            raise ValidationError(
                {"text": _("Upload a new scan to change an OCR text, so pages stay aligned.")}
            )


# The kind of `Document` each kind of text content of a `MediaContent` item holds.
TEXT_CONTENT_KINDS: dict[str, str] = {
    ContentKind.OCR_TEXT: Document.Kind.OCR,
    ContentKind.PLAIN_TEXT: Document.Kind.PLAIN,
}


class FragmentQuerySet(models.QuerySet["Fragment"]):
    def visible(self) -> Self:
        """Fragments whose document's owner is published, whichever kind it is (architecture
        section 4.4, D4)."""
        owner_published = Q()
        for owner in Document.owner_accessors():
            owner_published |= published_q(f"document__{owner}__")
        return self.filter(owner_published)

    def with_number(self) -> Self:
        """Annotate `number`: the 1-based position among all the fragments of its document,
        by `start` (architecture section 4.2), whatever else the query filters out."""
        earlier = Fragment.objects.filter(document=OuterRef("document")).filter(
            Q(start__lt=OuterRef("start"))
            | Q(start=OuterRef("start"), end__lt=OuterRef("end"))
            | Q(start=OuterRef("start"), end=OuterRef("end"), pk__lt=OuterRef("pk"))
        )
        return self.annotate(number=count_of(earlier) + 1)

    def for_cards(self) -> Self:
        """Load what a fragment card shows (R-10): its number, its source with the source's
        institution, and its published tags."""
        return (
            self.with_number()
            .select_related(
                *(f"document__{owner}__institution" for owner in Document.owner_accessors())
            )
            .prefetch_related(Prefetch("tags", Tag.objects.published()))
        )

    def preview(self) -> Preview["Fragment"]:
        """Featured fragments first, then text order (R-09).

        Fragments of different documents follow document IDs, not a domain order. A preview
        across documents passes its own order to `preview()` instead.
        """
        return preview(self.order_by("-is_featured", "document_id", "start", "end", "pk"))

    def sharing_tags_with(self, item: "Note | SecondaryText | ContextualMaterial") -> Self:
        """The related fragments of an item (US-RA-10 AC3): visible typescript fragments that
        share a published tag with `item` or with a fragment of its text. Featured first, then
        by the work's first edition and text order (R-09), ready for `preview()`.

        Callers pass a published item, or a draft only for staff previewing it (US-WR-13): a
        draft's tags must not reach the public (R-06)."""
        tags = item.carried_tags().order_by()
        return (
            self.filter(published_q("document__typescript__"))
            .filter(pk__in=Fragment.objects.filter(tags__in=tags).values("pk"))
            .annotate(year=first_edition_year("document__typescript__work"))
            .order_by(
                "-is_featured", F("year").asc(nulls_last=True), "document_id", "start", "end", "pk"
            )
        )


class Fragment(BaseModel, Taggable):
    """A tagged character range of a document's text. Fragments may overlap freely."""

    document = models.ForeignKey(
        Document, verbose_name=_("document"), on_delete=models.CASCADE, related_name="fragments"
    )
    start = models.PositiveIntegerField(_("start"), editable=False)
    end = models.PositiveIntegerField(_("end"), editable=False)
    quote = models.TextField(_("quote"), editable=False, help_text=_("The selected text."))
    is_featured = models.BooleanField(
        _("featured"),
        default=False,
        help_text=_("Shown first in previews and on the home page."),
    )
    needs_review = models.BooleanField(
        _("needs review"),
        default=False,
        help_text=_("The text changed. Check the fragment, then clear this box."),
    )

    objects = FragmentQuerySet.as_manager()
    # Set only by `FragmentQuerySet.with_number()`.
    number: int

    class Meta:
        ordering = ("document", "start", "end")
        verbose_name = _("fragment")
        verbose_name_plural = _("fragments")
        constraints = (
            models.CheckConstraint(condition=Q(end__gt=F("start")), name="fragment_not_empty"),
        )

    def __str__(self) -> str:
        return Truncator(self.quote).chars(60)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.quote:
            self.quote = self.document.text[self.start : self.end]
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.update_search_entry()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        with transaction.atomic():
            SearchEntry.remove(EntityType.FRAGMENT, self.pk)
            result = super().delete(*args, **kwargs)
            Tag.update_search_entries()
        return result

    def update_search_entry(self) -> None:
        """Index the fragment while it is visible: its document's owner is published."""
        owner = self.document.owner
        if isinstance(owner, Publishable) and owner.status == Status.PUBLISHED:
            self.write_search_entry(owner.indexed_content(), self.published_tag_names())
        else:
            SearchEntry.remove(EntityType.FRAGMENT, self.pk)

    def write_search_entry(self, owner: IndexedContent, tags: list[str]) -> None:
        """Index the fragment under its owner: a link into the owner's page, and its filters.

        `tags` are the names of the published tags it carries."""
        SearchEntry.write(
            EntityType.FRAGMENT,
            self.pk,
            IndexedContent(
                title=str(self),
                url=fragment_url(owner.url, self.pk),
                texts=[(self.quote, Weight.QUOTE)],
                tags=tags,
                work_ids=owner.work_ids,
                decades=owner.decades,
                has_scan=owner.has_scan,
                has_text=True,
            ),
        )

    @property
    def start_page(self) -> int | None:
        return self.document.page_number(self.start)

    @property
    def shelfmark(self) -> str:
        """The number part of the shelfmark, e.g. "1618.19"."""
        owner = self.document.owner
        return fragment_shelfmark(owner.shelfmark if owner else "", self.start_page)

    @property
    def shelfmark_display(self) -> str:
        owner = self.document.owner
        return format_shelfmark(owner.institution if owner else None, self.shelfmark)

    @property
    def scan_display(self) -> str:
        """The scan page the fragment starts on, e.g. "19"; "" for a plain text."""
        return str(self.start_page or "")

    def clean(self) -> None:
        super().clean()
        # Offsets are set once, by the tagger. Later only re-anchoring moves them.
        if self._state.adding and self.end > len(self.document.text):
            raise ValidationError(_("The fragment goes past the end of the text."))

    def reanchor(self, text: str) -> None:
        """Follow the quote after the document text changed (US-WR-09 AC4).

        A fragment whose quote is still in place is left alone. Otherwise it is flagged for
        review, and also moved when its quote occurs exactly once in the new text, so it is
        never moved silently (docs/plan.md, D1). It is never deleted, and only the editor
        clears the flag.
        """
        if text[self.start : self.end] == self.quote:
            return
        before = (self.start, self.end, self.needs_review)
        position = text.find(self.quote)
        if position != -1 and text.find(self.quote, position + 1) == -1:
            self.start, self.end = position, position + len(self.quote)
        self.needs_review = True
        if (self.start, self.end, self.needs_review) != before:
            # Skips `Fragment.save()`'s index write: `Document.save()` indexes every fragment next.
            super().save(update_fields=["start", "end", "needs_review", "updated_at"])


# --- Site content -----------------------------------------------------------------------


class SiteSettings(BaseModel):
    """Editable texts of the home and About pages. There is exactly one row."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    intro_text = rich_text_field(
        verbose_name=_("introduction"), help_text=_("Introduction on the home page.")
    )
    portrait = models.FileField(
        _("portrait"), upload_to="site/", blank=True, validators=[IMAGE_EXTENSIONS]
    )
    portrait_alt = models.CharField(_("portrait text alternative"), max_length=255, blank=True)
    about_intro = rich_text_field(
        verbose_name=_("About page introduction"), help_text=_("Introduction on the About page.")
    )
    about_project = rich_text_field(
        verbose_name=_("About the project"), help_text=_("“O projekcie” on the About page.")
    )

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    def __str__(self) -> str:
        return str(_("Site settings"))

    @classmethod
    def load(cls) -> "SiteSettings":
        settings, _created = cls.objects.get_or_create(pk=1)
        return settings


class TeamMember(BaseModel):
    class Group(models.TextChoices):
        LEADERSHIP = "leadership", _("Project leadership")
        TEAM = "team", _("Team members")
        SITE = "site", _("Website development")

    name = models.CharField(_("full name"), max_length=255)
    role = models.CharField(_("role"), max_length=255, blank=True)
    bio = models.TextField(_("short biography"), blank=True)
    group = models.CharField(_("group"), max_length=20, choices=Group.choices)
    order = models.PositiveSmallIntegerField(
        _("order"), default=0, help_text=_("Lower numbers are shown first.")
    )

    class Meta:
        ordering = ("order", "name")
        verbose_name = _("team member")
        verbose_name_plural = _("team members")

    def __str__(self) -> str:
        return self.name
