"""Domain model of the archive (docs/architecture.md, section 4).

Editors work only in Django admin, so every rule that keeps the data consistent lives here:
in field definitions, database constraints, `clean()` and `save()`. There are no signals.
"""

from bisect import bisect_right
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any, ClassVar, Self

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Expression, F, Func, OuterRef, Q, Subquery, Value
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from search.models import EntityType, IndexedContent, SearchEntry, Weight

IMAGE_EXTENSIONS = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
PDF_EXTENSION = FileExtensionValidator(["pdf"])


def format_shelfmark(institution: "Institution | None", number: str) -> str:
    """Display form of a shelfmark, e.g. "ML, sygn. 1618" (US-WR-14 AC2)."""
    if not number:
        return ""
    if institution is None:
        return f"sygn. {number}"
    return f"{institution.abbreviation}, sygn. {number}"


# --- Shared behaviour -------------------------------------------------------------------


class BaseModel(models.Model):
    """Base of every model: timestamps, and a text alternative for every image (R-12).

    Any file field `X` with a companion `X_alt` field must have `X_alt` filled when `X` is set.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        errors = {}
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


def preview[M: models.Model](queryset: "models.QuerySet[M]") -> Preview[M]:
    """The first `PREVIEW_LIMIT` items of an ordered queryset (architecture section 4.5)."""
    return Preview(items=list(queryset[: settings.PREVIEW_LIMIT]), total=queryset.count())


def published_q(prefix: str = "") -> Q:
    """What the public may see (R-06): `prefix` leads to a published entity.

    Drafts are never listed, even for editors.
    """
    return Q(**{f"{prefix}status": Status.PUBLISHED})


class PublishableQuerySet[M: "Publishable"](models.QuerySet[M]):
    def published(self) -> Self:
        return self.filter(published_q())


class Publishable(BaseModel):
    """A public entity with its own page. Only published entities are public (R-06)."""

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_("Only published items are visible to the public."),
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

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


class Taggable(models.Model):
    """Tags on the whole item (US-WR-10)."""

    tags: "models.ManyToManyField[Tag, Any]" = models.ManyToManyField(
        "Tag", blank=True, related_name="%(class)ss"
    )

    class Meta:
        abstract = True

    def published_tags(self) -> "TagQuerySet":
        """The tags shown with this item. Draft tags never are (R-06)."""
        return Tag.objects.published().filter(pk__in=self.tags.values("pk"))


class Archival(models.Model):
    """An item held by an institution under a shelfmark, optionally with a text (`Document`)."""

    document_required = False
    # The reverse name from `Work` to this kind of item.
    works_lookup: ClassVar[str]
    _indexed_document_id: int | None = None

    institution = models.ForeignKey(
        "Institution",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)ss",
    )
    shelfmark = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Number only, e.g. 1618. The institution is chosen separately."),
    )
    document = models.OneToOneField(
        "Document",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s",
        help_text=_("The scan and OCR text, or the plain text, of this item."),
    )

    class Meta:
        abstract = True

    @property
    def shelfmark_display(self) -> str:
        return format_shelfmark(self.institution, self.shelfmark)

    def required_document_kind(self) -> str | None:
        """The kind of `Document` this item's text must be, or None for any kind."""
        return None

    def related_works(self) -> "WorkQuerySet":
        """The published works this item relates to, by first edition (R-03)."""
        return Work.objects.published().filter(**{self.works_lookup: self}).with_year()

    def indexed_content(self) -> IndexedContent:
        """Title, description and the whole text of a typescript, note, secondary text or
        contextual material."""
        assert isinstance(self, Publishable)
        text = self.document.text if self.document else ""
        work_ids, decades = search_filters(Work.objects.filter(**{self.works_lookup: self}))
        return IndexedContent(
            title=self.title,
            url=self.get_absolute_url(),
            texts=[
                (self.title, Weight.TITLE),
                (self.description, Weight.DESCRIPTION),
                (text, Weight.TEXT),
            ],
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
        if self._indexed_document_id not in (None, self.document_id):
            old = Fragment.objects.filter(document_id=self._indexed_document_id)
            SearchEntry.remove(EntityType.FRAGMENT, *old.values_list("pk", flat=True))
        self._indexed_document_id = self.document_id
        if self.document is None:
            return
        fragments = self.document.fragments.all()
        if owner is None:
            SearchEntry.remove(EntityType.FRAGMENT, *fragments.values_list("pk", flat=True))
            return
        for fragment in fragments:
            fragment.write_search_entry(owner)

    @classmethod
    def from_db(
        cls, db: str | None, field_names: Collection[str], values: Collection[Any], **kwargs: Any
    ) -> Self:
        """Remember the stored text, to unindex its fragments if the item gets another one."""
        item = super().from_db(db, field_names, values, **kwargs)
        item._indexed_document_id = item.__dict__.get("document_id")
        return item

    def clean(self) -> None:
        super().clean()
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


class ContentKind(models.TextChoices):
    IMAGE = "image", _("Image")
    DOCUMENT = "document", _("Document file")
    EXTERNAL_MEDIA = "external_media", _("External audio or video link")
    OCR_TEXT = "ocr_text", _("OCR text (scan + OCR file)")
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

    content_kind = models.CharField(max_length=20, choices=ContentKind.choices)
    image = models.FileField(upload_to="content/", blank=True, validators=[IMAGE_EXTENSIONS])
    image_alt = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="content/", blank=True)
    external_url = models.URLField(blank=True)

    class Meta:
        abstract = True

    def required_document_kind(self) -> str | None:
        text_kinds: dict[str, str] = {
            ContentKind.OCR_TEXT: Document.Kind.OCR,
            ContentKind.PLAIN_TEXT: Document.Kind.PLAIN,
        }
        return text_kinds.get(self.content_kind)

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
    abbreviation = models.CharField(max_length=20, unique=True, help_text=_("E.g. ML."))
    name = models.CharField(max_length=255, help_text=_("E.g. Muzeum Literatury."))

    class Meta:
        ordering = ("abbreviation",)

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
            Typescript.objects.published(),
            Note.objects.published(),
            SecondaryText.objects.published(),
            ContextualMaterial.objects.published(),
            SecondaryTextWorkLink.objects.visible(),
            MaterialWorkLink.objects.visible(),
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


class Tag(Publishable):
    class Kind(models.TextChoices):
        KEYWORD = "keyword", _("Buczkowski's keyword")
        INTERPRETATION = "interpretation", _("Interpretation")

    title = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        help_text=_("Only for filtering in the editor panel. Never public."),
    )
    related = models.ManyToManyField("self", blank=True, help_text=_("Works both ways."))

    objects = TagQuerySet.as_manager()
    # Set only by `TagQuerySet.with_occurrences()`.
    occurrences: int

    search_type = EntityType.TAG

    def get_absolute_url(self) -> str:
        return f"/tags/{self.slug}"

    def indexed_content(self) -> IndexedContent:
        work_ids, decades = search_filters(Work.objects.referred_to_by(self))
        return IndexedContent(
            title=self.title,
            url=self.get_absolute_url(),
            texts=[(self.title, Weight.TITLE), (self.description, Weight.QUOTE)],
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

    def referred_to_by(self, tag: "Tag") -> Self:
        """The works a tag refers to (US-RA-07 AC5): the tag is on the work, on a published item
        related to it, on a visible fragment of such an item, or on a visible work link."""
        carrying = Q(tags=tag) | Q(document__fragments__tags=tag)
        return self.filter(
            Q(tags=tag)
            | Q(pk__in=Typescript.objects.published().filter(carrying).values("work"))
            | Q(pk__in=Note.objects.published().filter(carrying).values("works"))
            | Q(pk__in=SecondaryText.objects.published().filter(carrying).values("works"))
            | Q(pk__in=ContextualMaterial.objects.published().filter(carrying).values("works"))
            | Q(pk__in=SecondaryTextWorkLink.objects.visible().filter(tags=tag).values("work"))
            | Q(pk__in=MaterialWorkLink.objects.visible().filter(tags=tag).values("work"))
        )


class Work(Publishable, Taggable):
    slug = models.SlugField(max_length=255, unique=True, help_text=_("Part of the page address."))
    genre = models.CharField(max_length=100, blank=True, help_text=_("E.g. powieść."))
    cover_image = models.FileField(upload_to="works/", blank=True, validators=[IMAGE_EXTENSIONS])
    cover_image_alt = models.CharField(max_length=255, blank=True)

    objects = WorkQuerySet.as_manager()
    # Set only by `WorkQuerySet.with_year()`.
    year: int | None

    search_type = EntityType.WORK

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.update_related_search_entries(self.related_items())

    def get_absolute_url(self) -> str:
        return f"/works/{self.slug}"

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        items = self.related_items()
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            self.update_related_search_entries(items)
        return result

    def related_items(self) -> list[Publishable]:
        return [
            *self.typescripts.all(),
            *self.notes.all(),
            *self.secondary_texts.all(),
            *self.materials.all(),
        ]

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
            texts=[(self.title, Weight.TITLE), (self.description, Weight.DESCRIPTION)],
            work_ids=[self.pk],
            decades=search_filters(Work.objects.filter(pk=self.pk))[1],
        )


class Edition(BaseModel):
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="editions")
    publisher = models.CharField(max_length=255)
    place = models.CharField(max_length=255)
    year = models.PositiveSmallIntegerField()
    cover_image = models.FileField(upload_to="editions/", blank=True, validators=[IMAGE_EXTENSIONS])
    cover_image_alt = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("year",)

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


class Typescript(Publishable, Taggable, Archival):
    document_required = True
    works_lookup = "typescripts"
    search_type = EntityType.TYPESCRIPT

    work = models.ForeignKey(Work, on_delete=models.PROTECT, related_name="typescripts")
    is_main = models.BooleanField(
        _("main typescript"),
        default=False,
        help_text=_("One per work. Marking this one unmarks the previous one."),
    )

    objects = PublishableQuerySet["Typescript"].as_manager()

    class Meta:
        ordering = ("shelfmark", "title")
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
        return f"/typescripts/{self.pk}"

    def validate_constraints(self, exclude: Collection[str] | None = None) -> None:
        """Skip "one main typescript per work" here: `save()` unmarks the previous one first."""
        super().validate_constraints(exclude={*(exclude or ()), "is_main"})

    def required_document_kind(self) -> str | None:
        return Document.Kind.OCR


class Note(Publishable, Taggable, MediaContent):
    works_lookup = "notes"
    search_type = EntityType.NOTE

    works = models.ManyToManyField(Work, related_name="notes")

    objects = PublishableQuerySet["Note"].as_manager()

    def get_absolute_url(self) -> str:
        return f"/notes/{self.pk}"


class SecondaryText(Publishable, Taggable, Archival):
    class Kind(models.TextChoices):
        LETTER = "letter", _("Letter")
        REVIEW = "review", _("Review")
        STUDY = "study", _("Study")
        RECORDING = "recording", _("Recording")
        OTHER = "other", _("Other")

    document_required = True
    works_lookup = "secondary_texts"
    search_type = EntityType.SECONDARY_TEXT

    kind = models.CharField(max_length=20, choices=Kind.choices)
    author = models.CharField(max_length=255, blank=True)
    source = models.CharField(
        max_length=500, blank=True, help_text=_("Publisher, place, year, pages, as one line.")
    )
    letter_date = models.DateField(null=True, blank=True, help_text=_("For letters."))
    sender = models.CharField(max_length=255, blank=True, help_text=_("For letters."))
    recipient = models.CharField(max_length=255, blank=True, help_text=_("For letters."))
    works = models.ManyToManyField(
        Work, through="SecondaryTextWorkLink", related_name="secondary_texts"
    )

    objects = PublishableQuerySet["SecondaryText"].as_manager()

    def get_absolute_url(self) -> str:
        return f"/secondary-texts/{self.pk}"


class ContextualMaterial(Publishable, Taggable, MediaContent):
    works_lookup = "materials"
    search_type = EntityType.MATERIAL

    works = models.ManyToManyField(Work, through="MaterialWorkLink", related_name="materials")

    objects = PublishableQuerySet["ContextualMaterial"].as_manager()

    def get_absolute_url(self) -> str:
        return f"/materials/{self.pk}"


class WorkLinkQuerySet[L: "SecondaryTextWorkLink | MaterialWorkLink"](models.QuerySet[L]):
    def visible(self) -> Self:
        """Links whose work and linked item are both published."""
        return self.filter(published_q("work__"), published_q(f"{self.model.item_field}__"))


class SecondaryTextWorkLink(BaseModel, Taggable):
    """A secondary text's link to a work. Its tags appear on the work page (US-RA-05)."""

    secondary_text = models.ForeignKey(
        SecondaryText, on_delete=models.CASCADE, related_name="work_links"
    )
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="secondary_text_links")

    item_field = "secondary_text"
    objects = WorkLinkQuerySet["SecondaryTextWorkLink"].as_manager()

    class Meta:
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
        ContextualMaterial, on_delete=models.CASCADE, related_name="work_links"
    )
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="material_links")

    item_field = "material"
    objects = WorkLinkQuerySet["MaterialWorkLink"].as_manager()

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=["material", "work"], name="unique_material_work"),
        )

    def __str__(self) -> str:
        return f"{self.material} ↔ {self.work}"


# --- Texts and fragments (architecture section 4.4) -------------------------------------


class Document(BaseModel):
    """The text of an archival item: a scan with its OCR text, or a plain text."""

    class Kind(models.TextChoices):
        OCR = "ocr", _("Scan + OCR text")
        PLAIN = "plain", _("Plain text")

    kind = models.CharField(max_length=10, choices=Kind.choices)
    scan = models.FileField(
        upload_to="scans/", blank=True, validators=[PDF_EXTENSION], help_text=_("PDF file.")
    )
    text = models.TextField(blank=True)
    page_offsets = ArrayField(models.PositiveIntegerField(), default=list, editable=False)

    _saved_text: str | None = None
    _saved_page_offsets: list[int] | None = None

    class Meta:
        ordering = ("-created_at",)

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
            if isinstance(owner, Publishable):
                owner.update_search_entry()
        self._saved_text = self.text
        self._saved_page_offsets = list(self.page_offsets)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Unindex the fragments first: the database deletes them without `Fragment.delete()`."""
        with transaction.atomic():
            SearchEntry.remove(EntityType.FRAGMENT, *self.fragments.values_list("pk", flat=True))
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

    def set_ocr_text(self, raw: str) -> None:
        """Load Tesseract plain-text output: pages separated by a form feed (`\\f`)."""
        pages = raw.removesuffix("\f").split("\f")
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
                {"text": _("Upload a new OCR file to change an OCR text, so pages stay aligned.")}
            )


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

    def preview(self) -> Preview["Fragment"]:
        """Featured fragments first, then text order (R-09).

        Fragments of different documents follow document IDs, not a domain order. A preview
        across documents passes its own order to `preview()` instead.
        """
        return preview(self.order_by("-is_featured", "document_id", "start", "end", "pk"))


class Fragment(BaseModel, Taggable):
    """A tagged character range of a document's text. Fragments may overlap freely."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="fragments")
    start = models.PositiveIntegerField(editable=False)
    end = models.PositiveIntegerField(editable=False)
    quote = models.TextField(editable=False, help_text=_("The selected text."))
    location = models.CharField(max_length=255, blank=True, help_text=_("E.g. rozdział I."))
    shelfmark = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Number only, e.g. 1618.0009; institution from the document."),
    )
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(
        _("featured"),
        default=False,
        help_text=_("Shown first in previews and on the home page."),
    )
    needs_review = models.BooleanField(
        default=False,
        help_text=_("The text changed. Check the fragment, then clear this box."),
    )

    objects = FragmentQuerySet.as_manager()
    # Set only by `FragmentQuerySet.with_number()`.
    number: int

    class Meta:
        ordering = ("document", "start", "end")
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
            self.write_search_entry(owner.indexed_content())
        else:
            SearchEntry.remove(EntityType.FRAGMENT, self.pk)

    def write_search_entry(self, owner: IndexedContent) -> None:
        """Index the fragment under its owner: a link into the owner's page, and its filters."""
        SearchEntry.write(
            EntityType.FRAGMENT,
            self.pk,
            IndexedContent(
                title=str(self),
                url=f"{owner.url}?fragment={self.pk}",
                texts=[(self.quote, Weight.QUOTE), (self.description, Weight.DESCRIPTION)],
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
    def shelfmark_display(self) -> str:
        owner = self.document.owner
        return format_shelfmark(owner.institution if owner else None, self.shelfmark)

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
            self.save(update_fields=["start", "end", "needs_review", "updated_at"])


# --- Site content -----------------------------------------------------------------------


class SiteSettings(BaseModel):
    """Editable texts of the home, footer and About pages. There is exactly one row."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    intro_text = models.TextField(blank=True, help_text=_("Introduction on the home page."))
    portrait = models.FileField(upload_to="site/", blank=True, validators=[IMAGE_EXTENSIONS])
    portrait_alt = models.CharField(max_length=255, blank=True)
    funding_note = models.TextField(blank=True, help_text=_("Shown in the footer."))
    about_intro = models.TextField(blank=True, help_text=_("Introduction on the About page."))
    about_project = models.TextField(blank=True, help_text=_("“O projekcie” on the About page."))

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

    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    group = models.CharField(max_length=20, choices=Group.choices)
    order = models.PositiveSmallIntegerField(
        default=0, help_text=_("Lower numbers are shown first.")
    )

    class Meta:
        ordering = ("order", "name")

    def __str__(self) -> str:
        return self.name
