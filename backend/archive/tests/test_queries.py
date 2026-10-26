"""Shared queries: what the public sees and the values derived from it (docs/plan.md, step 2)."""

from typing import Any

import pytest
from factory.django import DjangoModelFactory
from pytest_django.fixtures import Settings

from archive.models import (
    ContentKind,
    ContextualMaterial,
    Fragment,
    MaterialWorkLink,
    Note,
    SecondaryText,
    SecondaryTextWorkLink,
    Status,
    Tag,
    Taggable,
    Typescript,
    Work,
    first_edition_year,
)
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def with_text[T](factory: type[DjangoModelFactory[T]], **kwargs: Any) -> T:
    """A note or contextual material whose content is a plain text, so it can have fragments."""
    return factory.create(
        content_kind=ContentKind.PLAIN_TEXT,
        external_url="",
        document=DocumentFactory.create(),
        **kwargs,
    )


@pytest.mark.django_db
class TestPublished:
    @pytest.mark.parametrize(
        ("factory", "model"),
        [
            (WorkFactory, Work),
            (TagFactory, Tag),
            (TypescriptFactory, Typescript),
            (NoteFactory, Note),
            (SecondaryTextFactory, SecondaryText),
            (ContextualMaterialFactory, ContextualMaterial),
        ],
    )
    def test_r_06_only_published_entities_are_public(
        self, factory: type[DjangoModelFactory[Any]], model: type[Any]
    ) -> None:
        # Arrange
        published = factory.create(status=PUBLISHED)
        factory.create(status=Status.DRAFT)

        # Act
        public = list(model.objects.published())

        # Assert
        assert public == [published]


@pytest.mark.django_db
class TestVisibleFragments:
    def test_d4_fragments_of_a_published_owner_are_visible(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        main = TypescriptFactory.create(work=work, is_main=True, status=PUBLISHED)
        older = TypescriptFactory.create(work=work, status=PUBLISHED)
        draft = TypescriptFactory.create(work=work, status=Status.DRAFT)
        visible = [
            FragmentFactory.create(document=main.document),
            FragmentFactory.create(document=older.document),
            FragmentFactory.create(document=with_text(NoteFactory, status=PUBLISHED).document),
            FragmentFactory.create(document=SecondaryTextFactory.create(status=PUBLISHED).document),
            FragmentFactory.create(
                document=with_text(ContextualMaterialFactory, status=PUBLISHED).document
            ),
        ]
        FragmentFactory.create(document=draft.document)
        FragmentFactory.create(document=with_text(NoteFactory).document)
        FragmentFactory.create(document=DocumentFactory.create())

        # Act
        fragments = set(Fragment.objects.visible())

        # Assert
        assert fragments == set(visible)

    def test_r_10_fragment_number_counts_every_fragment_of_its_document(self) -> None:
        # Arrange
        tag = TagFactory.create()
        document = DocumentFactory.create(text="Czarny potok płynie przez las.")
        third = FragmentFactory.create(document=document, start=7, end=19)
        first = FragmentFactory.create(document=document, start=0, end=6)
        second = FragmentFactory.create(document=document, start=0, end=12)
        twin = FragmentFactory.create(document=document, start=7, end=19)
        FragmentFactory.create(document=DocumentFactory.create(), start=0, end=6)
        third.tags.add(tag)
        twin.tags.add(tag)

        # Act
        numbers = {
            fragment: fragment.number
            for fragment in Fragment.objects.with_number().filter(document=document)
        }
        tagged = [fragment.number for fragment in Fragment.objects.with_number().filter(tags=tag)]

        # Assert
        assert numbers == {first: 1, second: 2, third: 3, twin: 4}
        assert tagged == [3, 4]


@pytest.mark.django_db
class TestPublishedTags:
    def test_r_06_draft_tags_are_never_shown_on_an_item(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        published = TagFactory.create(status=PUBLISHED)
        work.tags.add(published, TagFactory.create(status=Status.DRAFT))

        # Act
        tags = list(work.published_tags())

        # Assert
        assert tags == [published]


@pytest.mark.django_db
class TestPreview:
    def test_r_09_preview_shows_featured_first_then_text_order_with_the_total(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok płynie przez las.")
        first = FragmentFactory.create(document=document, start=0, end=6)
        FragmentFactory.create(document=document, start=7, end=12)
        featured = FragmentFactory.create(document=document, start=20, end=25, is_featured=True)

        # Act
        result = Fragment.objects.filter(document=document).preview()

        # Assert
        assert result.items == [featured, first]
        assert result.total == 3

    def test_r_09_preview_keeps_text_order_across_documents(self) -> None:
        # Arrange
        older, newer = DocumentFactory.create(), DocumentFactory.create()
        first = FragmentFactory.create(document=older, start=5)
        second = FragmentFactory.create(document=newer, start=0)

        # Act
        result = Fragment.objects.all().preview()

        # Assert
        assert result.items == [first, second]

    def test_r_09_preview_length_is_one_setting(self, settings: Settings) -> None:
        # Arrange
        settings.PREVIEW_LIMIT = 1
        document = DocumentFactory.create(text="Czarny potok płynie.")
        first = FragmentFactory.create(document=document, start=0, end=6)
        FragmentFactory.create(document=document, start=7, end=12)

        # Act
        result = Fragment.objects.filter(document=document).preview()

        # Assert
        assert (result.items, result.total) == ([first], 2)


@pytest.mark.django_db
class TestWorkLinks:
    @pytest.mark.parametrize(
        ("factory", "model", "item"),
        [
            (SecondaryTextWorkLinkFactory, SecondaryTextWorkLink, "secondary_text"),
            (MaterialWorkLinkFactory, MaterialWorkLink, "material"),
        ],
    )
    def test_r_06_a_link_is_visible_when_both_ends_are_published(
        self, factory: type[DjangoModelFactory[Any]], model: type[Any], item: str
    ) -> None:
        # Arrange
        visible = factory.create(work__status=PUBLISHED, **{f"{item}__status": PUBLISHED})
        factory.create(work__status=Status.DRAFT, **{f"{item}__status": PUBLISHED})
        factory.create(work__status=PUBLISHED, **{f"{item}__status": Status.DRAFT})

        # Act
        links = list(model.objects.visible())

        # Assert
        assert links == [visible]


@pytest.mark.django_db
class TestYearOfWork:
    def test_us_ra_04_ac1_year_is_the_first_edition(self) -> None:
        # Arrange
        work = WorkFactory.create()
        EditionFactory.create(work=work, year=1957)
        EditionFactory.create(work=work, year=1947)
        typescript = TypescriptFactory.create(work=work)

        # Act
        year = Work.objects.with_year().get().year
        typescript_year = (
            Typescript.objects.annotate(year=first_edition_year("work")).get(pk=typescript.pk).year
        )

        # Assert
        assert (year, typescript_year) == (1947, 1947)

    def test_us_ra_18_ac2_each_work_is_listed_once(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        EditionFactory.create(work=work, year=1947)
        EditionFactory.create(work=work, year=1957)

        # Act
        works = list(Work.objects.with_year())

        # Assert
        assert works == [work]


@pytest.mark.django_db
class TestRelatedWorks:
    def test_r_03_items_list_their_published_works_by_first_edition(self) -> None:
        # Arrange
        later, earlier = WorkFactory.create(status=PUBLISHED), WorkFactory.create(status=PUBLISHED)
        draft = WorkFactory.create()
        EditionFactory.create(work=later, year=1966)
        EditionFactory.create(work=earlier, year=1947)
        note = NoteFactory.create()
        note.works.add(later, earlier, draft)
        secondary_text = SecondaryTextFactory.create()
        material = ContextualMaterialFactory.create()
        for work in (later, earlier, draft):
            SecondaryTextWorkLinkFactory.create(secondary_text=secondary_text, work=work)
            MaterialWorkLinkFactory.create(material=material, work=work)
        typescript = TypescriptFactory.create(work=earlier)

        # Act
        related = {
            item: list(item.related_works())
            for item in (note, secondary_text, material, typescript)
        }

        # Assert
        assert related == {
            note: [earlier, later],
            secondary_text: [earlier, later],
            material: [earlier, later],
            typescript: [earlier],
        }


@pytest.mark.django_db
class TestTagReferences:
    def test_us_ra_07_ac5_tag_refers_to_works_through_items_fragments_and_links(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        works = WorkFactory.create_batch(7, status=PUBLISHED)
        works[0].tags.add(tag)
        TypescriptFactory.create(work=works[1], status=PUBLISHED).tags.add(tag)
        typescript = TypescriptFactory.create(work=works[2], status=PUBLISHED)
        FragmentFactory.create(document=typescript.document).tags.add(tag)
        note = with_text(NoteFactory, status=PUBLISHED)
        note.works.add(works[3])
        FragmentFactory.create(document=note.document).tags.add(tag)
        SecondaryTextWorkLinkFactory.create(
            work=works[4], secondary_text__status=PUBLISHED
        ).tags.add(tag)
        MaterialWorkLinkFactory.create(work=works[5], material__status=PUBLISHED).tags.add(tag)
        material = ContextualMaterialFactory.create(status=PUBLISHED)
        MaterialWorkLinkFactory.create(work=works[6], material=material)
        material.tags.add(tag)

        # Act
        referred = set(Work.objects.published().referred_to_by(tag))

        # Assert
        assert referred == set(works)

    def test_us_ra_07_ac5_drafts_do_not_carry_a_tag_to_a_work(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        work = WorkFactory.create(status=PUBLISHED)
        TypescriptFactory.create(work=work).tags.add(tag)
        draft_note = with_text(NoteFactory)
        draft_note.works.add(work)
        FragmentFactory.create(document=draft_note.document).tags.add(tag)
        SecondaryTextWorkLinkFactory.create(work=work).tags.add(tag)
        WorkFactory.create().tags.add(tag)

        # Act
        referred = list(Work.objects.published().referred_to_by(tag))

        # Assert
        assert referred == []

    def test_us_ra_07_ac5_each_work_is_listed_once(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        work = WorkFactory.create(status=PUBLISHED)
        work.tags.add(tag)
        typescript = TypescriptFactory.create(work=work, status=PUBLISHED)
        typescript.tags.add(tag)
        FragmentFactory.create(document=typescript.document).tags.add(tag)

        # Act
        referred = list(Work.objects.published().referred_to_by(tag))

        # Assert
        assert referred == [work]


@pytest.mark.django_db
class TestOccurrences:
    def test_us_ra_20_ac2_occurrences_count_fragments_items_and_work_links(self) -> None:
        # Arrange
        tag, unused = TagFactory.create(status=PUBLISHED), TagFactory.create(status=PUBLISHED)
        work = WorkFactory.create(status=PUBLISHED)
        typescript = TypescriptFactory.create(work=work, status=PUBLISHED)
        carriers: list[Taggable] = [
            work,
            typescript,
            FragmentFactory.create(document=typescript.document),
            FragmentFactory.create(document=typescript.document, start=1),
            NoteFactory.create(status=PUBLISHED),
            SecondaryTextFactory.create(status=PUBLISHED),
            ContextualMaterialFactory.create(status=PUBLISHED),
            SecondaryTextWorkLinkFactory.create(work=work, secondary_text__status=PUBLISHED),
            MaterialWorkLinkFactory.create(work=work, material__status=PUBLISHED),
        ]
        for carrier in carriers:
            carrier.tags.add(tag)

        # Act
        occurrences = {item: item.occurrences for item in Tag.objects.with_occurrences()}

        # Assert
        assert occurrences == {tag: 9, unused: 0}

    def test_r_06_drafts_are_not_occurrences(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        draft_typescript = TypescriptFactory.create(work__status=PUBLISHED)
        carriers: list[Taggable] = [
            WorkFactory.create(),
            draft_typescript,
            FragmentFactory.create(document=draft_typescript.document),
            NoteFactory.create(),
            SecondaryTextWorkLinkFactory.create(work__status=PUBLISHED),
            MaterialWorkLinkFactory.create(material__status=PUBLISHED),
        ]
        for carrier in carriers:
            carrier.tags.add(tag)

        # Act
        occurrences = Tag.objects.with_occurrences().get().occurrences

        # Assert
        assert occurrences == 0
