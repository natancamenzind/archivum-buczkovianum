from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

from django.db.models.fields.files import FieldFile
from rest_framework import serializers

from archive.models import (
    Archival,
    BibliographyEntry,
    ContentKind,
    ContextualMaterial,
    Document,
    Edition,
    Fragment,
    Note,
    Preview,
    Publishable,
    SecondaryText,
    SiteSettings,
    Tag,
    TeamMember,
    Typescript,
    Work,
    format_shelfmark,
    fragment_shelfmark,
    fragment_url,
)
from search.models import MAX_DECADE, MAX_ID, EntityType, SearchEntry
from search.query import Hit, Sort, Tab


class FileUrlField(serializers.CharField):
    """The URL of a stored file; empty without one."""

    def get_attribute(self, instance: Any) -> str:
        file = cast(FieldFile, super().get_attribute(instance))
        return file.url if file else ""


class YearField(serializers.IntegerField):
    """The year of a work's first edition, from `WorkQuerySet.with_year()`."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            allow_null=True,
            help_text="The year of the first edition; null without editions.",
            **kwargs,
        )


@dataclass(frozen=True)
class TeamGroup:
    group: TeamMember.Group
    members: list[TeamMember]


@dataclass(frozen=True)
class AboutPage:
    intro: str
    project: str
    team: list[TeamGroup]


class TeamMemberSerializer(serializers.ModelSerializer[TeamMember]):
    class Meta:
        model = TeamMember
        fields = ("name", "role", "bio")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class TeamGroupSerializer(serializers.Serializer[TeamGroup]):
    group = serializers.ChoiceField(choices=TeamMember.Group.choices)
    members = TeamMemberSerializer(many=True)


class AboutPageSerializer(serializers.Serializer[AboutPage]):
    """US-RA-13. `intro` and `project` are rich text: HTML, sanitized when an editor saves it."""

    intro = serializers.CharField(allow_blank=True, help_text="HTML.")
    project = serializers.CharField(allow_blank=True, help_text="HTML.")
    team = TeamGroupSerializer(
        many=True, help_text="Groups that have members, in the order of TeamMember.Group."
    )


class WorkCardSerializer(serializers.ModelSerializer[Work]):
    """The work card (US-RA-01 AC3), from a queryset with `with_year()` and
    `with_fragment_count()`."""

    year = YearField(read_only=True)
    cover_image = FileUrlField(read_only=True, help_text="Empty when the work has no cover.")
    fragment_count = serializers.IntegerField(
        read_only=True, help_text="Visible fragments of the main typescript (D19); 0 without one."
    )

    class Meta:
        model = Work
        fields = (
            "slug",
            "title",
            "year",
            "cover_image",
            "cover_image_alt",
            "fragment_count",
        )
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class TagCountSerializer(serializers.ModelSerializer[Tag]):
    """A tag with its occurrence count (US-RA-20), from a queryset with `with_occurrences()`."""

    occurrences = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ("slug", "title", "occurrences")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class TypescriptGroup:
    work: Work
    typescripts: list[Typescript]


class TypescriptRowSerializer(serializers.ModelSerializer[Typescript]):
    shelfmark = serializers.CharField(
        source="shelfmark_display", read_only=True, help_text='E.g. "ML, sygn. 1618"; may be empty.'
    )

    class Meta:
        model = Typescript
        fields = ("id", "title", "shelfmark")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class TypescriptGroupSerializer(serializers.Serializer[TypescriptGroup]):
    """A work's group on the typescripts list (US-RA-19 AC2), from a work with `with_year()`."""

    slug = serializers.CharField(source="work.slug")
    title = serializers.CharField(source="work.title")
    year = YearField(source="work.year")
    typescripts = TypescriptRowSerializer(many=True, help_text="By shelfmark, as numbers.")


class SuggestionSerializer(serializers.ModelSerializer[SearchEntry]):
    """A suggestion under the search fields (US-RA-17): a work or a tag, and its page."""

    type = serializers.ChoiceField(
        source="entity_type", choices=(EntityType.WORK, EntityType.TAG), read_only=True
    )

    class Meta:
        model = SearchEntry
        fields = ("type", "title", "url")
        # Output only, so the schema marks every field as present.
        read_only_fields = fields


class TagChipSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ("slug", "title")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class ContextualMaterials:
    """The contextual materials block (R-08)."""

    texts: list[SecondaryText | ContextualMaterial]
    visuals: list[ContextualMaterial]


class MaterialTextSerializer(serializers.Serializer[SecondaryText | ContextualMaterial]):
    """A row of "Teksty sekundarne" (R-08): a secondary text, or a contextual material that is
    not an image, which shows its title only (D5)."""

    url = serializers.CharField(source="get_absolute_url")
    author = serializers.SerializerMethodField()
    title = serializers.CharField()
    publication = serializers.SerializerMethodField(help_text="Publisher, place, year, pages.")

    def get_author(self, item: SecondaryText | ContextualMaterial) -> str:
        return item.author if isinstance(item, SecondaryText) else ""

    def get_publication(self, item: SecondaryText | ContextualMaterial) -> str:
        return item.source if isinstance(item, SecondaryText) else ""


class VisualMaterialSerializer(serializers.ModelSerializer[ContextualMaterial]):
    """A thumbnail of "Materiały wizualne" (R-08), captioned with title and shelfmark."""

    url = serializers.CharField(source="get_absolute_url", read_only=True)
    shelfmark = serializers.CharField(
        source="shelfmark_display", read_only=True, help_text='E.g. "ML, sygn. 1700"; may be empty.'
    )
    image = FileUrlField(read_only=True, help_text="Empty when the material has no image.")

    class Meta:
        model = ContextualMaterial
        fields = ("url", "title", "shelfmark", "image", "image_alt")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class ContextualMaterialsSerializer(serializers.Serializer[ContextualMaterials]):
    texts = MaterialTextSerializer(many=True, help_text="By title.")
    visuals = VisualMaterialSerializer(many=True, help_text="By title.")


class FragmentRowSerializer(serializers.ModelSerializer[Fragment]):
    """A row of "Fragmenty z maszynopisu" (US-RA-08 AC3), from a queryset with `with_number()`.

    The context's `owner` is the item whose text holds the fragments.
    """

    number = serializers.IntegerField(read_only=True, help_text="1-based, by position in the text.")
    scan_number = serializers.SerializerMethodField(
        help_text='The scan page the fragment starts on, e.g. "19"; empty for a plain text.'
    )
    shelfmark = serializers.SerializerMethodField(
        help_text='E.g. "ML, sygn. 1618.19"; may be empty.'
    )

    class Meta:
        model = Fragment
        fields = ("id", "number", "scan_number", "shelfmark")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def page(self, fragment: Fragment) -> int | None:
        owner: Archival = self.context["owner"]
        return owner.document.page_number(fragment.start) if owner.document else None

    def get_scan_number(self, fragment: Fragment) -> str:
        return str(self.page(fragment) or "")

    def get_shelfmark(self, fragment: Fragment) -> str:
        owner: Archival = self.context["owner"]
        number = fragment_shelfmark(owner.shelfmark, self.page(fragment))
        return format_shelfmark(owner.institution, number)


class FragmentPreviewSerializer(serializers.Serializer[Preview[Fragment]]):
    items = FragmentRowSerializer(many=True, help_text="Featured first, then text order (R-09).")
    total = serializers.IntegerField(help_text="The number of all the fragments.")


class WorkSummarySerializer(serializers.ModelSerializer[Work]):
    """A work in a context column (R-03), from a queryset with `with_year()` and
    `with_fragment_count()`."""

    year = YearField(read_only=True)
    fragment_count = serializers.IntegerField(
        read_only=True, help_text="Visible fragments of the main typescript (D19); 0 without one."
    )

    class Meta:
        model = Work
        fields = ("slug", "title", "year", "fragment_count")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class TypescriptPage:
    typescript: Typescript
    work: Work | None
    work_typescripts: list[Typescript]
    fragments: Preview[Fragment]
    tags: list[Tag]
    materials: ContextualMaterials


class TypescriptPageSerializer(serializers.Serializer[TypescriptPage]):
    """US-RA-08. `description` is rich text: HTML, sanitized when an editor saves it."""

    id = serializers.IntegerField(source="typescript.pk")
    is_draft = serializers.BooleanField(
        source="typescript.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="typescript.title")
    description = serializers.CharField(
        source="typescript.description", allow_blank=True, help_text="HTML."
    )
    header_image = FileUrlField(
        source="typescript.header_image",
        help_text="Shown behind the title; empty when there is none.",
    )
    header_image_alt = serializers.CharField(source="typescript.header_image_alt", allow_blank=True)
    shelfmark = serializers.CharField(
        source="typescript.shelfmark_display", help_text='E.g. "ML, sygn. 1618"; may be empty.'
    )
    document = serializers.IntegerField(
        source="typescript.document_id", help_text="The text for the reader: /api/documents/<id>/."
    )
    page_count = serializers.IntegerField(source="typescript.document.page_count")
    work = WorkSummarySerializer(allow_null=True, help_text="Null while the work is a draft.")
    work_typescripts = TypescriptRowSerializer(
        many=True, help_text="The work's typescripts by shelfmark, this one included."
    )
    fragments = FragmentPreviewSerializer()
    tags = TagChipSerializer(
        many=True, help_text="Tags on the typescript and on its fragments, by name."
    )
    materials = ContextualMaterialsSerializer(help_text="Those linked to the typescript's work.")


class EditionSerializer(serializers.ModelSerializer[Edition]):
    class Meta:
        model = Edition
        fields = ("year", "publisher", "place")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


class BibliographyPreviewSerializer(serializers.Serializer[Preview[BibliographyEntry]]):
    items = serializers.ListField(
        child=serializers.CharField(), help_text="The first entries' texts, in order."
    )
    total = serializers.IntegerField(help_text="The number of all the entries.")


class FragmentCardSerializer(serializers.ModelSerializer[Fragment]):
    """The fragment card (R-10), from a queryset with `with_number()`. Its source is the
    published item holding the fragment's document.

    Without the context's `works` (the sources' published works by document ID, by year), each
    card queries its source's works.
    """

    url = serializers.SerializerMethodField(help_text="The source, scrolled to the fragment.")
    source_type = serializers.ChoiceField(
        source="document.owner.search_type",
        choices=(
            EntityType.TYPESCRIPT,
            EntityType.NOTE,
            EntityType.SECONDARY_TEXT,
            EntityType.MATERIAL,
        ),
        read_only=True,
    )
    work = serializers.SerializerMethodField(help_text="The source's published works, by year.")
    number = serializers.IntegerField(read_only=True, help_text="1-based, by position in the text.")
    scan_number = serializers.CharField(
        source="scan_display",
        read_only=True,
        help_text='The scan page the fragment starts on, e.g. "19"; empty for a plain text.',
    )
    scan = FileUrlField(
        source="document.scan", read_only=True, help_text="PDF URL; empty for a plain text."
    )
    start_page = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="1-based scan page the fragment starts on; null for a plain text.",
    )
    shelfmark = serializers.CharField(
        source="shelfmark_display",
        read_only=True,
        help_text='E.g. "ML, sygn. 1618.19"; may be empty.',
    )
    tags = TagChipSerializer(many=True, read_only=True, help_text="Published tags, by name.")

    class Meta:
        model = Fragment
        fields = (
            "id",
            "url",
            "source_type",
            "work",
            "number",
            "scan_number",
            "quote",
            "scan",
            "start_page",
            "shelfmark",
            "tags",
        )
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def owner(self, fragment: Fragment) -> Archival:
        owner = fragment.document.owner
        assert owner is not None
        return owner

    def get_url(self, fragment: Fragment) -> str:
        owner = self.owner(fragment)
        assert isinstance(owner, Publishable)
        return fragment_url(owner.get_absolute_url(), fragment.pk)

    def get_work(self, fragment: Fragment) -> str:
        works: dict[int, list[Work]] | None = self.context.get("works")
        related = (
            self.owner(fragment).related_works()
            if works is None
            else works.get(fragment.document_id, [])
        )
        return ", ".join(work.title for work in related)


class FragmentCardPreviewSerializer(serializers.Serializer[Preview[Fragment]]):
    items = FragmentCardSerializer(many=True, help_text="Featured first, then text order (R-09).")
    total = serializers.IntegerField(help_text="The number of all the fragments.")


class NoteCardSerializer(serializers.ModelSerializer[Note]):
    """The note card (US-RA-04 AC3)."""

    url = serializers.CharField(source="get_absolute_url", read_only=True)
    shelfmark = serializers.CharField(
        source="shelfmark_display", read_only=True, help_text='E.g. "ML, sygn. 1678"; may be empty.'
    )
    image = FileUrlField(read_only=True, help_text="Empty when the note is not an image.")
    tags = TagChipSerializer(many=True, read_only=True, help_text="Published tags, by name.")

    class Meta:
        model = Note
        fields = ("url", "title", "shelfmark", "image", "image_alt", "tags")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class WorkPage:
    work: Work
    main_typescript: int | None
    fragments: Preview[Fragment]
    typescripts: list[Typescript]
    notes: list[Note]
    tags: list[Tag]
    materials: ContextualMaterials
    bibliography: Preview[BibliographyEntry]


class WorkPageSerializer(serializers.Serializer[WorkPage]):
    """US-RA-04, from a work with `with_year()`. `description` is rich text: HTML, sanitized when
    an editor saves it."""

    slug = serializers.CharField(source="work.slug")
    is_draft = serializers.BooleanField(
        source="work.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="work.title")
    description = serializers.CharField(
        source="work.description", allow_blank=True, help_text="HTML."
    )
    header_image = FileUrlField(
        source="work.header_image", help_text="Shown behind the title; empty when there is none."
    )
    header_image_alt = serializers.CharField(source="work.header_image_alt", allow_blank=True)
    year = YearField(source="work.year")
    editions = EditionSerializer(source="work.editions", many=True, help_text="By year.")
    main_typescript = serializers.IntegerField(
        allow_null=True,
        help_text="The typescript whose fragments the preview shows; null without a published one.",
    )
    fragments = FragmentCardPreviewSerializer(help_text="The main typescript's visible fragments.")
    typescripts = TypescriptRowSerializer(many=True, help_text="By shelfmark, as numbers.")
    notes = NoteCardSerializer(many=True, help_text="By title.")
    tags = TagChipSerializer(
        many=True, help_text="Tags that refer to the work (US-RA-07 AC5), by name."
    )
    materials = ContextualMaterialsSerializer(help_text="Those linked to the work.")
    bibliography = BibliographyPreviewSerializer(help_text="Empty when the work has no entries.")


class BibliographyWorkSerializer(serializers.ModelSerializer[Work]):
    """A work in the bibliography page's side column, from a queryset with `with_year()`."""

    year = YearField(read_only=True)

    class Meta:
        model = Work
        fields = ("slug", "title", "year")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class BibliographyPage:
    work: Work
    entries: list[BibliographyEntry]
    works: list[Work]


class BibliographyPageSerializer(serializers.Serializer[BibliographyPage]):
    """US-RA-21."""

    slug = serializers.CharField(source="work.slug")
    is_draft = serializers.BooleanField(
        source="work.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="work.title")
    entries = serializers.ListField(
        child=serializers.CharField(), help_text="Every entry's text, in order."
    )
    works = BibliographyWorkSerializer(
        many=True, help_text="Published works with a bibliography, by first edition."
    )


@dataclass(frozen=True)
class SecondaryTextPage:
    secondary_text: SecondaryText
    works: list[Work]
    fragments: Preview[Fragment]
    tags: list[Tag]


class SecondaryTextPageSerializer(serializers.Serializer[SecondaryTextPage]):
    """US-RA-10. `description` is rich text: HTML, sanitized when an editor saves it."""

    id = serializers.IntegerField(source="secondary_text.pk")
    is_draft = serializers.BooleanField(
        source="secondary_text.is_draft",
        help_text="True only for staff previewing a draft (US-WR-13).",
    )
    title = serializers.CharField(source="secondary_text.title")
    description = serializers.CharField(
        source="secondary_text.description", allow_blank=True, help_text="HTML."
    )
    header_image = FileUrlField(
        source="secondary_text.header_image",
        help_text="Shown behind the title; empty when there is none.",
    )
    header_image_alt = serializers.CharField(
        source="secondary_text.header_image_alt", allow_blank=True
    )
    kind = serializers.ChoiceField(source="secondary_text.kind", choices=SecondaryText.Kind.choices)
    sender = serializers.CharField(
        source="secondary_text.sender", allow_blank=True, help_text="For letters; may be empty."
    )
    letter_date = serializers.DateField(
        source="secondary_text.letter_date", allow_null=True, help_text="For letters."
    )
    document = serializers.IntegerField(
        source="secondary_text.document_id",
        help_text="The text for the reader: /api/documents/<id>/.",
    )
    works = WorkSummarySerializer(many=True, help_text="Related works, by first edition (R-03).")
    fragments = FragmentCardPreviewSerializer(
        help_text="Typescript fragments sharing a tag with the text or its fragments."
    )
    tags = TagChipSerializer(
        many=True, help_text="Tags on the text, its fragments and its work links, by name."
    )


class MediaContentSerializer(serializers.Serializer[Note | ContextualMaterial]):
    """The content of a note or contextual material (US-RA-11 AC3): only the field of its kind
    is filled."""

    kind = serializers.ChoiceField(source="content_kind", choices=ContentKind.choices)
    image = FileUrlField(read_only=True, help_text="Empty unless the kind is `image`.")
    image_alt = serializers.CharField(allow_blank=True)
    file = FileUrlField(read_only=True, help_text="Empty unless the kind is `document`.")
    external_url = serializers.CharField(
        allow_blank=True, help_text="An audio or video link; empty unless `external_media`."
    )
    document = serializers.IntegerField(
        source="document_id",
        allow_null=True,
        help_text="The text for the reader, /api/documents/<id>/; null unless a text kind.",
    )


@dataclass(frozen=True)
class NotePage:
    note: Note
    works: list[Work]
    fragments: Preview[Fragment]
    tags: list[Tag]


class NotePageSerializer(serializers.Serializer[NotePage]):
    """US-RA-11."""

    id = serializers.IntegerField(source="note.pk")
    is_draft = serializers.BooleanField(
        source="note.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="note.title")
    header_image = FileUrlField(
        source="note.header_image", help_text="Shown behind the title; empty when there is none."
    )
    header_image_alt = serializers.CharField(source="note.header_image_alt", allow_blank=True)
    shelfmark = serializers.CharField(
        source="note.shelfmark_display", help_text='E.g. "ML, sygn. 1678"; may be empty.'
    )
    content = MediaContentSerializer(source="note")
    works = WorkSummarySerializer(many=True, help_text="Related works, by first edition (R-03).")
    fragments = FragmentCardPreviewSerializer(
        help_text="Typescript fragments sharing a tag with the note or its fragments."
    )
    tags = TagChipSerializer(many=True, help_text="Tags on the note and its fragments, by name.")


@dataclass(frozen=True)
class MaterialPage:
    material: ContextualMaterial
    works: list[Work]
    fragments: Preview[Fragment]
    tags: list[Tag]


class MaterialPageSerializer(serializers.Serializer[MaterialPage]):
    """US-RA-12. `description` is rich text: HTML, sanitized when an editor saves it. The type
    line's kind is `content.kind`."""

    id = serializers.IntegerField(source="material.pk")
    is_draft = serializers.BooleanField(
        source="material.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="material.title")
    description = serializers.CharField(
        source="material.description", allow_blank=True, help_text="HTML."
    )
    header_image = FileUrlField(
        source="material.header_image",
        help_text="Shown behind the title; empty when there is none.",
    )
    header_image_alt = serializers.CharField(source="material.header_image_alt", allow_blank=True)
    shelfmark = serializers.CharField(
        source="material.shelfmark_display", help_text='E.g. "ML, sygn. 1700"; may be empty.'
    )
    content = MediaContentSerializer(source="material")
    works = WorkSummarySerializer(many=True, help_text="Related works, by first edition (R-03).")
    fragments = FragmentCardPreviewSerializer(
        help_text="Typescript fragments sharing a tag with the material or its fragments."
    )
    tags = TagChipSerializer(
        many=True, help_text="Tags on the material, its fragments and its work links, by name."
    )


@dataclass(frozen=True)
class TagPage:
    tag: Tag
    works: list[Work]
    fragments: list[Fragment]
    notes: list[Note]
    related: list[Tag]
    materials: ContextualMaterials


class TagPageSerializer(serializers.Serializer[TagPage]):
    """US-RA-07, from a tag with `with_occurrences()`. `description` is rich text: HTML,
    sanitized when an editor saves it."""

    slug = serializers.CharField(source="tag.slug")
    is_draft = serializers.BooleanField(
        source="tag.is_draft", help_text="True only for staff previewing a draft (US-WR-13)."
    )
    title = serializers.CharField(source="tag.title")
    description = serializers.CharField(
        source="tag.description", allow_blank=True, help_text="HTML."
    )
    header_image = FileUrlField(
        source="tag.header_image", help_text="Shown behind the title; empty when there is none."
    )
    header_image_alt = serializers.CharField(source="tag.header_image_alt", allow_blank=True)
    occurrences = serializers.IntegerField(source="tag.occurrences")
    works = WorkSummarySerializer(
        many=True,
        help_text="The works the tag refers to (US-RA-07 AC5), by first edition. "
        "`fragment_count` counts the main typescript's fragments that carry the tag (D19).",
    )
    fragments = FragmentCardSerializer(
        many=True, help_text="Every visible fragment with the tag: by work, then text order."
    )
    notes = NoteCardSerializer(
        many=True, help_text="Notes with the tag on the whole note or a fragment, by title."
    )
    related = TagChipSerializer(many=True, help_text="Published related tags, by name.")
    materials = ContextualMaterialsSerializer(
        help_text="Those with the tag on the whole item, a fragment, or a work link."
    )


class DocumentFragmentSerializer(FragmentRowSerializer):
    """A fragment for the reader (R-11), from a queryset with `with_number()`.

    The context's `owner` is the item whose text holds the fragments.
    """

    start_page = serializers.SerializerMethodField(
        help_text="1-based scan page the fragment starts on; null for a plain text."
    )
    tags = TagChipSerializer(many=True, read_only=True, help_text="Published tags, by name.")

    class Meta:
        model = Fragment
        fields = ("id", "start", "end", "number", "start_page", "scan_number", "shelfmark", "tags")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_start_page(self, fragment: Fragment) -> int | None:
        return self.page(fragment)


class DocumentSerializer(serializers.ModelSerializer[Document]):
    """The text of an item for the reader (R-11, architecture section 4.4)."""

    scan = FileUrlField(read_only=True, help_text="PDF URL; empty for a plain text.")
    is_draft = serializers.BooleanField(
        source="owner.is_draft",
        read_only=True,
        help_text="True only for staff previewing a draft (US-WR-13).",
    )
    fragments = DocumentFragmentSerializer(many=True, read_only=True, help_text="By position.")

    class Meta:
        model = Document
        fields = ("id", "kind", "text", "page_offsets", "scan", "is_draft", "fragments")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class Found[M]:
    """A search result: the entity and its hit (US-RA-15)."""

    item: M
    hit: Hit


@dataclass(frozen=True)
class WorkFacet:
    work: Work
    count: int


@dataclass(frozen=True)
class DecadeFacet:
    decade: int
    count: int


@dataclass(frozen=True)
class SearchFacets:
    """The counts next to every tab and filter value (US-RA-16 AC1, AC2)."""

    tabs: dict[str, int]
    works: list[WorkFacet]
    decades: list[DecadeFacet]
    has_scan: int
    has_text: int


@dataclass(frozen=True)
class SearchPage:
    facets: SearchFacets
    works: list[Found[Work]]
    tags: list[Found[Tag]]
    fragments: list[Fragment]
    notes: list[Found[Note]]
    typescripts: list[Found[Typescript]]
    secondary_texts: list[Found[SecondaryText]]
    materials: list[Found[ContextualMaterial]]
    suggested_tags: list[Tag]

    @property
    def total(self) -> int:
        return sum(
            len(group)
            for group in (
                self.works,
                self.tags,
                self.fragments,
                self.notes,
                self.typescripts,
                self.secondary_texts,
                self.materials,
            )
        )


class WorkResultSerializer(serializers.Serializer[Found[Work]]):
    """A work result (US-RA-15 AC5), from a work with `with_year()`. Works show no snippet."""

    url = serializers.CharField(source="hit.entry.url")
    title = serializers.CharField(source="item.title")
    year = YearField(source="item.year")
    fragments = serializers.SerializerMethodField(
        help_text="The work's fragments that match the query."
    )

    def get_fragments(self, found: Found[Work]) -> int:
        work_fragments: dict[int, int] = self.context["work_fragments"]
        return work_fragments.get(found.item.pk, 0)


class SnippetField(serializers.CharField):
    def __init__(self) -> None:
        super().__init__(
            source="hit.snippet",
            allow_blank=True,
            help_text="HTML: the escaped text around the match, the search terms in <mark>.",
        )


class TagResultSerializer(serializers.Serializer[Found[Tag]]):
    """A tag result, from a tag with `with_occurrences()`. The snippet is cut from its
    description."""

    url = serializers.CharField(source="hit.entry.url")
    title = serializers.CharField(source="item.title")
    occurrences = serializers.IntegerField(source="item.occurrences")
    snippet = SnippetField()


class ItemResultSerializer(serializers.Serializer[Found[Archival]]):
    """A note, typescript, secondary text or contextual material result."""

    url = serializers.SerializerMethodField(
        help_text="The item's page; with `?q=` naming the first match, for the reader (R-11 AC3)."
    )
    title = serializers.CharField(source="hit.entry.title")
    shelfmark = serializers.CharField(
        source="item.shelfmark_display", help_text='E.g. "ML, sygn. 1678"; may be empty.'
    )
    snippet = SnippetField()

    def get_url(self, found: Found[Archival]) -> str:
        url, term = found.hit.entry.url, found.hit.term
        return f"{url}?{urlencode({'q': term})}" if term else url


class SearchParamsSerializer(serializers.Serializer[None]):
    """The search page's query string (US-RA-16 AC4). The values of one filter are alternatives;
    different filters combine."""

    q = serializers.CharField(
        default="", allow_blank=True, help_text="Web search syntax: quoted phrases, or, -word."
    )
    tab = serializers.ChoiceField(Tab.choices, default=Tab.ALL)
    work = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=MAX_ID),
        default=list,
        help_text="Ids of published works.",
    )
    decade = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=MAX_DECADE),
        default=list,
        help_text="Decades of first editions, e.g. 1940 for 1940 to 1949.",
    )
    has_scan = serializers.BooleanField(default=False)
    has_text = serializers.BooleanField(default=False)
    sort = serializers.ChoiceField(
        Sort.choices,
        default=Sort.RELEVANCE,
        help_text="Within each group. An empty query is always sorted by title.",
    )


class TabCountsSerializer(serializers.Serializer[dict[str, int]]):
    all = serializers.IntegerField()
    works = serializers.IntegerField()
    fragments = serializers.IntegerField()
    notes = serializers.IntegerField()
    tags = serializers.IntegerField()


class WorkFacetSerializer(serializers.Serializer[WorkFacet]):
    id = serializers.IntegerField(source="work.pk")
    title = serializers.CharField(source="work.title")
    count = serializers.IntegerField()


class DecadeFacetSerializer(serializers.Serializer[DecadeFacet]):
    decade = serializers.IntegerField(help_text="E.g. 1940 for 1940 to 1949.")
    count = serializers.IntegerField()


class SearchFacetsSerializer(serializers.Serializer[SearchFacets]):
    """Each filter's counts apply the tab and the other filters, but not that filter itself."""

    tabs = TabCountsSerializer(help_text="Results in each tab, with the filters applied.")
    works = WorkFacetSerializer(
        many=True,
        help_text="Works with results in the tab, and the selected ones, by first edition.",
    )
    decades = DecadeFacetSerializer(
        many=True, help_text="Decades with results in the tab, and the selected ones, in order."
    )
    has_scan = serializers.IntegerField(help_text="Results with a scan.")
    has_text = serializers.IntegerField(help_text="Results with a transcription.")


class SearchPageSerializer(serializers.Serializer[SearchPage]):
    """The search results (US-RA-15, US-RA-16): the groups of the tab, each by relevance or by
    title, as asked, and the facet counts.

    The context's `work_fragments` holds the matching fragments of each work, by work id, and
    `works` the fragment cards' works (see `FragmentCardSerializer`).
    """

    facets = SearchFacetsSerializer()
    total = serializers.IntegerField(help_text="Results in all the groups.")
    works = WorkResultSerializer(many=True)
    tags = TagResultSerializer(many=True)
    fragments = FragmentCardSerializer(many=True)
    notes = ItemResultSerializer(many=True)
    typescripts = ItemResultSerializer(many=True)
    secondary_texts = ItemResultSerializer(many=True)
    materials = ItemResultSerializer(many=True)
    suggested_tags = TagCountSerializer(
        many=True, help_text="The most frequent tags, only when nothing was found (US-RA-15 AC8)."
    )


@dataclass(frozen=True)
class HomeStatistics:
    works: int
    fragments: int
    tags: int


@dataclass(frozen=True)
class FeaturedFragment:
    fragment: Fragment
    work: WorkFacet | None


@dataclass(frozen=True)
class HomePage:
    settings: SiteSettings
    statistics: HomeStatistics
    works: list[Work]
    featured: FeaturedFragment | None
    tags: list[Tag]


class HomeStatisticsSerializer(serializers.Serializer[HomeStatistics]):
    works = serializers.IntegerField(help_text="Published works.")
    fragments = serializers.IntegerField(help_text="Visible fragments of every document.")
    tags = serializers.IntegerField(help_text="Published tags.")


class FeaturedFragmentSerializer(serializers.Serializer[FeaturedFragment]):
    """US-RA-02. The context's `works` holds the card's works (see `FragmentCardSerializer`)."""

    fragment = FragmentCardSerializer()
    work = WorkFacetSerializer(
        allow_null=True,
        help_text=(
            "The source's first published work, by first edition, and the count of the "
            "Fragmenty search filtered to it; null when the source has no published work."
        ),
    )


class HomePageSerializer(serializers.Serializer[HomePage]):
    """US-RA-01. `intro` is rich text: HTML, sanitized when an editor saves it."""

    intro = serializers.CharField(source="settings.intro_text", allow_blank=True, help_text="HTML.")
    portrait = FileUrlField(
        source="settings.portrait", read_only=True, help_text="Empty when there is no portrait."
    )
    portrait_alt = serializers.CharField(source="settings.portrait_alt", allow_blank=True)
    statistics = HomeStatisticsSerializer()
    works = WorkCardSerializer(many=True, help_text="By first edition.")
    featured = FeaturedFragmentSerializer(
        allow_null=True, help_text="A random visible featured fragment; null when there is none."
    )
    tags = TagCountSerializer(
        many=True, help_text="The tag cloud: tags in use, the most frequent first."
    )
