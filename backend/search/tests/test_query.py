"""The search query service (US-RA-15, US-RA-16)."""

import pytest

from archive.models import ContentKind, Status
from archive.tests.factories import (
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    NoteFactory,
    SecondaryTextFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)
from search.models import EntityType
from search.query import Filters, SearchResults, Sort, Tab, search

PUBLISHED = Status.PUBLISHED


def titles(results: SearchResults) -> list[tuple[str, str]]:
    return [(hit.entry.entity_type, hit.entry.title) for g in results.groups for hit in g.hits]


@pytest.fixture
def archive() -> dict[str, int]:
    """Two works from two decades; "dezerter" in a work, a tag, a fragment and a note."""
    wertepy = WorkFactory.create(status=PUBLISHED, title="Wertepy", description="Dezerter w lesie.")
    EditionFactory.create(work=wertepy, year=1947)
    potok = WorkFactory.create(status=PUBLISHED, title="Czarny potok")
    EditionFactory.create(work=potok, year=1954)
    TagFactory.create(status=PUBLISHED, title="Dezerter")
    typescript = TypescriptFactory.create(
        status=PUBLISHED,
        work=potok,
        title="Pierwsza wersja",
        document__text="Szedł dezerter przez las.",
    )
    FragmentFactory.create(document=typescript.document, start=6, end=14)
    note = NoteFactory.create(
        status=PUBLISHED,
        title="Notes 18",
        content_kind=ContentKind.PLAIN_TEXT,
        external_url="",
        document=DocumentFactory.create(text="dezerter"),
    )
    note.works.add(wertepy)
    note.save()
    WorkFactory.create(title="Dezerter (szkic)")
    return {"wertepy": wertepy.pk, "potok": potok.pk}


@pytest.mark.django_db
class TestResults:
    def test_us_ra_15_ac3_groups_follow_the_type_order(self, archive: dict[str, int]) -> None:
        # Arrange
        query = "dezerter"

        # Act
        results = search(query)

        # Assert
        assert [group.entity_type for group in results.groups] == [
            EntityType.WORK,
            EntityType.TAG,
            EntityType.FRAGMENT,
            EntityType.NOTE,
            EntityType.TYPESCRIPT,
        ]
        assert results.total == 5

    def test_r_06_drafts_are_not_found(self, archive: dict[str, int]) -> None:
        # Arrange
        query = "szkic"

        # Act
        results = search(query)

        # Assert
        assert results.total == 0

    def test_us_ra_15_ac4_sorted_by_relevance_or_by_title(self) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Wertepy", description="Las, las i las.")
        WorkFactory.create(status=PUBLISHED, title="Zielony las")

        # Act
        relevance = titles(search("las"))
        by_title = titles(search("las", sort=Sort.TITLE))

        # Assert
        assert relevance == [("work", "Zielony las"), ("work", "Wertepy")]
        assert by_title == [("work", "Wertepy"), ("work", "Zielony las")]

    def test_us_ra_15_ac6_snippet_highlights_terms_except_for_works(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        query = "dezerter"

        # Act
        results = search(query)

        # Assert
        snippets = {group.entity_type: group.hits[0].snippet for group in results.groups}
        assert snippets[EntityType.WORK] == ""
        assert snippets[EntityType.TYPESCRIPT] == "Szedł <mark>dezerter</mark> przez las."

    def test_us_ra_15_ac6_snippet_text_is_escaped(self) -> None:
        # Arrange
        NoteFactory.create(status=PUBLISHED, description='Las & "potok"')

        # Act
        results = search("las")

        # Assert
        assert results.groups[0].hits[0].snippet == "<mark>Las</mark> &amp; &quot;potok&quot;"

    def test_us_ra_15_quotes_search_for_an_exact_phrase(self) -> None:
        # Arrange
        WorkFactory.create(status=PUBLISHED, title="Czarny potok")
        WorkFactory.create(status=PUBLISHED, title="Potok czarny")

        # Act
        results = search('"czarny potok"')

        # Assert
        assert titles(results) == [("work", "Czarny potok")]

    def test_us_ra_15_ac8_no_results_suggest_the_most_frequent_tags(self) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        typescript = TypescriptFactory.create(status=PUBLISHED, work=work)
        fragment = FragmentFactory.create(document=typescript.document)
        tags = [TagFactory.create(status=PUBLISHED, title=f"Tag {n}") for n in range(5)]
        for count, tag in zip((3, 1, 0, 2, 2), tags, strict=True):
            for carrier in (work, typescript, fragment)[:count]:
                carrier.tags.add(tag)

        # Act
        results = search("nieistniejące")

        # Assert
        assert results.total == 0
        assert [tag.title for tag in results.suggested_tags] == ["Tag 0", "Tag 3", "Tag 4"]

    def test_us_ra_16_ac5_empty_query_returns_everything_by_title(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        query = " "

        # Act
        results = search(query, tab=Tab.WORKS)

        # Assert
        assert titles(results) == [("work", "Czarny potok"), ("work", "Wertepy")]
        assert results.suggested_tags == []


@pytest.mark.django_db
class TestTabsAndFilters:
    def test_us_ra_16_ac1_tabs_narrow_results_and_count_each_tab(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        query = "dezerter"

        # Act
        results = search(query, tab=Tab.FRAGMENTS)

        # Assert
        assert [group.entity_type for group in results.groups] == [EntityType.FRAGMENT]
        assert results.facets.tabs == {
            Tab.ALL: 5,
            Tab.WORKS: 1,
            Tab.FRAGMENTS: 1,
            Tab.NOTES: 1,
            Tab.TAGS: 1,
        }

    def test_us_ra_16_ac2_work_filter_keeps_results_related_to_the_work(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        filters = Filters(work_ids=(archive["wertepy"],))

        # Act
        results = search("dezerter", filters=filters)

        # Assert
        assert titles(results) == [("work", "Wertepy"), ("note", "Notes 18")]
        assert results.facets.works == {archive["wertepy"]: 2, archive["potok"]: 2}

    def test_us_ra_16_ac2_period_filter_uses_the_decade_of_the_first_edition(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        filters = Filters(decades=(1950,))

        # Act
        results = search("dezerter", filters=filters)

        # Assert
        assert titles(results) == [("fragment", "dezerter"), ("typescript", "Pierwsza wersja")]
        assert results.facets.decades == {1940: 2, 1950: 2}

    def test_us_ra_16_ac2_availability_filters_count_scans_and_texts(
        self, archive: dict[str, int]
    ) -> None:
        # Arrange
        filters = Filters(has_scan=True)

        # Act
        results = search("dezerter", filters=filters)
        with_text = search("dezerter", filters=Filters(has_text=True))

        # Assert
        assert titles(results) == [("fragment", "dezerter"), ("typescript", "Pierwsza wersja")]
        assert (results.facets.has_scan, results.facets.has_text) == (2, 2)
        assert with_text.total == 3

    def test_us_ra_16_ac2_filters_combine(self, archive: dict[str, int]) -> None:
        # Arrange
        SecondaryTextFactory.create(status=PUBLISHED, title="Dezerter w krytyce")
        filters = Filters(work_ids=(archive["potok"],), has_text=True)

        # Act
        results = search("dezerter", tab=Tab.ALL, filters=filters)

        # Assert
        assert titles(results) == [("fragment", "dezerter"), ("typescript", "Pierwsza wersja")]
