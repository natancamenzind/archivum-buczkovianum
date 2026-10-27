from dataclasses import dataclass

from rest_framework import serializers

from archive.models import (
    Archival,
    ContextualMaterial,
    Document,
    Edition,
    Fragment,
    Institution,
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
)
from search.models import EntityType, SearchEntry


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

    year = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="The year of the first edition; null without editions.",
    )
    cover_image = serializers.SerializerMethodField(help_text="Empty when the work has no cover.")
    fragment_count = serializers.IntegerField(
        read_only=True, help_text="Visible fragments of the main typescript (D19); 0 without one."
    )

    class Meta:
        model = Work
        fields = (
            "slug",
            "title",
            "genre",
            "year",
            "cover_image",
            "cover_image_alt",
            "fragment_count",
        )
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_cover_image(self, work: Work) -> str:
        return work.cover_image.url if work.cover_image else ""


class TagCountSerializer(serializers.ModelSerializer[Tag]):
    """A tag with its occurrence count (US-RA-20), from a queryset with `with_occurrences()`."""

    occurrences = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ("slug", "title", "occurrences")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields


@dataclass(frozen=True)
class HomeStatistics:
    works: int
    fragments: int
    tags: int


@dataclass(frozen=True)
class HomePage:
    settings: SiteSettings
    statistics: HomeStatistics
    works: list[Work]
    tags: list[Tag]


class HomeStatisticsSerializer(serializers.Serializer[HomeStatistics]):
    works = serializers.IntegerField(help_text="Published works.")
    fragments = serializers.IntegerField(help_text="Visible fragments of every document.")
    tags = serializers.IntegerField(help_text="Published tags.")


class HomePageSerializer(serializers.Serializer[HomePage]):
    """US-RA-01. `intro` is rich text: HTML, sanitized when an editor saves it."""

    intro = serializers.CharField(source="settings.intro_text", allow_blank=True, help_text="HTML.")
    portrait = serializers.SerializerMethodField(help_text="Empty when there is no portrait.")
    portrait_alt = serializers.CharField(source="settings.portrait_alt", allow_blank=True)
    statistics = HomeStatisticsSerializer()
    works = WorkCardSerializer(many=True, help_text="By first edition.")
    tags = TagCountSerializer(
        many=True, help_text="The tag cloud: tags in use, the most frequent first."
    )

    def get_portrait(self, page: HomePage) -> str:
        return page.settings.portrait.url if page.settings.portrait else ""


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
    genre = serializers.CharField(source="work.genre", allow_blank=True)
    year = serializers.IntegerField(
        source="work.year",
        allow_null=True,
        help_text="The year of the first edition; null without editions.",
    )
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
    image = serializers.SerializerMethodField(help_text="Empty when the material has no image.")

    class Meta:
        model = ContextualMaterial
        fields = ("url", "title", "shelfmark", "image", "image_alt")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_image(self, material: ContextualMaterial) -> str:
        return material.image.url if material.image else ""


class ContextualMaterialsSerializer(serializers.Serializer[ContextualMaterials]):
    texts = MaterialTextSerializer(many=True, help_text="By title.")
    visuals = VisualMaterialSerializer(many=True, help_text="By title.")


class FragmentRowSerializer(serializers.ModelSerializer[Fragment]):
    """A row of "Fragmenty z maszynopisu" (US-RA-08 AC3), from a queryset with `with_number()`.

    The context's `institution` is the one of the fragments' document owner.
    """

    number = serializers.IntegerField(read_only=True, help_text="1-based, by position in the text.")
    shelfmark = serializers.SerializerMethodField(
        help_text='E.g. "ML, sygn. 1618.0009"; may be empty.'
    )

    class Meta:
        model = Fragment
        fields = ("id", "number", "location", "shelfmark")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_shelfmark(self, fragment: Fragment) -> str:
        institution: Institution | None = self.context["institution"]
        return format_shelfmark(institution, fragment.shelfmark)


class FragmentPreviewSerializer(serializers.Serializer[Preview[Fragment]]):
    items = FragmentRowSerializer(many=True, help_text="Featured first, then text order (R-09).")
    total = serializers.IntegerField(help_text="The number of all the fragments.")


class WorkSummarySerializer(serializers.ModelSerializer[Work]):
    """A work in a context column (R-03), from a queryset with `with_year()` and
    `with_fragment_count()`."""

    year = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="The year of the first edition; null without editions.",
    )
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
    title = serializers.CharField(source="typescript.title")
    description = serializers.CharField(
        source="typescript.description", allow_blank=True, help_text="HTML."
    )
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


class FragmentCardSerializer(serializers.ModelSerializer[Fragment]):
    """The fragment card (R-10), from a queryset with `with_number()`. Its source is the
    published item holding the fragment's document."""

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
    scan = serializers.SerializerMethodField(help_text="PDF URL; empty for a plain text.")
    start_page = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text="1-based scan page the fragment starts on; null for a plain text.",
    )
    shelfmark = serializers.CharField(
        source="shelfmark_display",
        read_only=True,
        help_text='E.g. "ML, sygn. 1618.0009"; may be empty.',
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
            "location",
            "quote",
            "scan",
            "start_page",
            "shelfmark",
            "description",
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
        return f"{owner.get_absolute_url()}?fragment={fragment.pk}"

    def get_work(self, fragment: Fragment) -> str:
        return ", ".join(work.title for work in self.owner(fragment).related_works())

    def get_scan(self, fragment: Fragment) -> str:
        return fragment.document.scan.url if fragment.document.scan else ""


class FragmentCardPreviewSerializer(serializers.Serializer[Preview[Fragment]]):
    items = FragmentCardSerializer(many=True, help_text="Featured first, then text order (R-09).")
    total = serializers.IntegerField(help_text="The number of all the fragments.")


class NoteCardSerializer(serializers.ModelSerializer[Note]):
    """The note card (US-RA-04 AC3). `description` is rich text: HTML, sanitized when an editor
    saves it."""

    url = serializers.CharField(source="get_absolute_url", read_only=True)
    shelfmark = serializers.CharField(
        source="shelfmark_display", read_only=True, help_text='E.g. "ML, sygn. 1678"; may be empty.'
    )
    description = serializers.CharField(read_only=True, help_text="HTML.")
    image = serializers.SerializerMethodField(help_text="Empty when the note is not an image.")
    tags = TagChipSerializer(many=True, read_only=True, help_text="Published tags, by name.")

    class Meta:
        model = Note
        fields = ("url", "title", "shelfmark", "description", "image", "image_alt", "tags")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_image(self, note: Note) -> str:
        return note.image.url if note.image else ""


@dataclass(frozen=True)
class WorkPage:
    work: Work
    main_typescript: int | None
    fragments: Preview[Fragment]
    typescripts: list[Typescript]
    notes: list[Note]
    tags: list[Tag]
    materials: ContextualMaterials


class WorkPageSerializer(serializers.Serializer[WorkPage]):
    """US-RA-04, from a work with `with_year()`. `description` is rich text: HTML, sanitized when
    an editor saves it."""

    slug = serializers.CharField(source="work.slug")
    title = serializers.CharField(source="work.title")
    description = serializers.CharField(
        source="work.description", allow_blank=True, help_text="HTML."
    )
    year = serializers.IntegerField(
        source="work.year",
        allow_null=True,
        help_text="The year of the first edition; null without editions.",
    )
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


@dataclass(frozen=True)
class SecondaryTextPage:
    secondary_text: SecondaryText
    works: list[Work]
    fragments: Preview[Fragment]
    tags: list[Tag]


class SecondaryTextPageSerializer(serializers.Serializer[SecondaryTextPage]):
    """US-RA-10. `description` is rich text: HTML, sanitized when an editor saves it."""

    id = serializers.IntegerField(source="secondary_text.pk")
    title = serializers.CharField(source="secondary_text.title")
    description = serializers.CharField(
        source="secondary_text.description", allow_blank=True, help_text="HTML."
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


class DocumentFragmentSerializer(FragmentRowSerializer):
    """A fragment for the reader (R-11), from a queryset with `with_number()`.

    The context holds the fragments' `document` and the `institution` of its owner.
    """

    start_page = serializers.SerializerMethodField(
        help_text="1-based scan page the fragment starts on; null for a plain text."
    )
    tags = TagChipSerializer(many=True, read_only=True, help_text="Published tags, by name.")

    class Meta:
        model = Fragment
        fields = ("id", "start", "end", "number", "start_page", "location", "shelfmark", "tags")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_start_page(self, fragment: Fragment) -> int | None:
        document: Document = self.context["document"]
        return document.page_number(fragment.start)


class DocumentSerializer(serializers.ModelSerializer[Document]):
    """The text of an item for the reader (R-11, architecture section 4.4)."""

    scan = serializers.SerializerMethodField(help_text="PDF URL; empty for a plain text.")
    fragments = DocumentFragmentSerializer(many=True, read_only=True, help_text="By position.")

    class Meta:
        model = Document
        fields = ("id", "kind", "text", "page_offsets", "scan", "fragments")
        # Output only, so the schema marks every field as present, the blank ones too.
        read_only_fields = fields

    def get_scan(self, document: Document) -> str:
        return document.scan.url if document.scan else ""
