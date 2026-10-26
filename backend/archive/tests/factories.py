from factory.declarations import Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory, FileField

from archive.models import (
    ContentKind,
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


class InstitutionFactory(DjangoModelFactory[Institution]):
    class Meta:
        model = Institution
        django_get_or_create = ("abbreviation",)

    abbreviation = "ML"
    name = "Muzeum Literatury"


class TagFactory(DjangoModelFactory[Tag]):
    class Meta:
        model = Tag

    title = Sequence(lambda n: f"Tag {n}")
    slug = Sequence(lambda n: f"tag-{n}")
    kind = Tag.Kind.KEYWORD


class WorkFactory(DjangoModelFactory[Work]):
    class Meta:
        model = Work

    title = Sequence(lambda n: f"Work {n}")
    slug = Sequence(lambda n: f"work-{n}")
    genre = "powieść"


class EditionFactory(DjangoModelFactory[Edition]):
    class Meta:
        model = Edition

    work = SubFactory(WorkFactory)
    publisher = "Czytelnik"
    place = "Warszawa"
    year = 1947


class DocumentFactory(DjangoModelFactory[Document]):
    class Meta:
        model = Document

    class Params:
        ocr = Trait(
            kind=Document.Kind.OCR,
            scan=FileField(filename="scan.pdf"),
            page_offsets=[0],
        )

    kind = Document.Kind.PLAIN
    text = "Czarny potok płynie przez las."


class TypescriptFactory(DjangoModelFactory[Typescript]):
    class Meta:
        model = Typescript

    title = Sequence(lambda n: f"Typescript {n}")
    work = SubFactory(WorkFactory)
    document = SubFactory(DocumentFactory, ocr=True)


class NoteFactory(DjangoModelFactory[Note]):
    class Meta:
        model = Note

    title = Sequence(lambda n: f"Note {n}")
    content_kind = ContentKind.EXTERNAL_MEDIA
    external_url = "https://example.com/recording"


class SecondaryTextFactory(DjangoModelFactory[SecondaryText]):
    class Meta:
        model = SecondaryText

    title = Sequence(lambda n: f"Secondary text {n}")
    kind = SecondaryText.Kind.REVIEW
    document = SubFactory(DocumentFactory)


class SecondaryTextWorkLinkFactory(DjangoModelFactory[SecondaryTextWorkLink]):
    class Meta:
        model = SecondaryTextWorkLink

    secondary_text = SubFactory(SecondaryTextFactory)
    work = SubFactory(WorkFactory)


class ContextualMaterialFactory(DjangoModelFactory[ContextualMaterial]):
    class Meta:
        model = ContextualMaterial

    title = Sequence(lambda n: f"Material {n}")
    content_kind = ContentKind.EXTERNAL_MEDIA
    external_url = "https://example.com/film"


class MaterialWorkLinkFactory(DjangoModelFactory[MaterialWorkLink]):
    class Meta:
        model = MaterialWorkLink

    material = SubFactory(ContextualMaterialFactory)
    work = SubFactory(WorkFactory)


class FragmentFactory(DjangoModelFactory[Fragment]):
    class Meta:
        model = Fragment

    document = SubFactory(DocumentFactory)
    start = 0
    end = 12


class SiteSettingsFactory(DjangoModelFactory[SiteSettings]):
    class Meta:
        model = SiteSettings

    intro_text = "<p>Archiwum twórczości Leopolda Buczkowskiego.</p>"


class TeamMemberFactory(DjangoModelFactory[TeamMember]):
    class Meta:
        model = TeamMember

    name = Sequence(lambda n: f"Member {n}")
    group = TeamMember.Group.TEAM
