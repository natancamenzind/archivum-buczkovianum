"""Keeping the search index in step with the archive (docs/architecture.md, section 6)."""

from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.urls import reverse

from archive.models import ContentKind, Status, Work
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
from search.models import EntityType, SearchEntry
from search.tests.factories import SearchEntryFactory

PUBLISHED = Status.PUBLISHED


def entry(entity_type: EntityType, entity_id: int) -> SearchEntry | None:
    return SearchEntry.objects.filter(entity_type=entity_type, entity_id=entity_id).first()


def stored(entity_type: EntityType, entity_id: int) -> SearchEntry:
    return SearchEntry.objects.get(entity_type=entity_type, entity_id=entity_id)


@pytest.mark.django_db
def test_the_text_search_config_exists() -> None:
    """Architecture section 6: the database has the configured configuration (`polish` in CI)."""
    # Arrange
    sql = "SELECT 1 FROM pg_ts_config WHERE cfgname = %s"

    # Act
    with connection.cursor() as cursor:
        cursor.execute(sql, [settings.SEARCH_TS_CONFIG])
        found = cursor.fetchone()

    # Assert
    assert found is not None


@pytest.mark.django_db
class TestWrites:
    def test_us_wr_04_ac4_saving_a_typescript_updates_the_search_index(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create(
            work__status=PUBLISHED,
            title="Pierwsza wersja",
            description="Maszynopis z poprawkami.",
            document__text="Czarny potok płynie.",
        )
        assert entry(EntityType.TYPESCRIPT, typescript.pk) is None
        typescript.status = PUBLISHED

        # Act
        typescript.save()

        # Assert
        indexed = entry(EntityType.TYPESCRIPT, typescript.pk)
        assert indexed is not None
        assert str(indexed) == "typescript: Pierwsza wersja"
        assert indexed.url == f"/typescripts/{typescript.pk}"
        assert indexed.body == "Maszynopis z poprawkami.\n\nCzarny potok płynie."
        assert indexed.work_ids == [typescript.work_id]
        assert (indexed.has_scan, indexed.has_text) == (True, True)

    def test_r_06_a_draft_leaves_the_index(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        assert entry(EntityType.WORK, work.pk) is not None
        work.status = Status.DRAFT

        # Act
        work.save()

        # Assert
        assert entry(EntityType.WORK, work.pk) is None

    @pytest.mark.parametrize(
        ("factory", "entity_type", "url"),
        [
            (WorkFactory, EntityType.WORK, "/works/{slug}"),
            (TagFactory, EntityType.TAG, "/tags/{slug}"),
            (NoteFactory, EntityType.NOTE, "/notes/{pk}"),
            (SecondaryTextFactory, EntityType.SECONDARY_TEXT, "/secondary-texts/{pk}"),
            (ContextualMaterialFactory, EntityType.MATERIAL, "/materials/{pk}"),
        ],
    )
    def test_us_ra_15_ac1_every_published_entity_is_indexed(
        self, factory: type[WorkFactory], entity_type: EntityType, url: str
    ) -> None:
        # Arrange
        entity = factory.create(status=PUBLISHED)

        # Act
        indexed = entry(entity_type, entity.pk)

        # Assert
        assert indexed is not None
        assert indexed.url == url.format(pk=entity.pk, slug=getattr(entity, "slug", ""))

    def test_us_ra_15_ac1_a_visible_fragment_is_indexed_with_its_place_in_the_source(
        self,
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(
            status=PUBLISHED,
            work__status=PUBLISHED,
            document__text="Czarny potok płynie przez las.",
        )

        # Act
        fragment = FragmentFactory.create(
            document=typescript.document, start=7, end=12, description="Motyw wody."
        )

        # Assert
        indexed = entry(EntityType.FRAGMENT, fragment.pk)
        assert indexed is not None
        assert indexed.url == f"/typescripts/{typescript.pk}?fragment={fragment.pk}"
        assert indexed.body == "potok\n\nMotyw wody."
        assert indexed.work_ids == [typescript.work_id]

    def test_d4_fragments_follow_their_owner_in_and_out_of_the_index(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        fragment = FragmentFactory.create(document=typescript.document)
        assert entry(EntityType.FRAGMENT, fragment.pk) is None

        # Act
        typescript.status = PUBLISHED
        typescript.save()
        published = entry(EntityType.FRAGMENT, fragment.pk)
        typescript.status = Status.DRAFT
        typescript.save()

        # Assert
        assert published is not None
        assert entry(EntityType.FRAGMENT, fragment.pk) is None

    def test_deleting_removes_the_entries_of_an_item_and_its_fragments(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=PUBLISHED)
        fragment = FragmentFactory.create(document=typescript.document)
        other = FragmentFactory.create(document=typescript.document, start=1)

        # Act
        other.delete()
        typescript.delete()

        # Assert
        assert not SearchEntry.objects.exists()
        assert fragment.pk is not None

    def test_changing_a_text_updates_its_owner_entry(self) -> None:
        # Arrange
        secondary_text = SecondaryTextFactory.create(status=PUBLISHED)
        document = secondary_text.document
        assert document is not None
        document.text = "List o Wertepach."

        # Act
        document.save()

        # Assert
        indexed = entry(EntityType.SECONDARY_TEXT, secondary_text.pk)
        assert indexed is not None
        assert indexed.body == "List o Wertepach."
        assert (indexed.has_scan, indexed.has_text) == (False, True)

    def test_a_text_without_an_owner_is_not_indexed(self) -> None:
        # Arrange
        document = DocumentFactory.create()

        # Act
        document.save()

        # Assert
        assert not SearchEntry.objects.exists()

    def test_us_ra_16_ac2_an_edition_updates_the_decades_of_related_entries(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        EditionFactory.create(work=work, year=1957)
        note = NoteFactory.create(status=PUBLISHED)
        note.works.add(work)
        note.save()
        first = EditionFactory.create(work=work, year=1947)

        # Act
        decades_with_first = stored(EntityType.NOTE, note.pk).decades
        first.delete()

        # Assert
        assert decades_with_first == [1940]
        indexed = entry(EntityType.NOTE, note.pk)
        assert indexed is not None
        assert (indexed.work_ids, indexed.decades) == ([work.pk], [1950])

    def test_an_edition_reindexes_its_work_without_saving_it(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED, title="Wertepy")
        edition = EditionFactory.create(work=work, year=1957)
        elsewhere = Work.objects.get(pk=work.pk)
        elsewhere.title = "Changed elsewhere"
        elsewhere.save()

        # Act
        edition.year = 1947
        edition.save()

        # Assert
        work.refresh_from_db()
        assert work.title == "Changed elsewhere"
        assert stored(EntityType.WORK, work.pk).decades == [1940]

    def test_us_ra_16_ac2_a_tag_is_filed_under_the_works_it_refers_to(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        work = WorkFactory.create(status=PUBLISHED)
        EditionFactory.create(work=work, year=1966)
        link = MaterialWorkLinkFactory.create(work=work, material__status=PUBLISHED)
        link.tags.add(tag)

        # Act
        tag.save()

        # Assert
        indexed = entry(EntityType.TAG, tag.pk)
        assert indexed is not None
        assert (indexed.work_ids, indexed.decades) == ([work.pk], [1960])

    def test_us_ra_16_ac2_media_without_a_text_has_neither_scan_nor_text(self) -> None:
        # Arrange
        material = ContextualMaterialFactory.create(
            status=PUBLISHED, content_kind=ContentKind.EXTERNAL_MEDIA
        )

        # Act
        indexed = entry(EntityType.MATERIAL, material.pk)

        # Assert
        assert indexed is not None
        assert (indexed.has_scan, indexed.has_text, indexed.body) == (False, False, "")

    def test_d4_fragments_of_a_replaced_text_leave_the_index(self) -> None:
        # Arrange
        note = NoteFactory.create(
            status=PUBLISHED,
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(),
        )
        old_document = note.document
        assert old_document is not None
        fragment = FragmentFactory.create(document=old_document)
        note = type(note).objects.get(pk=note.pk)
        assert entry(EntityType.FRAGMENT, fragment.pk) is not None
        note.document = DocumentFactory.create()

        # Act
        note.save()

        # Assert
        assert entry(EntityType.FRAGMENT, fragment.pk) is None

    def test_r_06_draft_works_are_not_in_the_filters(self) -> None:
        # Arrange
        work = WorkFactory.create()
        EditionFactory.create(work=work, year=1947)
        note = NoteFactory.create()
        note.works.add(work)
        note.status = PUBLISHED
        note.save()
        assert stored(EntityType.NOTE, note.pk).work_ids == []

        # Act
        work.status = PUBLISHED
        work.save()

        # Assert
        indexed = entry(EntityType.NOTE, note.pk)
        assert indexed is not None
        assert (indexed.work_ids, indexed.decades) == ([work.pk], [1940])

    def test_deleting_a_work_takes_it_out_of_related_entries(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        note = NoteFactory.create(status=PUBLISHED)
        note.works.add(work)
        note.save()

        # Act
        work.delete()

        # Assert
        indexed = entry(EntityType.NOTE, note.pk)
        assert indexed is not None
        assert indexed.work_ids == []

    def test_deleting_the_last_carrier_takes_the_work_out_of_a_tag_entry(self) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED)
        work = WorkFactory.create(status=PUBLISHED)
        note = NoteFactory.create(status=PUBLISHED)
        note.works.add(work)
        note.tags.add(tag)
        tag.save()
        assert stored(EntityType.TAG, tag.pk).work_ids == [work.pk]

        # Act
        note.delete()

        # Assert
        tag_entry = entry(EntityType.TAG, tag.pk)
        assert tag_entry is not None
        assert tag_entry.work_ids == []


@pytest.mark.django_db
class TestEditorPanel:
    def test_us_wr_04_ac4_works_and_tags_chosen_in_the_form_reach_the_index(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        EditionFactory.create(work=work, year=1947)
        tag = TagFactory.create(status=PUBLISHED)
        data = {
            "title": "Notes 18",
            "status": PUBLISHED,
            "content_kind": ContentKind.EXTERNAL_MEDIA,
            "external_url": "https://example.com/nagranie",
            "works": [work.pk],
            "tags": [tag.pk],
        }

        # Act
        response = admin_client.post(reverse("admin:archive_note_add"), data)

        # Assert
        assert response.status_code == 302
        note = SearchEntry.objects.get(entity_type=EntityType.NOTE)
        tag_entry = entry(EntityType.TAG, tag.pk)
        assert tag_entry is not None
        assert (note.work_ids, note.decades) == ([work.pk], [1940])
        assert tag_entry.work_ids == [work.pk]

    def test_us_wr_10_ac2_a_tagged_work_link_files_the_tag_under_the_work(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        tag = TagFactory.create(status=PUBLISHED)
        secondary_text = SecondaryTextFactory.create(status=PUBLISHED, title="Recenzja")
        link = SecondaryTextWorkLinkFactory.create(secondary_text=secondary_text, work=work)
        data = {
            "title": "Recenzja",
            "status": PUBLISHED,
            "kind": secondary_text.kind,
            "document": secondary_text.document_id,
            "work_links-TOTAL_FORMS": 1,
            "work_links-INITIAL_FORMS": 1,
            "work_links-0-id": link.pk,
            "work_links-0-secondary_text": secondary_text.pk,
            "work_links-0-work": work.pk,
            "work_links-0-tags": [tag.pk],
        }

        # Act
        response = admin_client.post(
            reverse("admin:archive_secondarytext_change", args=[secondary_text.pk]), data
        )

        # Assert
        assert response.status_code == 302
        tag_entry = entry(EntityType.TAG, tag.pk)
        assert tag_entry is not None
        assert tag_entry.work_ids == [work.pk]


@pytest.mark.django_db
class TestRebuild:
    def test_rebuild_search_index_restores_published_entities_and_visible_fragments(
        self,
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=PUBLISHED)
        FragmentFactory.create(document=typescript.document)
        WorkFactory.create()
        expected = set(SearchEntry.objects.values_list("entity_type", "entity_id"))
        SearchEntry.objects.all().delete()
        SearchEntryFactory.create(title="Usunięty utwór")
        output = StringIO()

        # Act
        call_command("rebuild_search_index", stdout=output)

        # Assert
        assert set(SearchEntry.objects.values_list("entity_type", "entity_id")) == expected
        assert len(expected) == 2
        assert output.getvalue() == "Indexed 2 entries.\n"
